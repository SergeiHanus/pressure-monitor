"""
Unit tests for IFTTT notification channel.
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime
import requests
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from channels.ifttt_channel import IFTTTChannel
from config import Config

class TestIFTTTChannel(unittest.TestCase):
    """Test cases for IFTTTChannel."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.valid_config = {
            'webhook_url': 'https://maker.ifttt.com/trigger/test/with/key/test_key',
            'timeout': 30
        }
        
        self.pressure_data = {
            'triggered': True,
            'current_pressure': 760.0,
            'min_pressure': 750.0,
            'pressure_drop': 10.0,
            'min_pressure_time': datetime(2025, 1, 15, 18, 0),
            'threshold': 8.0
        }
    
    def test_init_valid_config(self):
        """Test initialization with valid configuration."""
        channel = IFTTTChannel(self.valid_config)
        
        self.assertEqual(channel.webhook_url, 'https://maker.ifttt.com/trigger/test/with/key/test_key')
    
    def test_validate_config_valid(self):
        """Test configuration validation with valid config."""
        channel = IFTTTChannel(self.valid_config)
        self.assertTrue(channel.validate_config())
    
    def test_validate_config_missing_url(self):
        """Test configuration validation with missing webhook URL."""
        invalid_config = self.valid_config.copy()
        invalid_config['webhook_url'] = None
        
        channel = IFTTTChannel(invalid_config)
        self.assertFalse(channel.validate_config())
    
    def test_format_message(self):
        """Test message formatting for IFTTT."""
        channel = IFTTTChannel(self.valid_config)
        message_data = channel.format_message(self.pressure_data)
        
        # Check required fields
        required_fields = ['value1', 'value2', 'value3']
        for field in required_fields:
            self.assertIn(field, message_data)
        
        # Check content
        self.assertIn('10.0 mmHg drop expected', message_data['value1'])
        self.assertIn('760.0 mmHg', message_data['value2'])
        self.assertIn('750.0 mmHg', message_data['value2'])
        self.assertIn('2025-01-15 18:00', message_data['value3'])
    
    @patch('requests.post')
    def test_send_notification_success(self, mock_post):
        """Test successful notification sending."""
        # Mock successful response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        channel = IFTTTChannel(self.valid_config)
        result = channel.send_notification(self.pressure_data)
        
        self.assertTrue(result)
        
        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        
        # Check URL
        self.assertEqual(call_args[0][0], self.valid_config['webhook_url'])
        
        # Check payload
        payload = call_args[1]['json']
        self.assertIn('value1', payload)
        self.assertIn('value2', payload)
        self.assertIn('value3', payload)
    
    @patch('requests.post')
    def test_send_notification_request_exception(self, mock_post):
        """Test notification sending with request exception."""
        # Mock request exception
        mock_post.side_effect = requests.exceptions.RequestException("Connection error")
        
        channel = IFTTTChannel(self.valid_config)
        result = channel.send_notification(self.pressure_data)
        
        self.assertFalse(result)
    
    @patch('requests.post')
    def test_send_notification_custom_timeout(self, mock_post):
        """Test that custom timeout is used from config."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Custom timeout in config
        config_with_timeout = self.valid_config.copy()
        config_with_timeout['timeout'] = 60
        
        channel = IFTTTChannel(config_with_timeout)
        channel.send_notification(self.pressure_data)
        
        # Verify timeout was used
        call_args = mock_post.call_args
        self.assertEqual(call_args[1]['timeout'], 60)
    
    @patch('requests.post')
    def test_send_notification_default_timeout(self, mock_post):
        """Test that default timeout is used when not in config."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Config without timeout
        config_without_timeout = {
            'webhook_url': 'https://maker.ifttt.com/trigger/test/with/key/test_key'
        }
        
        channel = IFTTTChannel(config_without_timeout)
        channel.send_notification(self.pressure_data)
        
        # Verify default timeout was used
        call_args = mock_post.call_args
        self.assertEqual(call_args[1]['timeout'], Config.WEBHOOK_TIMEOUT)


if __name__ == '__main__':
    unittest.main() 