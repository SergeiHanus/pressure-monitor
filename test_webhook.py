#!/usr/bin/env python3
"""
Test script for Pressure Monitor webhook functionality

This script mocks OpenWeather API responses to simulate pressure drop scenarios
and test the webhook triggering functionality.
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from dotenv import load_dotenv
from config import Config
from pressure_monitor import PressureMonitor

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format=Config.LOG_FORMAT,
    handlers=[
        logging.FileHandler('test_webhook.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class MockPressureMonitor(PressureMonitor):
    """Mock version of PressureMonitor that uses simulated forecast data."""
    
    def __init__(self, test_scenario: str = "pressure_drop"):
        """Initialize with test scenario."""
        super().__init__()
        self.test_scenario = test_scenario
        logger.info(f"Initialized mock pressure monitor with scenario: {test_scenario}")
    
    def get_weather_forecast(self) -> Dict[str, Any]:
        """Return mock forecast data based on test scenario."""
        current_time = datetime.now()
        
        if self.test_scenario == "pressure_drop":
            # Scenario: Pressure drops from 1013 hPa to 1000 hPa (13 hPa = ~9.75 mmHg drop)
            return self._create_mock_forecast_pressure_drop(current_time)
        elif self.test_scenario == "no_drop":
            # Scenario: Pressure stays stable (no alert)
            return self._create_mock_forecast_no_drop(current_time)
        elif self.test_scenario == "minimal_drop":
            # Scenario: Pressure drops just below threshold (7 mmHg drop)
            return self._create_mock_forecast_minimal_drop(current_time)
        else:
            raise ValueError(f"Unknown test scenario: {self.test_scenario}")
    
    def _create_mock_forecast_pressure_drop(self, current_time: datetime) -> Dict[str, Any]:
        """Create mock forecast with significant pressure drop."""
        forecasts = []
        
        # Current pressure: 1013 hPa
        current_pressure = 1013
        
        # Pressure values that create a 13 hPa drop over 24 hours
        pressure_values = [1013, 1010, 1007, 1004, 1001, 1000, 1000, 1000]
        
        for i, pressure in enumerate(pressure_values):
            forecast_time = current_time + timedelta(hours=i * 3)
            forecasts.append({
                'dt': int(forecast_time.timestamp()),
                'main': {
                    'pressure': pressure,
                    'temp': 20 + i,  # Mock temperature
                    'humidity': 60 + i  # Mock humidity
                },
                'weather': [{'description': 'Cloudy'}],
                'dt_txt': forecast_time.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return {
            'list': forecasts,
            'city': {'name': 'Test City', 'coord': {'lat': self.lat, 'lon': self.lon}}
        }
    
    def _create_mock_forecast_no_drop(self, current_time: datetime) -> Dict[str, Any]:
        """Create mock forecast with stable pressure (no alert)."""
        forecasts = []
        base_pressure = 1013
        
        for i in range(8):
            forecast_time = current_time + timedelta(hours=i * 3)
            forecasts.append({
                'dt': int(forecast_time.timestamp()),
                'main': {
                    'pressure': base_pressure + i,  # Slight increase
                    'temp': 20 + i,
                    'humidity': 60 + i
                },
                'weather': [{'description': 'Clear'}],
                'dt_txt': forecast_time.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return {
            'list': forecasts,
            'city': {'name': 'Test City', 'coord': {'lat': self.lat, 'lon': self.lon}}
        }
    
    def _create_mock_forecast_minimal_drop(self, current_time: datetime) -> Dict[str, Any]:
        """Create mock forecast with minimal pressure drop (below threshold)."""
        forecasts = []
        
        # Pressure values that create a 7 mmHg drop (just below 8 mmHg threshold)
        pressure_values = [1013, 1011, 1009, 1007, 1005, 1004, 1004, 1004]
        
        for i, pressure in enumerate(pressure_values):
            forecast_time = current_time + timedelta(hours=i * 3)
            forecasts.append({
                'dt': int(forecast_time.timestamp()),
                'main': {
                    'pressure': pressure,
                    'temp': 20 + i,
                    'humidity': 60 + i
                },
                'weather': [{'description': 'Partly Cloudy'}],
                'dt_txt': forecast_time.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return {
            'list': forecasts,
            'city': {'name': 'Test City', 'coord': {'lat': self.lat, 'lon': self.lon}}
        }

def test_webhook_scenarios():
    """Test different webhook scenarios."""
    scenarios = [
        ("pressure_drop", "Should trigger webhook - significant pressure drop"),
        ("no_drop", "Should NOT trigger webhook - stable pressure"),
        ("minimal_drop", "Should NOT trigger webhook - minimal pressure drop")
    ]
    
    for scenario, description in scenarios:
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing scenario: {scenario}")
        logger.info(f"Description: {description}")
        logger.info(f"{'='*60}")
        
        try:
            monitor = MockPressureMonitor(scenario)
            monitor.run()
            
            if scenario == "pressure_drop":
                logger.info("✅ Expected: Webhook should have been triggered")
            else:
                logger.info("✅ Expected: No webhook should have been triggered")
                
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
        
        time.sleep(2)  # Brief pause between tests

def test_webhook_payload_format():
    """Test the webhook payload format directly."""
    logger.info(f"\n{'='*60}")
    logger.info("Testing webhook payload format")
    logger.info(f"{'='*60}")
    
    # Create mock pressure data
    mock_pressure_data = {
        'triggered': True,
        'current_pressure': 760.0,  # mmHg
        'min_pressure': 750.0,      # mmHg
        'pressure_drop': 10.0,      # mmHg
        'min_pressure_time': datetime.now() + timedelta(hours=12),
        'threshold': Config.PRESSURE_THRESHOLD_MMHG
    }
    
    # Test payload generation
    payload = Config.get_webhook_payload(mock_pressure_data)
    
    logger.info("Generated webhook payload:")
    for key, value in payload.items():
        logger.info(f"  {key}: {value}")
    
    logger.info("✅ Payload format test completed")

def main():
    """Main test function."""
    logger.info("Starting webhook test scenarios")
    
    # Test webhook payload format
    test_webhook_payload_format()
    
    # Test different scenarios
    test_webhook_scenarios()
    
    logger.info("\n🎉 All tests completed!")

if __name__ == "__main__":
    main() 