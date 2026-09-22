"""
Base Notification Provider Interface
Uniform contract for Email, Slack, Teams, and Google Chat integrations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class NotificationProvider(ABC):
    @abstractmethod
    def get_channel_name(self) -> str:
        """Returns channel identifier (e.g. 'slack', 'email')."""
        pass

    @abstractmethod
    def send(self, payload: Dict[str, Any], attachment_path: Optional[str] = None) -> bool:
        """Dispatches notification payload to the external service."""
        pass

    @abstractmethod
    def validate_configuration(self) -> bool:
        """Checks whether all necessary environment variables/secrets are present."""
        pass

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Tests connectivity without leaking secrets."""
        pass

