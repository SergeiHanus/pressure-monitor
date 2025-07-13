#!/usr/bin/env python3
"""
Integration tests for Pressure Monitor functionality

This script provides integration tests including mocked scenarios for testing
the complete pressure monitoring workflow.
"""

import os
import sys
import time
import logging
import unittest
from datetime import datetime, timedelta
from typing import Dict, Any
from unittest.mock import patch, Mock

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
from config import Config
from pressure_monitor import PressureMonitor

# Load environment variables
load_dotenv()

class MockPressureMonitor(PressureMonitor):
    """Mock version of PressureMonitor that uses simulated forecast data."""
    
    def __init__(self, test_scenario: str = "pressure_drop"):
        """Initialize with test scenario."""
        super().__init__()
        self.test_scenario = test_scenario
        logging.info(f"Initialized mock pressure monitor with scenario: {test_scenario}")
    
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
        
        # Pressure values that create a 13 hPa drop over 24 hours
        pressure_values = [1013, 1010, 1007, 1004, 1001, 1000, 1000, 1000]
        
        for i, pressure in enumerate(pressure_values):
            forecast_time = current_time + timedelta(hours=i * 3)
            forecasts.append({
                'dt': int(forecast_time.timestamp()),
                'main': {
                    'pressure': pressure,
                    'temp': 20 + i,
                    'humidity': 60 + i
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
        
        # Pressure values that create a 7 hPa drop (just below 8 mmHg threshold)
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


class TestPressureMonitorIntegration(unittest.TestCase):
    """Integration tests for the complete pressure monitoring system."""
    
    @patch.dict(os.environ, {
        'OPENWEATHER_API_KEY': 'test_api_key',
        'COORDINATES': '40.7128,-74.0060',
        'TELEGRAM_BOT_TOKEN': 'test_token',
        'TELEGRAM_CHAT_ID': '123456789'
    })
    def setUp(self):
        """Set up integration test fixtures."""
        # Configure logging for tests
        logging.basicConfig(level=logging.INFO)
        
        self.pressure_data = {
            'triggered': True,
            'current_pressure': 760.0,
            'min_pressure': 750.0,
            'pressure_drop': 10.0,
            'min_pressure_time': datetime.now(),
            'threshold': Config.PRESSURE_THRESHOLD_MMHG
        }
    
    @patch('channels.telegram_channel.requests.post')
    def test_pressure_drop_scenario(self, mock_post):
        """Test complete workflow with pressure drop scenario."""
        # Mock successful Telegram response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {'ok': True, 'result': {'message_id': 123}}
        mock_post.return_value = mock_response
        
        # Create mock monitor with pressure drop scenario
        monitor = MockPressureMonitor("pressure_drop")
        
        # Run the monitoring check
        monitor.run()
        
        # If Telegram is enabled, verify webhook was called
        if Config.is_channel_enabled('telegram'):
            mock_post.assert_called()
    
    @patch('channels.telegram_channel.requests.post')
    def test_no_drop_scenario(self, mock_post):
        """Test complete workflow with no pressure drop scenario."""
        # Create mock monitor with no drop scenario
        monitor = MockPressureMonitor("no_drop")
        
        # Run the monitoring check
        monitor.run()
        
        # Webhook should not be called for no drop scenario
        mock_post.assert_not_called()
    
    @patch('channels.telegram_channel.requests.post')
    def test_minimal_drop_scenario(self, mock_post):
        """Test complete workflow with minimal pressure drop scenario."""
        # Create mock monitor with minimal drop scenario
        monitor = MockPressureMonitor("minimal_drop")
        
        # Run the monitoring check
        monitor.run()
        
        # Webhook should not be called for minimal drop (below threshold)
        mock_post.assert_not_called()
    
    def test_webhook_payload_format(self):
        """Test the webhook payload format directly."""
        from datetime import datetime
        
        # Create mock pressure data
        mock_pressure_data = {
            'triggered': True,
            'current_pressure': 760.0,
            'min_pressure': 750.0,
            'pressure_drop': 10.0,
            'min_pressure_time': datetime.now() + timedelta(hours=12),
            'threshold': Config.PRESSURE_THRESHOLD_MMHG
        }
        
        # Test Telegram channel formatting
        if Config.is_channel_enabled('telegram'):
            from channels.telegram_channel import TelegramChannel
            
            config = Config.get_channel_config('telegram')
            if config.get('bot_token') and config.get('chat_id'):
                channel = TelegramChannel(config)
                payload = channel.format_message(mock_pressure_data)
                
                # Verify payload structure
                self.assertIn('text', payload)
                self.assertIn('parse_mode', payload)
                self.assertIn('disable_web_page_preview', payload)
                
                # Verify content
                text = payload['text']
                self.assertIn('⚠️', text)
                self.assertIn('Pressure Alert', text)
                self.assertIn('10.0 mmHg', text)


def test_webhook_scenarios():
    """Test different webhook scenarios."""
    scenarios = [
        ("pressure_drop", "Should trigger webhook - significant pressure drop"),
        ("no_drop", "Should NOT trigger webhook - stable pressure"),
        ("minimal_drop", "Should NOT trigger webhook - minimal pressure drop")
    ]
    
    for scenario, description in scenarios:
        print(f"\n{'='*60}")
        print(f"Testing scenario: {scenario}")
        print(f"Description: {description}")
        print(f"{'='*60}")
        
        try:
            monitor = MockPressureMonitor(scenario)
            monitor.run()
            
            if scenario == "pressure_drop":
                print("✅ Expected: Webhook should have been triggered")
            else:
                print("✅ Expected: No webhook should have been triggered")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
        
        time.sleep(1)  # Brief pause between tests


def main():
    """Main test function for manual execution."""
    print("Starting webhook integration tests")
    
    # Test webhook payload format
    print(f"\n{'='*60}")
    print("Testing webhook payload format")
    print(f"{'='*60}")
    
    # Create mock pressure data
    mock_pressure_data = {
        'triggered': True,
        'current_pressure': 760.0,
        'min_pressure': 750.0,
        'pressure_drop': 10.0,
        'min_pressure_time': datetime.now() + timedelta(hours=12),
        'threshold': Config.PRESSURE_THRESHOLD_MMHG
    }
    
    # Test Telegram payload if enabled
    if Config.is_channel_enabled('telegram'):
        from channels.telegram_channel import TelegramChannel
        
        config = Config.get_channel_config('telegram')
        channel = TelegramChannel(config)
        payload = channel.format_message(mock_pressure_data)
        
        print("Generated Telegram payload:")
        for key, value in payload.items():
            if key == 'text':
                print(f"  {key}: {value[:100]}...")  # Truncate long text
            else:
                print(f"  {key}: {value}")
    
    print("✅ Payload format test completed")
    
    # Test different scenarios
    test_webhook_scenarios()
    
    print("\n🎉 All integration tests completed!")


if __name__ == '__main__':
    # Check if running as unittest
    if len(sys.argv) > 1 and sys.argv[1] == 'unittest':
        unittest.main(argv=[''], exit=False)
    else:
        main() 