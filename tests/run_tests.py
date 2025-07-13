#!/usr/bin/env python3
"""
Test runner for Pressure Monitor test suite.

This script runs all tests in the tests directory and provides comprehensive reporting.
"""

import unittest
import sys
import os
from io import StringIO

def discover_and_run_tests():
    """Discover and run all tests in the tests directory."""
    # Add current directory to path for imports
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Discover tests
    loader = unittest.TestLoader()
    start_dir = 'tests'
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Create test runner with detailed output
    stream = StringIO()
    runner = unittest.TextTestRunner(
        stream=stream,
        verbosity=2,
        buffer=True,
        failfast=False
    )
    
    print("=" * 60)
    print("PRESSURE MONITOR TEST SUITE")
    print("=" * 60)
    
    # Run tests
    result = runner.run(suite)
    
    # Print results
    output = stream.getvalue()
    print(output)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print(f"\nFAILURES ({len(result.failures)}):")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if result.errors:
        print(f"\nERRORS ({len(result.errors)}):")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    # Return success/failure
    success = len(result.failures) == 0 and len(result.errors) == 0
    
    if success:
        print(f"\n✅ All tests passed!")
    else:
        print(f"\n❌ Some tests failed!")
    
    return success

def run_specific_test(test_name):
    """Run a specific test module or test case."""
    # Add current directory to path for imports
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    try:
        # Try to load and run the specific test
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromName(test_name)
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return len(result.failures) == 0 and len(result.errors) == 0
        
    except Exception as e:
        print(f"Error running test '{test_name}': {e}")
        return False

def main():
    """Main entry point."""
    if len(sys.argv) == 1:
        # Run all tests
        success = discover_and_run_tests()
    elif len(sys.argv) == 2:
        # Run specific test
        test_name = sys.argv[1]
        print(f"Running specific test: {test_name}")
        success = run_specific_test(test_name)
    else:
        print("Usage:")
        print("  python run_tests.py                    # Run all tests")
        print("  python run_tests.py test_module        # Run specific test module")
        print("  python run_tests.py test_module.TestClass.test_method  # Run specific test")
        sys.exit(1)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 