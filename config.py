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
    
    @classmethod
    def get_environment_variables(cls) -> Dict[str, str]:
        """Get required environment variables."""
        return {
            'OPENWEATHER_API_KEY': os.getenv('OPENWEATHER_API_KEY'),
            'IFTT_WEBHOOK_URL': os.getenv('IFTT_WEBHOOK_URL'),
            'COORDINATES': os.getenv('COORDINATES')
        }
    
    @classmethod
    def validate_environment(cls) -> None:
        """Validate that all required environment variables are set."""
        env_vars = cls.get_environment_variables()
        missing_vars = [key for key, value in env_vars.items() if not value]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
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
    def get_webhook_payload(cls, pressure_data: Dict[str, Any]) -> Dict[str, str]:
        """Format webhook payload for IFTT."""
        return {
            'value1': f"Pressure Alert: {pressure_data['pressure_drop']:.1f} mmHg drop expected",
            'value2': f"Current: {pressure_data['current_pressure']:.1f} mmHg, Min: {pressure_data['min_pressure']:.1f} mmHg",
            'value3': f"Expected at: {pressure_data['min_pressure_time'].strftime('%Y-%m-%d %H:%M')}"
        } 