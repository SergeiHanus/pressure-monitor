#!/usr/bin/env python3
"""
Simple test runner for webhook scenarios

Usage:
    python run_test.py pressure_drop    # Test webhook trigger
    python run_test.py no_drop         # Test no webhook
    python run_test.py minimal_drop    # Test minimal drop (no webhook)
"""

import sys
import os
# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from test_webhook import MockPressureMonitor

def main():
    if len(sys.argv) != 2:
        print("Usage: python run_test.py <scenario>")
        print("Scenarios: pressure_drop, no_drop, minimal_drop")
        sys.exit(1)
    
    scenario = sys.argv[1]
    valid_scenarios = ["pressure_drop", "no_drop", "minimal_drop"]
    
    if scenario not in valid_scenarios:
        print(f"Invalid scenario: {scenario}")
        print(f"Valid scenarios: {', '.join(valid_scenarios)}")
        sys.exit(1)
    
    print(f"Running test scenario: {scenario}")
    print("=" * 50)
    
    try:
        monitor = MockPressureMonitor(scenario)
        monitor.run()
        print(f"\n✅ Test completed for scenario: {scenario}")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 