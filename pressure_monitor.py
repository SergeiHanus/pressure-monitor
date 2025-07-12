#!/usr/bin/env python3
"""
Pressure Monitor Script

Monitors weather pressure changes using OpenWeather API and triggers IFTT webhook
when forecasted pressure drops more than 8 mmHg in the next 24 hours.
"""

import os
import sys
import time
import logging
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from config import Config
from channels import IFTTTChannel, TelegramChannel

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format=Config.LOG_FORMAT,
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class PressureMonitor:
    """Monitor weather pressure changes and trigger webhooks."""
    
    def __init__(self):
        """Initialize the pressure monitor with configuration."""
        # Validate environment variables
        Config.validate_environment()
        
        # Get environment variables
        env_vars = Config.get_environment_variables()
        self.api_key = env_vars['OPENWEATHER_API_KEY']
        self.coordinates = env_vars['COORDINATES']
        
        # Parse coordinates
        self.lat, self.lon = Config.parse_coordinates(self.coordinates)
        
        # Initialize notification channels
        self.notification_channels = self._initialize_channels()
        
        logger.info(f"Pressure monitor initialized for coordinates: {self.lat}, {self.lon}")
        logger.info(f"Enabled notification channels: {list(self.notification_channels.keys())}")
    
    def _initialize_channels(self) -> Dict[str, Any]:
        """Initialize enabled notification channels."""
        channels = {}
        enabled_channels = Config.get_enabled_channels()
        
        for channel_name, config in enabled_channels.items():
            try:
                if channel_name == 'ifttt':
                    channels[channel_name] = IFTTTChannel(config)
                elif channel_name == 'telegram':
                    channels[channel_name] = TelegramChannel(config)
                else:
                    logger.warning(f"Unknown notification channel: {channel_name}")
            except Exception as e:
                logger.error(f"Failed to initialize {channel_name} channel: {e}")
        
        logger.info(f"Initialized {len(channels)} notification channels")
        return channels
    
    def hPa_to_mmHg(self, hPa: float) -> float:
        """Convert hectopascals to millimeters of mercury."""
        return hPa * Config.HPA_TO_MMHG_RATIO
    
    def get_weather_forecast(self) -> Optional[Dict[str, Any]]:
        """Fetch weather forecast from OpenWeather API with retry logic."""
        params = Config.get_api_params(self.lat, self.lon, self.api_key)
        
        for attempt in range(Config.MAX_RETRIES):
            try:
                logger.info(f"Fetching weather forecast (attempt {attempt + 1}/{Config.MAX_RETRIES})")
                response = requests.get(Config.OPENWEATHER_API_URL, params=params, timeout=Config.API_TIMEOUT)
                response.raise_for_status()
                
                data = response.json()
                logger.info("Successfully fetched weather forecast")
                return data
                
            except requests.exceptions.RequestException as e:
                logger.error(f"API request failed (attempt {attempt + 1}/{Config.MAX_RETRIES}): {e}")
                if attempt < Config.MAX_RETRIES - 1:
                    logger.info(f"Retrying in {Config.RETRY_DELAY} seconds...")
                    time.sleep(Config.RETRY_DELAY)
                else:
                    logger.error("Max retries reached. Will try again at next scheduled run.")
                    return None
    
    def analyze_pressure_changes(self, forecast_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze pressure changes over the next 24 hours."""
        try:
            # Get current pressure (first forecast entry)
            current_pressure_hpa = forecast_data['list'][0]['main']['pressure']
            current_pressure_mmhg = self.hPa_to_mmHg(current_pressure_hpa)
            
            logger.info(f"Current pressure: {current_pressure_mmhg:.2f} mmHg ({current_pressure_hpa} hPa)")
            
            # Analyze next 24 hours (8 entries, 3-hour intervals)
            min_pressure_mmhg = current_pressure_mmhg
            min_pressure_time = datetime.fromtimestamp(forecast_data['list'][0]['dt'])  # Default to current time
            
            for i, forecast in enumerate(forecast_data['list'][:Config.FORECAST_INTERVALS]):  # Next 24 hours
                pressure_hpa = forecast['main']['pressure']
                pressure_mmhg = self.hPa_to_mmHg(pressure_hpa)
                forecast_time = datetime.fromtimestamp(forecast['dt'])
                
                if pressure_mmhg < min_pressure_mmhg:
                    min_pressure_mmhg = pressure_mmhg
                    min_pressure_time = forecast_time
                
                logger.debug(f"Forecast {i+1}: {pressure_mmhg:.2f} mmHg at {forecast_time}")
            
            pressure_drop = current_pressure_mmhg - min_pressure_mmhg
            
            logger.info(f"Minimum forecasted pressure: {min_pressure_mmhg:.2f} mmHg")
            logger.info(f"Pressure drop: {pressure_drop:.2f} mmHg")
            
            if pressure_drop > Config.PRESSURE_THRESHOLD_MMHG:
                return {
                    'triggered': True,
                    'current_pressure': current_pressure_mmhg,
                    'min_pressure': min_pressure_mmhg,
                    'pressure_drop': pressure_drop,
                    'min_pressure_time': min_pressure_time,
                    'threshold': Config.PRESSURE_THRESHOLD_MMHG
                }
            else:
                logger.info(f"Pressure drop ({pressure_drop:.2f} mmHg) below threshold ({Config.PRESSURE_THRESHOLD_MMHG} mmHg)")
                return None
                
        except (KeyError, IndexError, ValueError) as e:
            logger.error(f"Error analyzing pressure data: {e}")
            return None
    
    def send_notifications(self, pressure_data: Dict[str, Any]) -> Dict[str, bool]:
        """Send notifications to all enabled channels."""
        results = {}
        
        for channel_name, channel in self.notification_channels.items():
            try:
                logger.info(f"Sending notification via {channel_name} channel...")
                success = channel.send_notification(pressure_data)
                results[channel_name] = success
                
                if success:
                    logger.info(f"Notification sent successfully via {channel_name}")
                else:
                    logger.error(f"Failed to send notification via {channel_name}")
                    
            except Exception as e:
                logger.error(f"Error sending notification via {channel_name}: {e}")
                results[channel_name] = False
        
        return results
    
    def run(self) -> None:
        """Main execution method."""
        logger.info("Starting pressure monitoring check")
        
        try:
            # Get weather forecast
            forecast_data = self.get_weather_forecast()
            if not forecast_data:
                logger.error("Failed to get weather forecast")
                return
            
            # Analyze pressure changes
            pressure_alert = self.analyze_pressure_changes(forecast_data)
            
            if pressure_alert:
                logger.warning(f"PRESSURE ALERT: {pressure_alert['pressure_drop']:.1f} mmHg drop expected!")
                
                # Send notifications to all enabled channels
                notification_results = self.send_notifications(pressure_alert)
                
                # Log results
                successful_channels = [name for name, success in notification_results.items() if success]
                failed_channels = [name for name, success in notification_results.items() if not success]
                
                if successful_channels:
                    logger.info(f"Notifications sent successfully via: {', '.join(successful_channels)}")
                
                if failed_channels:
                    logger.error(f"Failed to send notifications via: {', '.join(failed_channels)}")
                    
            else:
                logger.info("No pressure alert conditions met")
                
        except Exception as e:
            logger.error(f"Unexpected error in pressure monitoring: {e}")
            raise

def main():
    """Main entry point."""
    try:
        monitor = PressureMonitor()
        monitor.run()
    except Exception as e:
        logger.error(f"Failed to initialize pressure monitor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 