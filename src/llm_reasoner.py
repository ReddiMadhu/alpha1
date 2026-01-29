"""
LLM Semantic Reasoning Layer.
Uses Llama-3.3B in Azure AI Foundry for semantic validation.
"""

import os
import json
from typing import Dict, Any, Optional
from loguru import logger
import requests

from src.config import Config


class LLMReasoner:
    """
    LLM-based semantic reasoning for relationship validation.
    Uses Llama-3.3B deployed in Azure AI Foundry.
    """
    
    def __init__(self):
        self.endpoint = Config.AZURE_FOUNDRY_ENDPOINT
        self.api_key = Config.AZURE_FOUNDRY_API_KEY
        self.model = Config.LLM_MODEL
        
        if not Config.ENABLE_LLM_VALIDATION:
            logger.warning("LLM validation is disabled in configuration")
            return
        
        if not self.endpoint or not self.api_key:
            logger.warning(
                "Azure AI Foundry credentials not configured. "
                "LLM validation will be skipped."
            )
    
    def validate_relationship(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a relationship candidate using LLM semantic reasoning.
        
        Args:
            candidate: Dictionary with source, target, and statistics
            
        Returns:
            Dictionary with validation result
        """
        if not Config.ENABLE_LLM_VALIDATION:
            return self._get_fallback_result("LLM validation disabled")
        
        if not self.endpoint or not self.api_key:
            return self._get_fallback_result("LLM credentials not configured")
        
        try:
            # Build prompt
            prompt = self._build_validation_prompt(candidate)
            
            # Call Azure AI Foundry
            response = self._call_azure_foundry(prompt)
            
            # Parse response
            result = json.loads(response)
            
            logger.debug(f"LLM validated: {candidate['source']['column']} <-> {candidate['target']['column']}")
            
            return result
            
        except Exception as e:
            logger.error(f"LLM validation failed: {e}")
            return self._get_fallback_result(f"Error: {str(e)}")
    
    def _build_validation_prompt(self, candidate: Dict[str, Any]) -> str:
        """Build structured prompt for relationship validation."""
        
        source = candidate["source"]
        target = candidate["target"]
        stats = candidate.get("statistics", {})
        
        # Get sample values (limit to 5)
        source_samples = source.get("sample_values", [])[:5]
        target_samples = target.get("sample_values", [])[:5]
        
        prompt = f"""Analyze this potential column relationship:

SOURCE COLUMN:
- File: {source['file']}
- Column: {source['column']}
- Data type: {source.get('data_type', 'unknown')}
- Sample values: {source_samples}
- Uniqueness: {source.get('uniqueness', 0):.1%}
- NULL %: {source.get('null_percent', 0):.1%}

TARGET COLUMN:
- File: {target['file']}
- Column: {target['column']}
- Data type: {target.get('data_type', 'unknown')}
- Sample values: {target_samples}
- Uniqueness: {target.get('uniqueness', 0):.1%}
- NULL %: {target.get('null_percent', 0):.1%}

OVERLAP STATISTICS:
- Value overlap: {stats.get('value_overlap_percent', 0):.1f}%
- Orphan records: {stats.get('orphans_in_source', 0) + stats.get('orphans_in_target', 0)}

INSTRUCTIONS:
Determine if these columns are semantically related and can be joined.
Respond ONLY with valid JSON in this EXACT format (no markdown, no code blocks):

{{
  "is_related": true or false,
  "relationship_type": "PRIMARY_KEY -> FOREIGN_KEY" or "SEMANTIC_MATCH" or "NONE",
  "cardinality": "1:1" or "1:N" or "N:1" or "M:N" or "UNKNOWN",
  "confidence_score": 0-100,
  "reasoning": "Brief explanation in one sentence",
  "warnings": ["warning1", "warning2"] or [],
  "transformation_needed": null or "UPPER()" or "STRIP_PREFIX()"
}}"""
        
        return prompt
    
    def _call_azure_foundry(self, prompt: str) -> str:
        """
        Call Azure AI Foundry API.
        
        Args:
            prompt: User prompt
            
        Returns:
            Response text
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a data analyst expert. Analyze column relationships "
                        "and provide structured JSON responses ONLY. No explanations, "
                        "no markdown formatting, just pure JSON."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": Config.LLM_TEMPERATURE,
            "max_tokens": Config.LLM_MAX_TOKENS,
            "response_format": {"type": "json_object"}
        }
        
        try:
            response = requests.post(
                f"{self.endpoint}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Azure AI Foundry API call failed: {e}")
    
    def _get_fallback_result(self, reason: str) -> Dict[str, Any]:
        """Return conservative fallback when LLM is unavailable."""
        return {
            "is_related": False,
            "relationship_type": "UNKNOWN",
            "cardinality": "UNKNOWN",
            "confidence_score": 0,
            "reasoning": f"LLM validation unavailable: {reason}",
            "warnings": ["LLM unavailable, using deterministic rules only"],
            "transformation_needed": None
        }
    
    def test_connection(self) -> bool:
        """
        Test connection to Azure AI Foundry.
        
        Returns:
            bool: True if connection successful
        """
        if not self.endpoint or not self.api_key:
            logger.error("Azure AI Foundry credentials not configured")
            return False
        
        try:
            test_candidate = {
                "source": {
                    "file": "test.xlsx",
                    "column": "id",
                    "data_type": "int",
                    "sample_values": [1, 2, 3],
                    "uniqueness": 1.0,
                    "null_percent": 0.0
                },
                "target": {
                    "file": "test2.xlsx",
                    "column": "test_id",
                    "data_type": "int",
                    "sample_values": [1, 2, 3],
                    "uniqueness": 0.5,
                    "null_percent": 0.0
                },
                "statistics": {
                    "value_overlap_percent": 100.0,
                    "orphans_in_source": 0,
                    "orphans_in_target": 0
                }
            }
            
            result = self.validate_relationship(test_candidate)
            
            if result.get("is_related") is not None:
                logger.success("✓ Azure AI Foundry connection successful")
                return True
            else:
                logger.error("✗ Azure AI Foundry returned invalid response")
                return False
                
        except Exception as e:
            logger.error(f"✗ Azure AI Foundry connection failed: {e}")
            return False
