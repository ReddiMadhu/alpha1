"""
Business Context Validator - The Standout Feature
Validates if discovered relationships tell a complete business story.
"""

from typing import Dict, List, Any, Optional
from loguru import logger

from src.config import Config
from src.llm_reasoner import LLMReasoner


class BusinessContextValidator:
    """
    Validates if discovered relationships connect scattered business information
    into a coherent narrative. Goes beyond technical joins to assess business value.
    
    **This is what makes the system stand out:**
    - Not just "Can these columns join?" 
    - But "Do these joins reveal the complete business story?"
    """
    
    def __init__(self):
        self.llm = LLMReasoner()
    
    def validate_business_context(
        self,
        profiles: Dict[str, Dict[str, Any]],
        relationships: List[Any]
    ) -> Dict[str, Any]:
        """
        Validate if the discovered relationships create a complete business view.
        
        Args:
            profiles: File profiles with column metadata
            relationships: Discovered relationship candidates
            
        Returns:
            Dictionary with business insights
        """
        if not Config.ENABLE_LLM_VALIDATION:
            return self._get_fallback_insights()
        
        logger.info("Analyzing business context...")
        
        # Build business context map
        context = self._build_business_context(profiles, relationships)
        
        # Ask LLM: "Does this tell a complete story?"
        business_insights = self._ask_llm_business_questions(context)
        
        return business_insights
    
    def _build_business_context(
        self,
        profiles: Dict[str, Dict[str, Any]],
        relationships: List[Any]
    ) -> Dict[str, Any]:
        """Build a business-focused context from technical metadata."""
        from pathlib import Path
        
        # Extract file names and their business entities
        files_summary = {}
        for file_path, profile in profiles.items():
            file_name = Path(file_path).stem
            
            # Infer business entity from file name and columns
            entity_type = self._infer_business_entity(file_name, profile)
            
            key_columns = [
                col_name for col_name, col_data in profile["columns"].items()
                if col_data.get("key_features", {}).get("primary_key_candidate") or
                   col_data.get("key_features", {}).get("foreign_key_candidate")
            ]
            
            files_summary[file_name] = {
                "entity_type": entity_type,
                "row_count": profile["row_count"],
                "key_columns": key_columns,
                "all_columns": list(profile["columns"].keys())
            }
        
        # Summarize relationships
        relationships_summary = []
        for rel in relationships:
            if rel.confidence_level in ["HIGH", "MEDIUM"]:
                relationships_summary.append({
                    "from": f"{Path(rel.source_file).stem}.{rel.source_column}",
                    "to": f"{Path(rel.target_file).stem}.{rel.target_column}",
                    "type": rel.relationship_type,
                    "confidence": rel.confidence_level
                })
        
        return {
            "files": files_summary,
            "relationships": relationships_summary,
            "file_count": len(profiles)
        }
    
    def _infer_business_entity(self, file_name: str, profile: Dict) -> str:
        """Infer business entity type from file name and columns."""
        name_lower = file_name.lower()
        
        # Common insurance entities
        if any(kw in name_lower for kw in ['policy', 'policies']):
            return "Policy"
        elif any(kw in name_lower for kw in ['claim', 'claims']):
            return "Claim"
        elif any(kw in name_lower for kw in ['customer', 'client', 'insured']):
            return "Customer"
        elif any(kw in name_lower for kw in ['agent', 'broker']):
            return "Agent"
        elif any(kw in name_lower for kw in ['premium', 'payment']):
            return "Premium"
        elif any(kw in name_lower for kw in ['coverage', 'benefit']):
            return "Coverage"
        elif any(kw in name_lower for kw in ['property', 'asset']):
            return "Property"
        
        # General business entities
        elif any(kw in name_lower for kw in ['order', 'transaction']):
            return "Transaction"
        elif any(kw in name_lower for kw in ['product', 'item']):
            return "Product"
        elif any(kw in name_lower for kw in ['invoice', 'billing']):
            return "Billing"
        else:
            return "Unknown"
    
    def _ask_llm_business_questions(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Ask LLM to validate business completeness."""
        
        prompt = self._build_business_validation_prompt(context)
        
        try:
            response = self.llm._call_azure_foundry(prompt)
            import json
            insights = json.loads(response)
            
            logger.success("✓ Business context validated")
            return insights
            
        except Exception as e:
            logger.warning(f"Business validation failed: {e}")
            return self._get_fallback_insights()
    
    def _build_business_validation_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for business context validation."""
        
        files_desc = "\n".join([
            f"- **{name}** ({data['entity_type']}): {data['row_count']} rows, "
            f"Keys: {', '.join(data['key_columns']) if data['key_columns'] else 'None'}"
            for name, data in context["files"].items()
        ])
        
        relationships_desc = "\n".join([
            f"- {rel['from']} → {rel['to']} ({rel['confidence']} confidence)"
            for rel in context["relationships"]
        ])
        
        prompt = f"""You are a business intelligence analyst specializing in insurance data.

DISCOVERED DATA FILES:
{files_desc}

DISCOVERED RELATIONSHIPS:
{relationships_desc}

CRITICAL QUESTIONS:

1. **Business Completeness**: Do these files and relationships tell a COMPLETE business story, 
   or are there critical missing pieces? For insurance data, do we have the full customer journey 
   (policy → premium → claim → payment)?

2. **Decision-Making Value**: Can a decision-maker understand the FULL PICTURE from joining 
   these files, or will they still see isolated snapshots?

3. **Missing Entities**: What critical business entities or relationships are MISSING that 
   would be needed for complete analysis? (e.g., missing claims data when we have policies?)

4. **Business Insights**: What key business questions CAN be answered with these joins? 
   What questions CANNOT be answered?

5. **Data Quality for Decisions**: Are there any data quality issues that would prevent 
   executives from trusting these joins for critical decisions?

Respond ONLY with valid JSON (no markdown):

{{
  "completeness_score": 0-100,
  "tells_complete_story": true or false,
  "complete_story_explanation": "Brief explanation of why/why not",
  "missing_critical_pieces": ["entity1", "entity2"],
  "answerable_questions": ["question1", "question2"],
  "unanswerable_questions": ["question1", "question2"],
  "business_value_assessment": "HIGH" or "MEDIUM" or "LOW",
  "executive_summary": "One-sentence summary of what this data reveals",
  "recommendations": ["recommendation1", "recommendation2"]
}}"""
        
        return prompt
    
    def _get_fallback_insights(self) -> Dict[str, Any]:
        """Return basic insights when LLM is unavailable."""
        return {
            "completeness_score": 0,
            "tells_complete_story": False,
            "complete_story_explanation": "LLM validation unavailable - unable to assess business context",
            "missing_critical_pieces": [],
            "answerable_questions": [],
            "unanswerable_questions": [],
            "business_value_assessment": "UNKNOWN",
            "executive_summary": "Technical relationships detected, but business context not validated",
            "recommendations": ["Enable LLM validation for business context analysis"]
        }
