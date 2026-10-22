"""
Customer notification provider ports and adapters (ADR-0004).

Dispatches transactional SMS, WhatsApp, and push updates for booking events:
booking confirmation, professional assignment, live dispatch ETA, arrival, and start OTP.
"""

from __future__ import annotations

import logging
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger("glamnow.notifications")


@runtime_checkable
class NotificationPort(Protocol):
    """Port interface for sending transactional notifications."""

    async def send_notification(
        self,
        recipient_phone: str,
        message: str,
        event_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> bool: ...


class MockNotificationAdapter:
    """
    In-memory notification recorder for testing and local development.
    """

    def __init__(self) -> None:
        self.sent_notifications: list[dict[str, Any]] = []

    async def send_notification(
        self,
        recipient_phone: str,
        message: str,
        event_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        record = {
            "recipient_phone": recipient_phone,
            "message": message,
            "event_type": event_type,
            "metadata": metadata or {},
        }
        self.sent_notifications.append(record)
        logger.info(
            "Notification [%s] sent to %s: %s",
            event_type,
            recipient_phone,
            message,
        )
        return True


_notification_service_instance: NotificationPort | None = None


def get_notification_service() -> NotificationPort:
    """Dependency injection factory for notification service."""
    global _notification_service_instance
    if _notification_service_instance is None:
        _notification_service_instance = MockNotificationAdapter()
    return _notification_service_instance


def set_notification_service(service: NotificationPort) -> None:
    """Override notification service for tests."""
    global _notification_service_instance
    _notification_service_instance = service
