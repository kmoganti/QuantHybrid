"""
Debug script to test imports and environment
"""
import sys
import os
from pathlib import Path

def main():
    print("Python Version:", sys.version)
    print("\nPython Path:")
    for path in sys.path:
        print(f"  - {path}")
    
    print("\nCurrent Directory:", os.getcwd())
    print("\nTrying imports...")
    
    try:
        from config.settings import Settings
        print("✓ Successfully imported Settings")
        
        settings = Settings()
        print("✓ Successfully created Settings instance")
        print("  DATABASE_URL:", settings.DATABASE_URL)
        
    except ImportError as e:
        print("✗ Import Error:", str(e))
    except Exception as e:
        print("✗ Error:", str(e))
        
if __name__ == "__main__":
    main()
