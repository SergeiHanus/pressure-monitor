"""
IFTTT notification channel implementation.
"""

import requests
from typing import Dict, Any
from datetime import datetime
from .base_channel import BaseChannel
from config import Config

class IFTTTChannel(BaseChannel):
    """IFTTT webhook notification channel."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize IFTTT channel."""
        super().__init__(config)
        self.webhook_url = config.get('webhook_url')
    
    def validate_config(self) -> bool:
        """Validate IFTTT configuration."""
        if not self.webhook_url:
            logger.error("IFTTT webhook URL not configured")
            return False
        return True
    
    def format_message(self, pressure_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format pressure data for IFTTT webhook."""
        return {
            'value1': f"Pressure Alert: {pressure_data['pressure_drop']:.1f} mmHg drop expected",
            'value2': f"Current: {pressure_data['current_pressure']:.1f} mmHg, Min: {pressure_data['min_pressure']:.1f} mmHg",
            'value3': f"Expected at: {pressure_data['min_pressure_time'].strftime('%Y-%m-%d %H:%M')}"
        }
    
    def send_notification(self, pressure_data: Dict[str, Any]) -> bool:
        """Send notification via IFTTT webhook."""
        try:
            payload = self.format_message(pressure_data)
            timeout = self.config.get('timeout', Config.WEBHOOK_TIMEOUT)
            
            logger.info(f"Sending IFTTT notification...")
            response = requests.post(
                self.webhook_url, 
                json=payload, 
                timeout=timeout
            )
            response.raise_for_status()
            
            logger.info("IFTTT notification sent successfully")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send IFTTT notification: {e}")
            return False 