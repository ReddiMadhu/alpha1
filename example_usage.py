"""
Example usage of the Excel Relationship Discovery System.
This script demonstrates how to use the system programmatically.
"""

from src.main import RelationshipDiscovery
from pathlib import Path

def example_basic_usage():
    """Basic usage example."""
    print("Example 1: Basic Usage")
    print("="*60)
    
    # Create discovery instance
    discovery = RelationshipDiscovery()
    
    # List your Excel files
    files = [
        "data/orders.xlsx",
        "data/customers.xlsx",
        "data/products.xlsx"
    ]
    
    # Run discovery
    report = discovery.discover_relationships(
        file_paths=files,
        output_file="output/my_report.json"
    )
    
    print(f"\nFound {len(report['relationships'])} relationships")
    print("\nTop relationships:")
    for rel in report['relationships'][:5]:
        print(f"  {rel['source']['column']} <-> {rel['target']['column']}")
        print(f"    Confidence: {rel['confidence_level']} ({rel['confidence_score']}%)")
        print(f"    Type: {rel['relationship_type']}")
        print()


def example_without_llm():
    """Example without LLM validation (faster)."""
    print("\nExample 2: Without LLM Validation")
    print("="*60)
    
    from src.config import Config
    
    # Disable LLM
    Config.ENABLE_LLM_VALIDATION = False
    
    discovery = RelationshipDiscovery()
    
    files = ["data/file1.xlsx", "data/file2.xlsx"]
    
    report = discovery.discover_relationships(files)
    
    print(f"Processed {report['report_metadata']['file_count']} files")
    print(f"Found {report['report_metadata']['total_relationships_found']} relationships")


def example_access_detailed_info():
    """Example: Access detailed information from report."""
    print("\nExample 3: Access Detailed Information")
    print("="*60)
    
    discovery = RelationshipDiscovery()
    
    files = ["data/orders.xlsx", "data/customers.xlsx"]
    
    report = discovery.discover_relationships(files)
    
    # Access file profiles
    for file_info in report['files']:
        print(f"\nFile: {file_info['file_name']}")
        print(f"  Rows: {file_info['row_count']:,}")
        print(f"  Columns: {file_info['column_count']}")
        
        # Primary key candidates
        pk_candidates = [
            col['name'] for col in file_info['columns']
            if col.get('key_features', {}).get('primary_key_candidate')
        ]
        if pk_candidates:
            print(f"  PK Candidates: {', '.join(pk_candidates)}")
    
    # Access relationships with warnings
    print("\n\nRelationships with Data Quality Warnings:")
    for rel in report['relationships']:
        if rel.get('warnings'):
            print(f"\n{rel['source']['column']} <-> {rel['target']['column']}:")
            for warning in rel['warnings']:
                print(f"  ⚠️  {warning}")


def example_filter_high_confidence():
    """Example: Filter for high-confidence relationships only."""
    print("\nExample 4: High-Confidence Relationships Only")
    print("="*60)
    
    discovery = RelationshipDiscovery()
    
    files = ["data/orders.xlsx", "data/customers.xlsx", "data/products.xlsx"]
    
    report = discovery.discover_relationships(files)
    
    # Filter high confidence
    high_conf = [
        r for r in report['relationships']
        if r['confidence_level'] == 'HIGH'
    ]
    
    print(f"\nHigh-confidence relationships: {len(high_conf)}")
    
    for rel in high_conf:
        print(f"\n{rel['source']['file']} → {rel['target']['file']}")
        print(f"  {rel['source']['column']} → {rel['target']['column']}")
        print(f"  Overlap: {rel['statistics']['value_overlap_percent']:.1f}%")
        print(f"  Type: {rel['relationship_type']}")


def example_generate_sql():
    """Example: Generate SQL joins from relationships."""
    print("\nExample 5: Generate SQL Joins")
    print("="*60)
    
    discovery = RelationshipDiscovery()
    
    files = ["data/orders.xlsx", "data/customers.xlsx"]
    
    report = discovery.discover_relationships(files)
    
    print("\n-- Recommended SQL Joins --\n")
    
    for rel in report['relationships']:
        if rel['confidence_level'] == 'HIGH':
            source_table = Path(rel['source']['file']).stem
            target_table = Path(rel['target']['file']).stem
            source_col = rel['source']['column']
            target_col = rel['target']['column']
            
            sql = f"""SELECT *
FROM {source_table} s
INNER JOIN {target_table} t
  ON s.{source_col} = t.{target_col};"""
            
            print(f"-- {source_table} -> {target_table}")
            print(sql)
            print()


if __name__ == "__main__":
    # Run examples (comment out the ones you don't need)
    
    # example_basic_usage()
    # example_without_llm()
    # example_access_detailed_info()
    # example_filter_high_confidence()
    # example_generate_sql()
    
    print("Uncomment examples in example_usage.py to run them")
