"""
Unit tests for Telegram notification channel.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import requests
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from channels.telegram_channel import TelegramChannel
from config import Config

class TestTelegramChannel(unittest.TestCase):
    """Test cases for TelegramChannel."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.valid_config = {
            'bot_token': 'test_bot_token',
            'chat_id': '123456789',
            'parse_mode': 'HTML',
            'disable_web_page_preview': True,
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
        channel = TelegramChannel(self.valid_config)
        
        self.assertEqual(channel.bot_token, 'test_bot_token')
        self.assertEqual(channel.chat_id, '123456789')
        self.assertEqual(channel.parse_mode, 'HTML')
        self.assertTrue(channel.disable_web_page_preview)
    
    def test_init_with_defaults(self):
        """Test initialization with default values."""
        minimal_config = {
            'bot_token': 'test_bot_token',
            'chat_id': '123456789'
        }
        
        channel = TelegramChannel(minimal_config)
        
        self.assertEqual(channel.parse_mode, Config.TELEGRAM_PARSE_MODE)
        self.assertEqual(channel.disable_web_page_preview, Config.TELEGRAM_DISABLE_WEB_PAGE_PREVIEW)
    
    def test_validate_config_valid(self):
        """Test configuration validation with valid config."""
        channel = TelegramChannel(self.valid_config)
        self.assertTrue(channel.validate_config())
    
    def test_validate_config_missing_token(self):
        """Test configuration validation with missing bot token."""
        invalid_config = self.valid_config.copy()
        invalid_config['bot_token'] = None
        
        channel = TelegramChannel(invalid_config)
        self.assertFalse(channel.validate_config())
    
    def test_validate_config_missing_chat_id(self):
        """Test configuration validation with missing chat ID."""
        invalid_config = self.valid_config.copy()
        invalid_config['chat_id'] = None
        
        channel = TelegramChannel(invalid_config)
        self.assertFalse(channel.validate_config())
    
    def test_format_message(self):
        """Test message formatting."""
        channel = TelegramChannel(self.valid_config)
        message_data = channel.format_message(self.pressure_data)
        
        self.assertIn('text', message_data)
        self.assertIn('parse_mode', message_data)
        self.assertIn('disable_web_page_preview', message_data)
        
        # Check message content
        text = message_data['text']
        self.assertIn('⚠️', text)
        self.assertIn('Pressure Alert', text)
        self.assertIn('10.0 mmHg', text)
        self.assertIn('760.0 mmHg', text)
        self.assertIn('750.0 mmHg', text)
        self.assertIn('2025-01-15 18:00', text)
        self.assertIn('8.0 mmHg', text)
    
    def test_format_message_html_tags(self):
        """Test that message contains proper HTML formatting."""
        channel = TelegramChannel(self.valid_config)
        message_data = channel.format_message(self.pressure_data)
        
        text = message_data['text']
        self.assertIn('<b>', text)
        self.assertIn('</b>', text)
        self.assertIn('<i>', text)
        self.assertIn('</i>', text)
    
    @patch('requests.post')
    def test_send_notification_success(self, mock_post):
        """Test successful notification sending."""
        # Mock successful response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {'ok': True, 'result': {'message_id': 123}}
        mock_post.return_value = mock_response
        
        channel = TelegramChannel(self.valid_config)
        result = channel.send_notification(self.pressure_data)
        
        self.assertTrue(result)
        
        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        
        # Check URL
        expected_url = f"{Config.TELEGRAM_API_URL}test_bot_token/sendMessage"
        self.assertEqual(call_args[0][0], expected_url)
        
        # Check payload
        payload = call_args[1]['json']
        self.assertEqual(payload['chat_id'], '123456789')
        self.assertEqual(payload['parse_mode'], 'HTML')
        self.assertTrue(payload['disable_web_page_preview'])
        self.assertIn('⚠️', payload['text'])
    
    @patch('requests.post')
    def test_send_notification_api_error(self, mock_post):
        """Test notification sending with Telegram API error."""
        # Mock API error response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {'ok': False, 'description': 'Bad Request'}
        mock_post.return_value = mock_response
        
        channel = TelegramChannel(self.valid_config)
        result = channel.send_notification(self.pressure_data)
        
        self.assertFalse(result)
    
    @patch('requests.post')
    def test_send_notification_request_exception(self, mock_post):
        """Test notification sending with request exception."""
        # Mock request exception
        mock_post.side_effect = requests.exceptions.RequestException("Connection error")
        
        channel = TelegramChannel(self.valid_config)
        result = channel.send_notification(self.pressure_data)
        
        self.assertFalse(result)
    
    @patch('requests.post')
    def test_send_notification_timeout_config(self, mock_post):
        """Test that custom timeout is used from config."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {'ok': True}
        mock_post.return_value = mock_response
        
        # Custom timeout in config
        config_with_timeout = self.valid_config.copy()
        config_with_timeout['timeout'] = 60
        
        channel = TelegramChannel(config_with_timeout)
        channel.send_notification(self.pressure_data)
        
        # Verify timeout was used
        call_args = mock_post.call_args
        self.assertEqual(call_args[1]['timeout'], 60)
    
    @patch('requests.post')
    def test_send_notification_default_timeout(self, mock_post):
        """Test that default timeout is used when not in config."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {'ok': True}
        mock_post.return_value = mock_response
        
        # Config without timeout
        config_without_timeout = {
            'bot_token': 'test_bot_token',
            'chat_id': '123456789'
        }
        
        channel = TelegramChannel(config_without_timeout)
        channel.send_notification(self.pressure_data)
        
        # Verify default timeout was used
        call_args = mock_post.call_args
        self.assertEqual(call_args[1]['timeout'], Config.WEBHOOK_TIMEOUT)
    
    def test_message_structure(self):
        """Test the structure of formatted message."""
        channel = TelegramChannel(self.valid_config)
        message_data = channel.format_message(self.pressure_data)
        
        # Check all required fields are present
        required_fields = ['text', 'parse_mode', 'disable_web_page_preview']
        for field in required_fields:
            self.assertIn(field, message_data)
        
        # Check field values
        self.assertEqual(message_data['parse_mode'], 'HTML')
        self.assertTrue(message_data['disable_web_page_preview'])
        self.assertIsInstance(message_data['text'], str)
        self.assertGreater(len(message_data['text']), 0)


class TestTelegramChannelIntegration(unittest.TestCase):
    """Integration tests for Telegram channel."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not self.bot_token or not self.chat_id:
            self.skipTest("Telegram credentials not available for integration tests")
        
        self.config = {
            'bot_token': self.bot_token,
            'chat_id': self.chat_id,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True,
            'timeout': 30
        }
        
        self.pressure_data = {
            'triggered': True,
            'current_pressure': 760.0,
            'min_pressure': 750.0,
            'pressure_drop': 10.0,
            'min_pressure_time': datetime.now(),
            'threshold': 8.0
        }
    
    def test_real_telegram_api_connection(self):
        """Test actual connection to Telegram API."""
        channel = TelegramChannel(self.config)
        
        # This will make a real API call if credentials are available
        result = channel.send_notification(self.pressure_data)
        
        # Should succeed if credentials are valid
        self.assertTrue(result, "Failed to send test message to Telegram")
    
    def test_telegram_api_validation(self):
        """Test validation against real Telegram API."""
        channel = TelegramChannel(self.config)
        
        # Test that configuration is valid
        self.assertTrue(channel.validate_config())
        
        # Test that we can format a message
        message_data = channel.format_message(self.pressure_data)
        self.assertIsInstance(message_data, dict)
        self.assertIn('text', message_data)


if __name__ == '__main__':
    unittest.main() 