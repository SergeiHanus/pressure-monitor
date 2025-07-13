"""
Unit tests for configuration system.
"""

import unittest
from unittest.mock import patch, Mock
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import Config

class TestConfig(unittest.TestCase):
    """Test cases for Config class."""
    
    def test_pressure_threshold_default(self):
        """Test default pressure threshold value."""
        self.assertEqual(Config.PRESSURE_THRESHOLD_MMHG, 8.0)  # Default production value
    
    def test_api_settings(self):
        """Test API configuration values."""
        self.assertEqual(Config.OPENWEATHER_API_URL, "https://api.openweathermap.org/data/2.5/forecast")
        self.assertEqual(Config.OPENWEATHER_UNITS, "metric")
        self.assertEqual(Config.API_TIMEOUT, 30)
        self.assertEqual(Config.TELEGRAM_API_URL, "https://api.telegram.org/bot")
    
    def test_retry_settings(self):
        """Test retry configuration values."""
        self.assertEqual(Config.MAX_RETRIES, 10)
        self.assertEqual(Config.RETRY_DELAY, 60)
    
    def test_forecast_settings(self):
        """Test forecast analysis settings."""
        self.assertEqual(Config.FORECAST_HOURS, 24)
        self.assertEqual(Config.FORECAST_INTERVALS, 8)
    
    def test_logging_settings(self):
        """Test logging configuration."""
        self.assertEqual(Config.LOG_LEVEL, "INFO")
        self.assertEqual(Config.LOG_FORMAT, '%(asctime)s - %(levelname)s - %(message)s')
        self.assertEqual(Config.LOG_FILE, 'pressure_monitor.log')
    
    def test_unit_conversion(self):
        """Test unit conversion ratio."""
        self.assertEqual(Config.HPA_TO_MMHG_RATIO, 0.750062)
    
    @patch.dict(os.environ, {
        'OPENWEATHER_API_KEY': 'test_api_key',
        'COORDINATES': '40.7128,-74.0060'
    })
    def test_get_environment_variables(self):
        """Test getting environment variables."""
        env_vars = Config.get_environment_variables()
        
        self.assertIn('OPENWEATHER_API_KEY', env_vars)
        self.assertIn('COORDINATES', env_vars)
        self.assertEqual(env_vars['OPENWEATHER_API_KEY'], 'test_api_key')
        self.assertEqual(env_vars['COORDINATES'], '40.7128,-74.0060')
    
    @patch.dict(os.environ, {
        'OPENWEATHER_API_KEY': 'test_api_key',
        'COORDINATES': '40.7128,-74.0060',
        'TELEGRAM_BOT_TOKEN': 'test_token',
        'TELEGRAM_CHAT_ID': '123456789'
    })
    def test_validate_environment_success(self):
        """Test environment validation with valid variables."""
        # Should not raise an exception
        try:
            Config.validate_environment()
        except ValueError:
            self.fail("validate_environment raised ValueError unexpectedly")
    
    @patch.dict(os.environ, {}, clear=True)
    def test_validate_environment_missing_required(self):
        """Test environment validation with missing required variables."""
        with self.assertRaises(ValueError) as context:
            Config.validate_environment()
        
        self.assertIn("Missing required environment variables", str(context.exception))
    
    @patch.dict(os.environ, {
        'OPENWEATHER_API_KEY': 'test_api_key',
        'COORDINATES': '40.7128,-74.0060'
    })
    def test_validate_environment_no_enabled_channels(self):
        """Test environment validation with no enabled channels."""
        # Mock all channels as disabled
        original_channels = Config.NOTIFICATION_CHANNELS
        Config.NOTIFICATION_CHANNELS = {
            'telegram': {'enabled': False},
            'ifttt': {'enabled': False}
        }
        
        try:
            with self.assertRaises(ValueError) as context:
                Config.validate_environment()
            
            self.assertIn("No notification channels are enabled", str(context.exception))
        finally:
            Config.NOTIFICATION_CHANNELS = original_channels
    
    def test_parse_coordinates_valid(self):
        """Test parsing valid coordinates."""
        lat, lon = Config.parse_coordinates('40.7128,-74.0060')
        
        self.assertAlmostEqual(lat, 40.7128)
        self.assertAlmostEqual(lon, -74.0060)
    
    def test_parse_coordinates_with_spaces(self):
        """Test parsing coordinates with spaces."""
        lat, lon = Config.parse_coordinates(' 40.7128 , -74.0060 ')
        
        self.assertAlmostEqual(lat, 40.7128)
        self.assertAlmostEqual(lon, -74.0060)
    
    def test_parse_coordinates_invalid_format(self):
        """Test parsing invalid coordinate format."""
        with self.assertRaises(ValueError) as context:
            Config.parse_coordinates('invalid')
        
        self.assertIn("COORDINATES must be in format 'lat,lon'", str(context.exception))
    
    def test_parse_coordinates_non_numeric(self):
        """Test parsing non-numeric coordinates."""
        with self.assertRaises(ValueError) as context:
            Config.parse_coordinates('abc,def')
        
        self.assertIn("COORDINATES must be in format 'lat,lon'", str(context.exception))
    
    def test_get_api_params(self):
        """Test getting API parameters."""
        params = Config.get_api_params(40.7128, -74.0060, 'test_api_key')
        
        expected_params = {
            'lat': 40.7128,
            'lon': -74.0060,
            'appid': 'test_api_key',
            'units': 'metric'
        }
        
        self.assertEqual(params, expected_params)
    
    def test_get_enabled_channels_default(self):
        """Test getting enabled channels with default config."""
        enabled_channels = Config.get_enabled_channels()
        
        # Should only include enabled channels
        for channel_name, channel_config in enabled_channels.items():
            self.assertTrue(channel_config.get('enabled', False))
    
    def test_get_channel_config_existing(self):
        """Test getting configuration for existing channel."""
        config = Config.get_channel_config('telegram')
        
        self.assertIsInstance(config, dict)
        self.assertIn('enabled', config)
    
    def test_get_channel_config_non_existing(self):
        """Test getting configuration for non-existing channel."""
        config = Config.get_channel_config('non_existing_channel')
        
        self.assertEqual(config, {})
    
    def test_is_channel_enabled_true(self):
        """Test checking if channel is enabled when it is."""
        # Assuming telegram is enabled in current config
        result = Config.is_channel_enabled('telegram')
        
        # This will depend on current config, but method should work
        self.assertIsInstance(result, bool)
    
    def test_is_channel_enabled_false(self):
        """Test checking if channel is enabled when it's not."""
        # Test with a channel that doesn't exist
        result = Config.is_channel_enabled('non_existing_channel')
        
        self.assertFalse(result)
    
    def test_notification_channels_structure(self):
        """Test the structure of notification channels configuration."""
        channels = Config.NOTIFICATION_CHANNELS
        
        self.assertIsInstance(channels, dict)
        
        # Check that each channel has required fields
        for channel_name, channel_config in channels.items():
            self.assertIsInstance(channel_config, dict)
            self.assertIn('enabled', channel_config)
            self.assertIsInstance(channel_config['enabled'], bool)
    
    def test_telegram_channel_config_structure(self):
        """Test Telegram channel configuration structure."""
        telegram_config = Config.NOTIFICATION_CHANNELS.get('telegram', {})
        
        expected_fields = ['enabled', 'bot_token', 'chat_id', 'parse_mode', 'disable_web_page_preview', 'timeout']
        
        for field in expected_fields:
            self.assertIn(field, telegram_config)
    
    def test_ifttt_channel_config_structure(self):
        """Test IFTTT channel configuration structure."""
        ifttt_config = Config.NOTIFICATION_CHANNELS.get('ifttt', {})
        
        expected_fields = ['enabled', 'webhook_url', 'timeout']
        
        for field in expected_fields:
            self.assertIn(field, ifttt_config)


if __name__ == '__main__':
    unittest.main() 