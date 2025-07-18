"""
Notification manager for cross-platform notification delivery.
"""

import logging
import json
import platform
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable
from dataclasses import asdict

from .notification_types import (
    Notification, NotificationType, NotificationPriority, NotificationChannel,
    NotificationStatus, NotificationPreferences, NotificationStats
)

logger = logging.getLogger(__name__)


class NotificationDeliveryChannel:
    """Base class for notification delivery channels."""
    
    def __init__(self, channel_type: NotificationChannel):
        self.channel_type = channel_type
        self.enabled = True
    
    def send_notification(self, notification: Notification) -> bool:
        """Send a notification through this channel."""
        raise NotImplementedError
    
    def is_available(self) -> bool:
        """Check if this channel is available on the current platform."""
        return True


class DesktopNotificationChannel(NotificationDeliveryChannel):
    """Desktop notification channel using system notifications."""
    
    def __init__(self):
        super().__init__(NotificationChannel.DESKTOP)
        self._setup_desktop_notifications()
    
    def _setup_desktop_notifications(self):
        """Set up desktop notification system."""
        try:
            # Try to import desktop notification libraries
            if platform.system() == "Windows":
                try:
                    import win10toast
                    self.toaster = win10toast.ToastNotifier()
                    self.notification_method = "win10toast"
                except ImportError:
                    logger.warning("win10toast not available, using fallback")
                    self.notification_method = "fallback"
            elif platform.system() == "Darwin":  # macOS
                try:
                    import pync
                    self.notification_method = "pync"
                except ImportError:
                    logger.warning("pync not available, using fallback")
                    self.notification_method = "fallback"
            elif platform.system() == "Linux":
                try:
                    import plyer
                    self.notification_method = "plyer"
                except ImportError:
                    logger.warning("plyer not available, using fallback")
                    self.notification_method = "fallback"
            else:
                self.notification_method = "fallback"
                
        except Exception as e:
            logger.warning(f"Failed to setup desktop notifications: {e}")
            self.notification_method = "fallback"
    
    def send_notification(self, notification: Notification) -> bool:
        """Send desktop notification."""
        try:
            if self.notification_method == "win10toast":
                self.toaster.show_toast(
                    title=notification.title,
                    msg=notification.message,
                    duration=10,
                    icon_path=notification.icon,
                    threaded=True
                )
                return True
            elif self.notification_method == "pync":
                import pync
                pync.notify(
                    notification.message,
                    title=notification.title,
                    sound="default" if notification.sound else None
                )
                return True
            elif self.notification_method == "plyer":
                from plyer import notification as plyer_notification
                plyer_notification.notify(
                    title=notification.title,
                    message=notification.message,
                    timeout=10
                )
                return True
            else:
                # Fallback: just log the notification
                logger.info(f"DESKTOP NOTIFICATION: {notification.title} - {notification.message}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to send desktop notification: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if desktop notifications are available."""
        return self.notification_method is not None


class InAppNotificationChannel(NotificationDeliveryChannel):
    """In-app notification channel for UI notifications."""
    
    def __init__(self):
        super().__init__(NotificationChannel.IN_APP)
        self.notification_queue: List[Notification] = []
        self.ui_callback: Optional[Callable] = None
    
    def set_ui_callback(self, callback: Callable[[Notification], None]):
        """Set callback for UI notifications."""
        self.ui_callback = callback
    
    def send_notification(self, notification: Notification) -> bool:
        """Send in-app notification."""
        try:
            if self.ui_callback:
                self.ui_callback(notification)
            else:
                # Queue for later delivery
                self.notification_queue.append(notification)
                logger.info(f"Queued in-app notification: {notification.title}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send in-app notification: {e}")
            return False
    
    def get_queued_notifications(self) -> List[Notification]:
        """Get queued notifications and clear the queue."""
        notifications = self.notification_queue.copy()
        self.notification_queue.clear()
        return notifications


class EmailNotificationChannel(NotificationDeliveryChannel):
    """Email notification channel."""
    
    def __init__(self, smtp_config: Dict[str, Any] = None):
        super().__init__(NotificationChannel.EMAIL)
        self.smtp_config = smtp_config or {}
    
    def send_notification(self, notification: Notification) -> bool:
        """Send email notification."""
        try:
            # This would integrate with an email service
            # For now, just log the notification
            logger.info(f"EMAIL NOTIFICATION: {notification.title} - {notification.message}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if email notifications are configured."""
        return bool(self.smtp_config.get("smtp_server"))


class WebhookNotificationChannel(NotificationDeliveryChannel):
    """Webhook notification channel for external integrations."""
    
    def __init__(self, webhook_url: str = None):
        super().__init__(NotificationChannel.WEBHOOK)
        self.webhook_url = webhook_url
    
    def send_notification(self, notification: Notification) -> bool:
        """Send webhook notification."""
        try:
            if not self.webhook_url:
                return False
            
            import requests
            
            payload = {
                "notification": asdict(notification),
                "timestamp": datetime.utcnow().isoformat(),
                "source": "aether_ai_companion"
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10,
                headers={"Content-Type": "application/json"}
            )
            
            response.raise_for_status()
            logger.info(f"Sent webhook notification: {notification.title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if webhook is configured."""
        return bool(self.webhook_url)


class NotificationManager:
    """Main notification manager for cross-platform delivery."""
    
    def __init__(self, preferences: NotificationPreferences = None):
        """Initialize the notification manager."""
        self.preferences = preferences or NotificationPreferences()
        self.channels: Dict[NotificationChannel, NotificationDeliveryChannel] = {}
        self.notification_history: List[Notification] = []
        self.stats = NotificationStats()
        
        # Setup delivery channels
        self._setup_channels()
        
        # Callbacks for notification events
        self.on_notification_sent: Optional[Callable] = None
        self.on_notification_failed: Optional[Callable] = None
    
    def _setup_channels(self):
        """Set up notification delivery channels."""
        # Desktop notifications
        if self.preferences.desktop_notifications:
            self.channels[NotificationChannel.DESKTOP] = DesktopNotificationChannel()
        
        # In-app notifications
        self.channels[NotificationChannel.IN_APP] = InAppNotificationChannel()
        
        # Email notifications
        if self.preferences.email_notifications:
            self.channels[NotificationChannel.EMAIL] = EmailNotificationChannel()
        
        # System tray (similar to desktop)
        self.channels[NotificationChannel.SYSTEM_TRAY] = DesktopNotificationChannel()
        
        logger.info(f"Initialized {len(self.channels)} notification channels")
    
    def add_channel(self, channel: NotificationDeliveryChannel):
        """Add a custom notification channel."""
        self.channels[channel.channel_type] = channel
        logger.info(f"Added notification channel: {channel.channel_type.value}")
    
    def send_notification(self, notification: Notification) -> bool:
        """Send a notification through appropriate channels."""
        # Check if notification should be sent based on preferences
        if not self.preferences.should_send_notification(notification):
            logger.debug(f"Notification filtered by preferences: {notification.title}")
            return False
        
        # Check if notification is expired
        if notification.is_expired():
            logger.debug(f"Notification expired: {notification.title}")
            return False
        
        # Check if it should be sent now
        if not notification.should_send_now():
            logger.debug(f"Notification not ready to send: {notification.title}")
            return False
        
        success = False
        failed_channels = []
        
        # Send through each requested channel
        for channel_type in notification.channels:
            if channel_type in self.channels:
                channel = self.channels[channel_type]
                
                if channel.enabled and channel.is_available():
                    try:
                        if channel.send_notification(notification):
                            success = True
                            self._update_stats_sent(channel_type)
                        else:
                            failed_channels.append(channel_type)
                    except Exception as e:
                        logger.error(f"Channel {channel_type.value} failed: {e}")
                        failed_channels.append(channel_type)
                else:
                    logger.warning(f"Channel {channel_type.value} not available")
                    failed_channels.append(channel_type)
            else:
                logger.warning(f"Channel {channel_type.value} not configured")
                failed_channels.append(channel_type)
        
        # Update notification status
        if success:
            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.utcnow()
            self.stats.total_sent += 1
            
            if self.on_notification_sent:
                self.on_notification_sent(notification)
        else:
            notification.status = NotificationStatus.FAILED
            self.stats.total_failed += 1
            
            if self.on_notification_failed:
                self.on_notification_failed(notification, failed_channels)
        
        # Add to history
        self.notification_history.append(notification)
        self._cleanup_old_notifications()
        
        return success
    
    def send_immediate_notification(
        self,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.SYSTEM_ALERT,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        channels: List[NotificationChannel] = None
    ) -> bool:
        """Send an immediate notification with simple parameters."""
        notification = Notification(
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            channels=channels or [NotificationChannel.DESKTOP, NotificationChannel.IN_APP]
        )
        
        return self.send_notification(notification)
    
    def schedule_notification(self, notification: Notification, send_time: datetime):
        """Schedule a notification to be sent at a specific time."""
        notification.scheduled_time = send_time
        
        # This would typically be handled by a scheduler or the reminder engine
        logger.info(f"Scheduled notification '{notification.title}' for {send_time}")
    
    def get_notification_history(self, hours: int = 24) -> List[Notification]:
        """Get notification history for the last N hours."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        return [
            notif for notif in self.notification_history
            if notif.created_at and notif.created_at >= cutoff_time
        ]
    
    def get_pending_notifications(self) -> List[Notification]:
        """Get notifications that are pending delivery."""
        return [
            notif for notif in self.notification_history
            if notif.status == NotificationStatus.PENDING
        ]
    
    def mark_notification_read(self, notification_id: str):
        """Mark a notification as read."""
        for notification in self.notification_history:
            if notification.id == notification_id:
                notification.status = NotificationStatus.READ
                notification.read_at = datetime.utcnow()
                self.stats.total_read += 1
                break
    
    def dismiss_notification(self, notification_id: str):
        """Dismiss a notification."""
        for notification in self.notification_history:
            if notification.id == notification_id:
                notification.status = NotificationStatus.DISMISSED
                self.stats.total_dismissed += 1
                break
    
    def _update_stats_sent(self, channel: NotificationChannel):
        """Update statistics for sent notifications."""
        if channel == NotificationChannel.DESKTOP:
            self.stats.desktop_sent += 1
        elif channel == NotificationChannel.MOBILE_PUSH:
            self.stats.mobile_sent += 1
        elif channel == NotificationChannel.EMAIL:
            self.stats.email_sent += 1
    
    def _cleanup_old_notifications(self):
        """Clean up old notifications from history."""
        # Keep only last 1000 notifications
        if len(self.notification_history) > 1000:
            self.notification_history = self.notification_history[-1000:]
        
        # Remove notifications older than 30 days
        cutoff_time = datetime.utcnow() - timedelta(days=30)
        self.notification_history = [
            notif for notif in self.notification_history
            if notif.created_at and notif.created_at >= cutoff_time
        ]
    
    def get_stats(self) -> NotificationStats:
        """Get notification statistics."""
        # Update time-based stats
        now = datetime.utcnow()
        
        self.stats.last_24_hours = len([
            notif for notif in self.notification_history
            if notif.sent_at and (now - notif.sent_at).total_seconds() < 86400
        ])
        
        self.stats.last_week = len([
            notif for notif in self.notification_history
            if notif.sent_at and (now - notif.sent_at).days < 7
        ])
        
        self.stats.last_month = len([
            notif for notif in self.notification_history
            if notif.sent_at and (now - notif.sent_at).days < 30
        ])
        
        return self.stats
    
    def test_channels(self) -> Dict[NotificationChannel, bool]:
        """Test all configured notification channels."""
        results = {}
        
        test_notification = Notification(
            title="Aether Test Notification",
            message="This is a test notification to verify channel functionality.",
            notification_type=NotificationType.SYSTEM_ALERT,
            priority=NotificationPriority.LOW
        )
        
        for channel_type, channel in self.channels.items():
            try:
                if channel.is_available():
                    success = channel.send_notification(test_notification)
                    results[channel_type] = success
                else:
                    results[channel_type] = False
            except Exception as e:
                logger.error(f"Test failed for channel {channel_type.value}: {e}")
                results[channel_type] = False
        
        return results
    
    def set_ui_callback(self, callback: Callable[[Notification], None]):
        """Set callback for in-app notifications."""
        if NotificationChannel.IN_APP in self.channels:
            in_app_channel = self.channels[NotificationChannel.IN_APP]
            if isinstance(in_app_channel, InAppNotificationChannel):
                in_app_channel.set_ui_callback(callback)
    
    def get_queued_in_app_notifications(self) -> List[Notification]:
        """Get queued in-app notifications."""
        if NotificationChannel.IN_APP in self.channels:
            in_app_channel = self.channels[NotificationChannel.IN_APP]
            if isinstance(in_app_channel, InAppNotificationChannel):
                return in_app_channel.get_queued_notifications()
        return []


# Global notification manager instance
_notification_manager = None


def get_notification_manager(preferences: NotificationPreferences = None) -> NotificationManager:
    """Get a singleton instance of the notification manager."""
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = NotificationManager(preferences)
    return _notification_manager