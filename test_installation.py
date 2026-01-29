"""
Quick installation test script.
Tests that all dependencies are installed correctly.
"""

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    
    try:
        import pandas
        print("  ✓ pandas")
    except ImportError as e:
        print(f"  ✗ pandas: {e}")
        return False
    
    try:
        import numpy
        print("  ✓ numpy")
    except ImportError as e:
        print(f"  ✗ numpy: {e}")
        return False
    
    try:
        import openpyxl
        print("  ✓ openpyxl")
    except ImportError as e:
        print(f"  ✗ openpyxl: {e}")
        return False
    
    try:
        import rapidfuzz
        print("  ✓ rapidfuzz")
    except  ImportError as e:
        print(f"  ✗ rapidfuzz: {e}")
        return False
    
    try:
        from loguru import logger
        print("  ✓ loguru")
    except ImportError as e:
        print(f"  ✗ loguru: {e}")
        return False
    
    try:
        from dotenv import load_dotenv
        print("  ✓ python-dotenv")
    except ImportError as e:
        print(f"  ✗ python-dotenv: {e}")
        return False
    
    return True


def test_project_structure():
    """Test that all source files exist."""
    print("\nTesting project structure...")
    
    from pathlib import Path
    
    required_files = [
        "src/__init__.py",
        "src/config.py",
        "src/excel_loader.py",
        "src/profiling_engine.py",
        "src/relationship_detector.py",
        "src/llm_reasoner.py",
        "src/main.py",
        "src/utils/__init__.py",
        "src/utils/data_types.py",
        "src/utils/pattern_matching.py",
        "requirements.txt",
        ".env.example",
        "README.md",
    ]
    
    all_exist = True
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ {file_path} NOT FOUND")
            all_exist = False
    
    return all_exist


def test_config():
    """Test configuration loading."""
    print("\nTesting configuration...")
    
    try:
        from src.config import Config
        print(f"  ✓ Config loaded")
        print(f"    - Max files: {Config.MAX_FILES_LIMIT}")
        print(f"    - LLM enabled: {Config.ENABLE_LLM_VALIDATION}")
        print(f"    - LLM model: {Config.LLM_MODEL}")
        return True
    except Exception as e:
        print(f"  ✗ Failed to load config: {e}")
        return False


def test_basic_functionality():
    """Test basic component initialization."""
    print("\nTesting basic functionality...")
    
    try:
        from src.excel_loader import ExcelLoader
        loader = ExcelLoader()
        print("  ✓ ExcelLoader initialized")
    except Exception as e:
        print(f"  ✗ ExcelLoader failed: {e}")
        return False
    
    try:
        from src.profiling_engine import ProfilingEngine
        profiler = ProfilingEngine()
        print("  ✓ ProfilingEngine initialized")
    except Exception as e:
        print(f"  ✗ ProfilingEngine failed: {e}")
        return False
    
    try:
        from src.llm_reasoner import LLMReasoner
        llm = LLMReasoner()
        print("  ✓ LLMReasoner initialized")
    except Exception as e:
        print(f"  ✗ LLMReasoner failed: {e}")
        return False
    
    try:
        from src.main import RelationshipDiscovery
        discovery = RelationshipDiscovery()
        print("  ✓ RelationshipDiscovery initialized")
    except Exception as e:
        print(f"  ✗ RelationshipDiscovery failed: {e}")
        return False
    
    return True


def main():
    """Run all tests."""
    print("="*60)
    print("Excel Relationship Discovery System - Installation Test")
    print("="*60)
    
    results = []
    
    results.append(("Import Test", test_imports()))
    results.append(("Project Structure", test_project_structure()))
    results.append(("Configuration", test_config()))
    results.append(("Basic Functionality", test_basic_functionality()))
    
    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("="*60)
    
    if all_passed:
        print("\n🎉 All tests passed! Installation successful.")
        print("\nNext steps:")
        print("  1. Configure Azure AI Foundry credentials in .env")
        print("  2. Run: python -m src.main your_file.xlsx --no-llm")
        print("  3. Check README.md for detailed usage")
    else:
        print("\n⚠️  Some tests failed. Please:")
        print("  1. Ensure all dependencies are installed: pip install -r requirements.txt")
        print("  2. Check that all source files are present")
        print("  3. Review error messages above")
    
    print()


if __name__ == "__main__":
    main()
