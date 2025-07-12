"""
Base notification channel class.

Defines the interface that all notification channels must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class BaseChannel(ABC):
    """Base class for all notification channels."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the channel with configuration."""
        self.config = config
        self.name = self.__class__.__name__
        logger.info(f"Initialized {self.name} channel")
    
    @abstractmethod
    def send_notification(self, pressure_data: Dict[str, Any]) -> bool:
        """
        Send notification with pressure alert data.
        
        Args:
            pressure_data: Dictionary containing pressure alert information
            
        Returns:
            bool: True if notification sent successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def format_message(self, pressure_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format pressure data into channel-specific message format.
        
        Args:
            pressure_data: Dictionary containing pressure alert information
            
        Returns:
            Dict[str, Any]: Formatted message for the channel
        """
        pass
    
    def validate_config(self) -> bool:
        """
        Validate channel configuration.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        return True
    
    def test_connection(self) -> bool:
        """
        Test channel connection/configuration.
        
        Returns:
            bool: True if connection test successful, False otherwise
        """
        try:
            logger.info(f"Testing {self.name} channel connection...")
            # Basic validation
            if not self.validate_config():
                logger.error(f"{self.name} configuration validation failed")
                return False
            
            logger.info(f"{self.name} channel connection test successful")
            return True
        except Exception as e:
            logger.error(f"{self.name} channel connection test failed: {e}")
            return False 