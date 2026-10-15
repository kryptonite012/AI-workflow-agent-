"""
Simple test runner for hierarchical agent tests
"""
import sys
import os

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

if __name__ == '__main__':
    # Import the test module
    from test_hierarchical_agent import *
    
    # Run the tests with detailed output
    import unittest
    unittest.main(verbosity=2)