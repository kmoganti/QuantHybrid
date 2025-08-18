"""
Simple test runner that doesn't use pytest directly
"""
import unittest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class BasicTests(unittest.TestCase):
    """Basic test cases"""
    
    def test_imports(self):
        """Test that we can import our modules"""
        from config import settings
        self.assertIsNotNone(settings)
    
    def test_settings(self):
        """Test settings configuration"""
        from config.settings import Settings
        settings = Settings()
        self.assertIsNotNone(settings.DATABASE_URL)
    
    def test_environment(self):
        """Test environment setup"""
        import os
        self.assertIsNotNone(os.getenv('PYTHONPATH'))

def run_tests():
    """Run the tests"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(BasicTests)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
