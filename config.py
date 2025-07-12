"""
Configuration file for Pressure Monitor

All configurable parameters are defined here for easy maintenance and customization.
"""

import os
from typing import Dict, Any

class Config:
    """Configuration class for Pressure Monitor."""
    
    # Pressure monitoring settings
    PRESSURE_THRESHOLD_MMHG = 8.0  # mmHg - threshold for pressure drop alert
    
    # API settings
    OPENWEATHER_API_URL = "https://api.openweathermap.org/data/2.5/forecast"
    OPENWEATHER_UNITS = "metric"  # Use metric units for consistent pressure values
    API_TIMEOUT = 30  # seconds
    
    # Telegram API settings
    TELEGRAM_API_URL = "https://api.telegram.org/bot"
    TELEGRAM_PARSE_MODE = "HTML"
    TELEGRAM_DISABLE_WEB_PAGE_PREVIEW = True
    
    # Retry settings
    MAX_RETRIES = 10
    RETRY_DELAY = 60  # seconds
    
    # Forecast analysis settings
    FORECAST_HOURS = 24  # hours to analyze
    FORECAST_INTERVALS = 8  # number of 3-hour intervals to check (8 * 3 = 24 hours)
    
    # Logging settings
    LOG_LEVEL = "INFO"
    LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
    LOG_FILE = 'pressure_monitor.log'
    
    # Webhook settings
    WEBHOOK_TIMEOUT = 30  # seconds
    
    # Unit conversion
    HPA_TO_MMHG_RATIO = 0.750062
    
    # Notification channels configuration
    NOTIFICATION_CHANNELS = {
        'ifttt': {
            'enabled': False,
            'webhook_url': os.getenv('IFTT_WEBHOOK_URL'),
            'timeout': 30  # seconds
        },
        'telegram': {
            'enabled': True,
            'bot_token': os.getenv('TELEGRAM_BOT_TOKEN'),
            'chat_id': os.getenv('TELEGRAM_CHAT_ID'),
            'parse_mode': os.getenv('TELEGRAM_PARSE_MODE', 'HTML'),
            'disable_web_page_preview': True,
            'timeout': 30  # seconds
        }
    }
    
    @classmethod
    def get_environment_variables(cls) -> Dict[str, str]:
        """Get required environment variables."""
        return {
            'OPENWEATHER_API_KEY': os.getenv('OPENWEATHER_API_KEY'),
            'COORDINATES': os.getenv('COORDINATES')
        }
    
    @classmethod
    def validate_environment(cls) -> None:
        """Validate that all required environment variables are set."""
        env_vars = cls.get_environment_variables()
        missing_vars = [key for key, value in env_vars.items() if not value]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        # Validate that at least one notification channel is enabled and configured
        enabled_channels = []
        for channel_name, config in cls.NOTIFICATION_CHANNELS.items():
            if config.get('enabled', False):
                enabled_channels.append(channel_name)
        
        if not enabled_channels:
            raise ValueError("No notification channels are enabled. Please enable at least one channel in the configuration.")
    
    @classmethod
    def parse_coordinates(cls, coordinates: str) -> tuple[float, float]:
        """Parse coordinates string into lat, lon tuple."""
        try:
            lat, lon = coordinates.split(',')
            return float(lat.strip()), float(lon.strip())
        except ValueError:
            raise ValueError("COORDINATES must be in format 'lat,lon' (e.g., '40.7128,-74.0060')")
    
    @classmethod
    def get_api_params(cls, lat: float, lon: float, api_key: str) -> Dict[str, Any]:
        """Get API parameters for OpenWeather request."""
        return {
            'lat': lat,
            'lon': lon,
            'appid': api_key,
            'units': cls.OPENWEATHER_UNITS
        }
    
    @classmethod
    def get_enabled_channels(cls) -> Dict[str, Dict[str, Any]]:
        """Get enabled notification channels."""
        return {
            name: config for name, config in cls.NOTIFICATION_CHANNELS.items()
            if config.get('enabled', False)
        }
    
    @classmethod
    def get_channel_config(cls, channel_name: str) -> Dict[str, Any]:
        """Get configuration for a specific channel."""
        return cls.NOTIFICATION_CHANNELS.get(channel_name, {})
    
    @classmethod
    def is_channel_enabled(cls, channel_name: str) -> bool:
        """Check if a specific channel is enabled."""
        config = cls.get_channel_config(channel_name)
        return config.get('enabled', False) 