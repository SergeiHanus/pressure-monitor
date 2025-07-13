"""
Unit tests for main pressure monitor functionality.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pressure_monitor import PressureMonitor
from config import Config

class TestPressureMonitor(unittest.TestCase):
    """Test cases for PressureMonitor class."""
    
    @patch.dict(os.environ, {
        'OPENWEATHER_API_KEY': 'test_api_key',
        'COORDINATES': '40.7128,-74.0060',
        'TELEGRAM_BOT_TOKEN': 'test_token',
        'TELEGRAM_CHAT_ID': '123456789'
    })
    @patch('pressure_monitor.Config.get_enabled_channels')
    def setUp(self, mock_get_enabled_channels):
        """Set up test fixtures."""
        # Mock enabled channels to avoid actual channel initialization
        mock_get_enabled_channels.return_value = {}
        
        self.monitor = PressureMonitor()
        
        # Mock forecast data
        self.mock_forecast_data = {
            'list': [
                {'main': {'pressure': 1013}, 'dt': 1642123456},  # Current
                {'main': {'pressure': 1010}, 'dt': 1642134056},  # +3h
                {'main': {'pressure': 1007}, 'dt': 1642144656},  # +6h
                {'main': {'pressure': 1004}, 'dt': 1642155256},  # +9h
                {'main': {'pressure': 1001}, 'dt': 1642165856},  # +12h
                {'main': {'pressure': 1000}, 'dt': 1642176456},  # +15h
                {'main': {'pressure': 1000}, 'dt': 1642187056},  # +18h
                {'main': {'pressure': 1000}, 'dt': 1642197656},  # +21h
            ]
        }
    
    def test_hpa_to_mmhg_conversion(self):
        """Test hectopascal to mmHg conversion."""
        # Test known conversion
        result = self.monitor.hPa_to_mmHg(1013)
        expected = 1013 * Config.HPA_TO_MMHG_RATIO
        
        self.assertAlmostEqual(result, expected, places=2)
    
    def test_hpa_to_mmhg_zero(self):
        """Test conversion with zero value."""
        result = self.monitor.hPa_to_mmHg(0)
        self.assertEqual(result, 0)
    
    @patch('requests.get')
    def test_get_weather_forecast_success(self, mock_get):
        """Test successful weather forecast retrieval."""
        # Mock successful response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = self.mock_forecast_data
        mock_get.return_value = mock_response
        
        result = self.monitor.get_weather_forecast()
        
        self.assertEqual(result, self.mock_forecast_data)
        mock_get.assert_called_once()
    
    @patch('requests.get')
    @patch('time.sleep')
    def test_get_weather_forecast_retry_success(self, mock_sleep, mock_get):
        """Test weather forecast retrieval with retry success."""
        # Mock first call fails, second succeeds
        mock_response_fail = Mock()
        mock_response_fail.raise_for_status.side_effect = Exception("Connection error")
        
        mock_response_success = Mock()
        mock_response_success.raise_for_status.return_value = None
        mock_response_success.json.return_value = self.mock_forecast_data
        
        mock_get.side_effect = [mock_response_fail, mock_response_success]
        
        result = self.monitor.get_weather_forecast()
        
        self.assertEqual(result, self.mock_forecast_data)
        self.assertEqual(mock_get.call_count, 2)
        mock_sleep.assert_called_once_with(Config.RETRY_DELAY)
    
    @patch('requests.get')
    @patch('time.sleep')
    def test_get_weather_forecast_max_retries_exceeded(self, mock_sleep, mock_get):
        """Test weather forecast retrieval when max retries exceeded."""
        # Mock all calls fail
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("Connection error")
        mock_get.return_value = mock_response
        
        result = self.monitor.get_weather_forecast()
        
        self.assertIsNone(result)
        self.assertEqual(mock_get.call_count, Config.MAX_RETRIES)
        self.assertEqual(mock_sleep.call_count, Config.MAX_RETRIES - 1)
    
    def test_analyze_pressure_changes_alert_triggered(self):
        """Test pressure analysis when alert should be triggered."""
        # Pressure drops from 1013 to 1000 hPa = 13 hPa = ~9.75 mmHg (> 8 mmHg threshold)
        result = self.monitor.analyze_pressure_changes(self.mock_forecast_data)
        
        self.assertIsNotNone(result)
        self.assertTrue(result['triggered'])
        self.assertAlmostEqual(result['current_pressure'], 759.81, places=1)  # 1013 * 0.750062
        self.assertAlmostEqual(result['min_pressure'], 750.06, places=1)      # 1000 * 0.750062
        self.assertAlmostEqual(result['pressure_drop'], 9.75, places=1)       # 13 * 0.750062
        self.assertEqual(result['threshold'], Config.PRESSURE_THRESHOLD_MMHG)
    
    def test_analyze_pressure_changes_no_alert(self):
        """Test pressure analysis when no alert should be triggered."""
        # Create forecast with minimal pressure drop
        minimal_drop_forecast = {
            'list': [
                {'main': {'pressure': 1013}, 'dt': 1642123456},  # Current
                {'main': {'pressure': 1012}, 'dt': 1642134056},  # Small drop
                {'main': {'pressure': 1011}, 'dt': 1642144656},
                {'main': {'pressure': 1010}, 'dt': 1642155256},
                {'main': {'pressure': 1009}, 'dt': 1642165856},
                {'main': {'pressure': 1008}, 'dt': 1642176456},
                {'main': {'pressure': 1007}, 'dt': 1642187056},
                {'main': {'pressure': 1006}, 'dt': 1642197656},  # 7 hPa drop = ~5.25 mmHg (< 8 mmHg)
            ]
        }
        
        # Temporarily set threshold to 8 for this test
        original_threshold = Config.PRESSURE_THRESHOLD_MMHG
        Config.PRESSURE_THRESHOLD_MMHG = 8.0
        
        try:
            result = self.monitor.analyze_pressure_changes(minimal_drop_forecast)
            self.assertIsNone(result)
        finally:
            Config.PRESSURE_THRESHOLD_MMHG = original_threshold
    
    def test_analyze_pressure_changes_invalid_data(self):
        """Test pressure analysis with invalid forecast data."""
        invalid_data = {'list': []}
        
        result = self.monitor.analyze_pressure_changes(invalid_data)
        
        self.assertIsNone(result)
    
    def test_analyze_pressure_changes_missing_keys(self):
        """Test pressure analysis with missing required keys."""
        invalid_data = {
            'list': [
                {'invalid': 'data'}
            ]
        }
        
        result = self.monitor.analyze_pressure_changes(invalid_data)
        
        self.assertIsNone(result)
    
    @patch('pressure_monitor.PressureMonitor._initialize_channels')
    def test_send_notifications_success(self, mock_init_channels):
        """Test successful notification sending."""
        # Mock successful channel
        mock_channel = Mock()
        mock_channel.send_notification.return_value = True
        
        self.monitor.notification_channels = {'test_channel': mock_channel}
        
        pressure_data = {
            'pressure_drop': 10.0,
            'current_pressure': 760.0,
            'min_pressure': 750.0,
            'min_pressure_time': datetime.now(),
            'threshold': 8.0
        }
        
        results = self.monitor.send_notifications(pressure_data)
        
        self.assertEqual(results, {'test_channel': True})
        mock_channel.send_notification.assert_called_once_with(pressure_data)
    
    @patch('pressure_monitor.PressureMonitor._initialize_channels')
    def test_send_notifications_failure(self, mock_init_channels):
        """Test notification sending with channel failure."""
        # Mock failing channel
        mock_channel = Mock()
        mock_channel.send_notification.return_value = False
        
        self.monitor.notification_channels = {'test_channel': mock_channel}
        
        pressure_data = {
            'pressure_drop': 10.0,
            'current_pressure': 760.0,
            'min_pressure': 750.0,
            'min_pressure_time': datetime.now(),
            'threshold': 8.0
        }
        
        results = self.monitor.send_notifications(pressure_data)
        
        self.assertEqual(results, {'test_channel': False})
    
    @patch('pressure_monitor.PressureMonitor._initialize_channels')
    def test_send_notifications_exception(self, mock_init_channels):
        """Test notification sending with channel exception."""
        # Mock channel that raises exception
        mock_channel = Mock()
        mock_channel.send_notification.side_effect = Exception("Channel error")
        
        self.monitor.notification_channels = {'test_channel': mock_channel}
        
        pressure_data = {
            'pressure_drop': 10.0,
            'current_pressure': 760.0,
            'min_pressure': 750.0,
            'min_pressure_time': datetime.now(),
            'threshold': 8.0
        }
        
        results = self.monitor.send_notifications(pressure_data)
        
        self.assertEqual(results, {'test_channel': False})
    
    @patch('pressure_monitor.PressureMonitor.send_notifications')
    @patch('pressure_monitor.PressureMonitor.analyze_pressure_changes')
    @patch('pressure_monitor.PressureMonitor.get_weather_forecast')
    def test_run_with_alert(self, mock_get_forecast, mock_analyze, mock_send):
        """Test main run method with pressure alert."""
        # Mock successful forecast and alert
        mock_get_forecast.return_value = self.mock_forecast_data
        mock_analyze.return_value = {
            'triggered': True,
            'pressure_drop': 10.0,
            'current_pressure': 760.0,
            'min_pressure': 750.0,
            'min_pressure_time': datetime.now(),
            'threshold': 8.0
        }
        mock_send.return_value = {'test_channel': True}
        
        # Should not raise exception
        self.monitor.run()
        
        mock_get_forecast.assert_called_once()
        mock_analyze.assert_called_once_with(self.mock_forecast_data)
        mock_send.assert_called_once()
    
    @patch('pressure_monitor.PressureMonitor.analyze_pressure_changes')
    @patch('pressure_monitor.PressureMonitor.get_weather_forecast')
    def test_run_no_alert(self, mock_get_forecast, mock_analyze):
        """Test main run method with no pressure alert."""
        # Mock successful forecast but no alert
        mock_get_forecast.return_value = self.mock_forecast_data
        mock_analyze.return_value = None
        
        # Should not raise exception
        self.monitor.run()
        
        mock_get_forecast.assert_called_once()
        mock_analyze.assert_called_once_with(self.mock_forecast_data)
    
    @patch('pressure_monitor.PressureMonitor.get_weather_forecast')
    def test_run_forecast_failure(self, mock_get_forecast):
        """Test main run method when forecast retrieval fails."""
        # Mock forecast failure
        mock_get_forecast.return_value = None
        
        # Should not raise exception
        self.monitor.run()
        
        mock_get_forecast.assert_called_once()


if __name__ == '__main__':
    unittest.main() 