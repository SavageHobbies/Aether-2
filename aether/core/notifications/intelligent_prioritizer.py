"""
Intelligent notification prioritizer that learns from user patterns.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import json
import os

from .notification_types import (
    Notification, NotificationType, NotificationPriority, NotificationChannel
)

logger = logging.getLogger(__name__)


@dataclass
class UserInteractionPattern:
    """Tracks user interaction patterns with notifications."""
    notification_type: NotificationType
    priority: NotificationPriority
    time_of_day: int  # Hour of day (0-23)
    day_of_week: int  # 0=Monday, 6=Sunday
    
    # Interaction metrics
    response_time_seconds: float = 0.0
    action_taken: Optional[str] = None  # "read", "dismissed", "acted", "ignored"
    engagement_score: float = 0.0  # 0-1 scale
    
    # Context
    tags: List[str] = field(default_factory=list)
    source_type: Optional[str] = None  # "task", "calendar", "conversation"


@dataclass
class PriorityScore:
    """Represents a calculated priority score for a notification."""
    base_priority: NotificationPriority
    adjusted_priority: NotificationPriority
    confidence: float  # 0-1 scale
    
    # Factors that influenced the score
    time_factor: float = 0.0
    pattern_factor: float = 0.0
    urgency_factor: float = 0.0
    context_factor: float = 0.0
    
    # Explanation for debugging
    explanation: str = ""


class IntelligentNotificationPrioritizer:
    """Learns from user patterns to intelligently prioritize notifications."""
    
    def __init__(self, data_file: str = None):
        """Initialize the prioritizer."""
        self.data_file = data_file or os.path.join(os.path.expanduser("~"), ".aether", "notification_patterns.json")
        self.interaction_history: List[UserInteractionPattern] = []
        self.priority_adjustments: Dict[str, float] = {}
        self.time_preferences: Dict[int, float] = {}  # Hour -> preference score
        self.type_preferences: Dict[NotificationType, float] = {}
        
        # Learning parameters
        self.learning_rate = 0.1
        self.min_interactions_for_learning = 10
        self.pattern_decay_days = 30
        
        # Load existing patterns
        self._load_patterns()
    
    def record_interaction(self, notification: Notification, action: str, response_time_seconds: float = 0.0):
        """Record a user interaction with a notification."""
        now = datetime.now()
        
        # Calculate engagement score based on action and response time
        engagement_score = self._calculate_engagement_score(action, response_time_seconds)
        
        pattern = UserInteractionPattern(
            notification_type=notification.notification_type,
            priority=notification.priority,
            time_of_day=now.hour,
            day_of_week=now.weekday(),
            response_time_seconds=response_time_seconds,
            action_taken=action,
            engagement_score=engagement_score,
            tags=notification.tags.copy(),
            source_type=self._determine_source_type(notification)
        )
        
        self.interaction_history.append(pattern)
        self._update_learned_patterns()
        self._save_patterns()
        
        logger.info(f"Recorded interaction: {action} for {notification.notification_type.value} (engagement: {engagement_score:.2f})")
    
    def calculate_priority_score(self, notification: Notification) -> PriorityScore:
        """Calculate an intelligent priority score for a notification."""
        base_priority = notification.priority
        now = datetime.now()
        
        # Initialize factors
        time_factor = self._calculate_time_factor(now.hour, now.weekday())
        pattern_factor = self._calculate_pattern_factor(notification)
        urgency_factor = self._calculate_urgency_factor(notification)
        context_factor = self._calculate_context_factor(notification)
        
        # Combine factors with weights
        weights = {
            'time': 0.2,
            'pattern': 0.3,
            'urgency': 0.3,
            'context': 0.2
        }
        
        combined_score = (
            time_factor * weights['time'] +
            pattern_factor * weights['pattern'] +
            urgency_factor * weights['urgency'] +
            context_factor * weights['context']
        )
        
        # Adjust base priority
        priority_levels = {
            NotificationPriority.LOW: 1,
            NotificationPriority.MEDIUM: 2,
            NotificationPriority.HIGH: 3,
            NotificationPriority.URGENT: 4,
            NotificationPriority.CRITICAL: 5
        }
        
        base_level = priority_levels.get(base_priority, 2)
        adjusted_level = max(1, min(5, base_level + int(combined_score * 2 - 1)))  # Adjust by -1 to +1 levels
        
        level_to_priority = {v: k for k, v in priority_levels.items()}
        adjusted_priority = level_to_priority.get(adjusted_level, base_priority)
        
        # Calculate confidence based on amount of historical data
        confidence = min(1.0, len(self.interaction_history) / 100.0)
        
        # Generate explanation
        explanation = self._generate_explanation(
            base_priority, adjusted_priority, time_factor, pattern_factor, urgency_factor, context_factor
        )
        
        return PriorityScore(
            base_priority=base_priority,
            adjusted_priority=adjusted_priority,
            confidence=confidence,
            time_factor=time_factor,
            pattern_factor=pattern_factor,
            urgency_factor=urgency_factor,
            context_factor=context_factor,
            explanation=explanation
        )
    
    def get_optimal_delivery_time(self, notification: Notification, within_hours: int = 24) -> datetime:
        """Suggest the optimal time to deliver a notification within a time window."""
        now = datetime.now()
        end_time = now + timedelta(hours=within_hours)
        
        best_time = now
        best_score = 0.0
        
        # Check each hour within the window
        current_time = now
        while current_time <= end_time:
            time_score = self._calculate_time_factor(current_time.hour, current_time.weekday())
            
            if time_score > best_score:
                best_score = time_score
                best_time = current_time
            
            current_time += timedelta(hours=1)
        
        return best_time
    
    def should_suppress_notification(self, notification: Notification) -> Tuple[bool, str]:
        """Determine if a notification should be suppressed based on learned patterns."""
        priority_score = self.calculate_priority_score(notification)
        
        # Suppress if adjusted priority is very low and confidence is high
        if (priority_score.adjusted_priority == NotificationPriority.LOW and 
            priority_score.confidence > 0.7 and
            priority_score.pattern_factor < 0.3):
            return True, "Low engagement pattern detected"
        
        # Suppress if user typically ignores this type at this time
        now = datetime.now()
        similar_patterns = self._get_similar_patterns(notification, now.hour, now.weekday())
        
        if len(similar_patterns) >= 5:
            ignore_rate = sum(1 for p in similar_patterns if p.action_taken == "ignored") / len(similar_patterns)
            if ignore_rate > 0.8:
                return True, f"High ignore rate ({ignore_rate:.1%}) for similar notifications"
        
        return False, ""
    
    def get_preferred_channels(self, notification: Notification) -> List[NotificationChannel]:
        """Get preferred delivery channels based on learned patterns."""
        # This would analyze which channels the user engages with most for different types
        # For now, return the original channels with some intelligent defaults
        
        priority_score = self.calculate_priority_score(notification)
        
        if priority_score.adjusted_priority in [NotificationPriority.URGENT, NotificationPriority.CRITICAL]:
            # High priority notifications should use multiple channels
            return [NotificationChannel.DESKTOP, NotificationChannel.MOBILE_PUSH, NotificationChannel.IN_APP]
        elif priority_score.adjusted_priority == NotificationPriority.HIGH:
            return [NotificationChannel.DESKTOP, NotificationChannel.IN_APP]
        else:
            return [NotificationChannel.IN_APP]
    
    def _calculate_engagement_score(self, action: str, response_time_seconds: float) -> float:
        """Calculate engagement score based on user action and response time."""
        action_scores = {
            "acted": 1.0,      # User took action (clicked, completed task, etc.)
            "read": 0.7,       # User read the notification
            "dismissed": 0.3,  # User dismissed without action
            "ignored": 0.0     # User ignored completely
        }
        
        base_score = action_scores.get(action, 0.0)
        
        # Adjust based on response time (faster response = higher engagement)
        if response_time_seconds > 0:
            # Normalize response time (faster = better, up to a point)
            if response_time_seconds < 60:  # Very fast response
                time_bonus = 0.2
            elif response_time_seconds < 300:  # Within 5 minutes
                time_bonus = 0.1
            elif response_time_seconds < 3600:  # Within 1 hour
                time_bonus = 0.0
            else:  # Slow response
                time_bonus = -0.1
            
            base_score = max(0.0, min(1.0, base_score + time_bonus))
        
        return base_score
    
    def _calculate_time_factor(self, hour: int, day_of_week: int) -> float:
        """Calculate time-based factor for notification priority."""
        # Use learned time preferences or defaults
        hour_preference = self.time_preferences.get(hour, 0.5)
        
        # Weekend vs weekday preference
        is_weekend = day_of_week >= 5
        weekend_factor = 0.8 if is_weekend else 1.0  # Slightly lower priority on weekends
        
        return hour_preference * weekend_factor
    
    def _calculate_pattern_factor(self, notification: Notification) -> float:
        """Calculate pattern-based factor from historical interactions."""
        similar_patterns = self._get_similar_patterns(
            notification, 
            datetime.now().hour, 
            datetime.now().weekday()
        )
        
        if not similar_patterns:
            return 0.5  # Neutral if no patterns
        
        # Calculate average engagement for similar notifications
        avg_engagement = sum(p.engagement_score for p in similar_patterns) / len(similar_patterns)
        return avg_engagement
    
    def _calculate_urgency_factor(self, notification: Notification) -> float:
        """Calculate urgency factor based on notification content and timing."""
        urgency_keywords = {
            "urgent": 0.9,
            "asap": 0.9,
            "immediately": 0.9,
            "deadline": 0.8,
            "overdue": 1.0,
            "critical": 0.9,
            "important": 0.7,
            "reminder": 0.6
        }
        
        content = (notification.title + " " + notification.message).lower()
        max_urgency = 0.0
        
        for keyword, urgency in urgency_keywords.items():
            if keyword in content:
                max_urgency = max(max_urgency, urgency)
        
        # Also consider notification type
        type_urgency = {
            NotificationType.TASK_OVERDUE: 1.0,
            NotificationType.DEADLINE_WARNING: 0.9,
            NotificationType.MEETING_REMINDER: 0.8,
            NotificationType.CALENDAR_CONFLICT: 0.8,
            NotificationType.TASK_REMINDER: 0.6,
            NotificationType.SYSTEM_ALERT: 0.4,
            NotificationType.IDEA_SUGGESTION: 0.3
        }.get(notification.notification_type, 0.5)
        
        return max(max_urgency, type_urgency)
    
    def _calculate_context_factor(self, notification: Notification) -> float:
        """Calculate context-based factor (tags, source, etc.)."""
        context_score = 0.5  # Base score
        
        # High-value tags increase priority
        high_value_tags = {"deadline", "meeting", "client", "urgent", "critical", "project"}
        tag_matches = len(set(notification.tags) & high_value_tags)
        context_score += tag_matches * 0.1
        
        # Source-based adjustments
        if notification.source_task_id:
            context_score += 0.1  # Tasks are generally important
        if notification.source_event_id:
            context_score += 0.15  # Calendar events are time-sensitive
        
        return min(1.0, context_score)
    
    def _get_similar_patterns(self, notification: Notification, hour: int, day_of_week: int) -> List[UserInteractionPattern]:
        """Get historical patterns similar to the current notification."""
        similar = []
        
        for pattern in self.interaction_history:
            # Check similarity criteria
            type_match = pattern.notification_type == notification.notification_type
            time_match = abs(pattern.time_of_day - hour) <= 2  # Within 2 hours
            day_match = pattern.day_of_week == day_of_week
            tag_overlap = len(set(pattern.tags) & set(notification.tags)) > 0
            
            # Score similarity
            similarity_score = 0
            if type_match:
                similarity_score += 3
            if time_match:
                similarity_score += 2
            if day_match:
                similarity_score += 1
            if tag_overlap:
                similarity_score += 1
            
            # Include if similarity is high enough
            if similarity_score >= 4:
                similar.append(pattern)
        
        return similar
    
    def _determine_source_type(self, notification: Notification) -> Optional[str]:
        """Determine the source type of a notification."""
        if notification.source_task_id:
            return "task"
        elif notification.source_event_id:
            return "calendar"
        elif notification.source_conversation_id:
            return "conversation"
        else:
            return "system"
    
    def _update_learned_patterns(self):
        """Update learned patterns based on interaction history."""
        if len(self.interaction_history) < self.min_interactions_for_learning:
            return
        
        # Update time preferences
        time_engagement = defaultdict(list)
        for pattern in self.interaction_history:
            time_engagement[pattern.time_of_day].append(pattern.engagement_score)
        
        for hour, scores in time_engagement.items():
            self.time_preferences[hour] = sum(scores) / len(scores)
        
        # Update type preferences
        type_engagement = defaultdict(list)
        for pattern in self.interaction_history:
            type_engagement[pattern.notification_type].append(pattern.engagement_score)
        
        for notif_type, scores in type_engagement.items():
            self.type_preferences[notif_type] = sum(scores) / len(scores)
        
        logger.info(f"Updated learned patterns from {len(self.interaction_history)} interactions")
    
    def _generate_explanation(self, base_priority, adjusted_priority, time_factor, pattern_factor, urgency_factor, context_factor) -> str:
        """Generate human-readable explanation for priority adjustment."""
        explanations = []
        
        if adjusted_priority != base_priority:
            direction = "increased" if adjusted_priority.value > base_priority.value else "decreased"
            explanations.append(f"Priority {direction} from {base_priority.value} to {adjusted_priority.value}")
        
        if time_factor > 0.7:
            explanations.append("Good time for user engagement")
        elif time_factor < 0.3:
            explanations.append("Suboptimal time for user engagement")
        
        if pattern_factor > 0.7:
            explanations.append("User typically engages well with similar notifications")
        elif pattern_factor < 0.3:
            explanations.append("User typically ignores similar notifications")
        
        if urgency_factor > 0.8:
            explanations.append("High urgency content detected")
        
        if context_factor > 0.7:
            explanations.append("Important contextual tags present")
        
        return "; ".join(explanations) if explanations else "No significant adjustments"
    
    def _load_patterns(self):
        """Load interaction patterns from file."""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                
                # Load interaction history
                for pattern_data in data.get('interactions', []):
                    pattern = UserInteractionPattern(**pattern_data)
                    self.interaction_history.append(pattern)
                
                # Load learned preferences
                self.time_preferences = data.get('time_preferences', {})
                self.time_preferences = {int(k): v for k, v in self.time_preferences.items()}
                
                type_prefs = data.get('type_preferences', {})
                self.type_preferences = {
                    NotificationType(k): v for k, v in type_prefs.items()
                }
                
                logger.info(f"Loaded {len(self.interaction_history)} interaction patterns")
        
        except Exception as e:
            logger.warning(f"Failed to load patterns: {e}")
    
    def _save_patterns(self):
        """Save interaction patterns to file."""
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            
            # Limit history size to prevent file from growing too large
            max_history = 1000
            if len(self.interaction_history) > max_history:
                self.interaction_history = self.interaction_history[-max_history:]
            
            # Prepare data for serialization
            interactions_data = []
            for pattern in self.interaction_history:
                pattern_dict = {
                    'notification_type': pattern.notification_type.value,
                    'priority': pattern.priority.value,
                    'time_of_day': pattern.time_of_day,
                    'day_of_week': pattern.day_of_week,
                    'response_time_seconds': pattern.response_time_seconds,
                    'action_taken': pattern.action_taken,
                    'engagement_score': pattern.engagement_score,
                    'tags': pattern.tags,
                    'source_type': pattern.source_type
                }
                interactions_data.append(pattern_dict)
            
            data = {
                'interactions': interactions_data,
                'time_preferences': self.time_preferences,
                'type_preferences': {k.value: v for k, v in self.type_preferences.items()},
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Saved patterns to {self.data_file}")
        
        except Exception as e:
            logger.error(f"Failed to save patterns: {e}")
    
    def get_learning_stats(self) -> Dict[str, any]:
        """Get statistics about the learning system."""
        return {
            'total_interactions': len(self.interaction_history),
            'learned_time_preferences': len(self.time_preferences),
            'learned_type_preferences': len(self.type_preferences),
            'learning_active': len(self.interaction_history) >= self.min_interactions_for_learning,
            'confidence_level': min(1.0, len(self.interaction_history) / 100.0),
            'data_file': self.data_file
        }


# Global prioritizer instance
_prioritizer = None


def get_intelligent_prioritizer(data_file: str = None) -> IntelligentNotificationPrioritizer:
    """Get a singleton instance of the intelligent prioritizer."""
    global _prioritizer
    if _prioritizer is None:
        _prioritizer = IntelligentNotificationPrioritizer(data_file)
    return _prioritizer