"""
Monday.com integration types and data structures.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union
from dataclasses import dataclass, field


class MondayItemStatus(Enum):
    """Status values for Monday.com items."""
    NOT_STARTED = "not_started"
    WORKING_ON_IT = "working_on_it"
    STUCK = "stuck"
    DONE = "done"
    CANCELLED = "cancelled"


class MondayPriority(Enum):
    """Priority levels for Monday.com items."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MondayColumnType(Enum):
    """Types of columns in Monday.com boards."""
    TEXT = "text"
    STATUS = "status"
    PERSON = "person"
    DATE = "date"
    TIMELINE = "timeline"
    NUMBERS = "numbers"
    RATING = "rating"
    DROPDOWN = "dropdown"
    CHECKBOX = "checkbox"
    EMAIL = "email"
    PHONE = "phone"
    LINK = "link"
    LONG_TEXT = "long_text"
    FILE = "file"


@dataclass
class MondayUser:
    """Represents a Monday.com user."""
    id: str
    name: str
    email: str
    photo_original: Optional[str] = None
    enabled: bool = True


@dataclass
class MondayColumn:
    """Represents a column in a Monday.com board."""
    id: str
    title: str
    type: MondayColumnType
    settings_str: Optional[str] = None
    
    @property
    def settings(self) -> Dict[str, Any]:
        """Parse column settings from JSON string."""
        if self.settings_str:
            import json
            try:
                return json.loads(self.settings_str)
            except json.JSONDecodeError:
                return {}
        return {}


@dataclass
class MondayColumnValue:
    """Represents a column value in a Monday.com item."""
    column_id: str
    value: Any
    text: Optional[str] = None
    
    def to_monday_format(self) -> Dict[str, Any]:
        """Convert to Monday.com API format."""
        if isinstance(self.value, str):
            return {"text": self.value}
        elif isinstance(self.value, bool):
            return {"checked": "true" if self.value else "false"}
        elif isinstance(self.value, (int, float)):
            return {"number": str(self.value)}
        elif isinstance(self.value, datetime):
            return {"date": self.value.strftime("%Y-%m-%d")}
        elif isinstance(self.value, dict):
            return self.value
        else:
            return {"text": str(self.value)}


@dataclass
class MondayItem:
    """Represents an item in a Monday.com board."""
    id: Optional[str] = None
    name: str = ""
    board_id: Optional[str] = None
    group_id: Optional[str] = None
    
    # Column values
    column_values: List[MondayColumnValue] = field(default_factory=list)
    
    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    creator_id: Optional[str] = None
    
    # Aether integration
    source_task_id: Optional[str] = None
    source_conversation_id: Optional[str] = None
    
    def __post_init__(self):
        """Initialize timestamps if not provided."""
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = self.created_at
    
    def get_column_value(self, column_id: str) -> Optional[MondayColumnValue]:
        """Get a specific column value."""
        for cv in self.column_values:
            if cv.column_id == column_id:
                return cv
        return None
    
    def set_column_value(self, column_id: str, value: Any, text: str = None):
        """Set a column value."""
        # Remove existing value for this column
        self.column_values = [cv for cv in self.column_values if cv.column_id != column_id]
        
        # Add new value
        column_value = MondayColumnValue(
            column_id=column_id,
            value=value,
            text=text
        )
        self.column_values.append(column_value)
    
    def get_status(self) -> Optional[str]:
        """Get the status column value."""
        status_value = self.get_column_value("status")
        if status_value and isinstance(status_value.value, dict):
            return status_value.value.get("label")
        return None
    
    def set_status(self, status: Union[str, MondayItemStatus]):
        """Set the status column value."""
        if isinstance(status, MondayItemStatus):
            status = status.value
        
        self.set_column_value("status", {"label": status})


@dataclass
class MondayGroup:
    """Represents a group in a Monday.com board."""
    id: str
    title: str
    color: Optional[str] = None
    position: Optional[str] = None


@dataclass
class MondayBoard:
    """Represents a Monday.com board."""
    id: Optional[str] = None
    name: str = ""
    description: Optional[str] = None
    
    # Structure
    columns: List[MondayColumn] = field(default_factory=list)
    groups: List[MondayGroup] = field(default_factory=list)
    items: List[MondayItem] = field(default_factory=list)
    
    # Permissions
    owners: List[MondayUser] = field(default_factory=list)
    subscribers: List[MondayUser] = field(default_factory=list)
    
    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialize timestamps if not provided."""
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = self.created_at
    
    def get_column_by_title(self, title: str) -> Optional[MondayColumn]:
        """Get a column by its title."""
        for column in self.columns:
            if column.title.lower() == title.lower():
                return column
        return None
    
    def get_group_by_title(self, title: str) -> Optional[MondayGroup]:
        """Get a group by its title."""
        for group in self.groups:
            if group.title.lower() == title.lower():
                return group
        return None


@dataclass
class MondayWorkspace:
    """Represents a Monday.com workspace."""
    id: str
    name: str
    kind: str = "open"
    description: Optional[str] = None
    
    # Boards in this workspace
    boards: List[MondayBoard] = field(default_factory=list)
    
    # Users with access
    users: List[MondayUser] = field(default_factory=list)


@dataclass
class MondayWebhook:
    """Represents a Monday.com webhook."""
    id: Optional[str] = None
    board_id: str = ""
    url: str = ""
    event: str = "create_item"  # create_item, change_column_value, etc.
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MondayAutomation:
    """Represents a Monday.com automation."""
    id: Optional[str] = None
    name: str = ""
    trigger: Dict[str, Any] = field(default_factory=dict)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    board_id: Optional[str] = None


@dataclass
class MondaySyncResult:
    """Result of Monday.com synchronization operation."""
    success: bool
    items_created: int = 0
    items_updated: int = 0
    items_deleted: int = 0
    boards_accessed: int = 0
    errors: List[str] = field(default_factory=list)
    sync_time: Optional[datetime] = None
    
    def __post_init__(self):
        if self.sync_time is None:
            self.sync_time = datetime.utcnow()


@dataclass
class MondayAuthConfig:
    """Configuration for Monday.com authentication."""
    api_token: str
    api_version: str = "2023-10"
    base_url: str = "https://api.monday.com/v2"
    
    # Webhook configuration
    webhook_secret: Optional[str] = None
    webhook_url: Optional[str] = None


@dataclass
class MondayPreferences:
    """User preferences for Monday.com integration."""
    default_board_id: Optional[str] = None
    default_group_id: Optional[str] = None
    
    # Task mapping preferences
    auto_create_items_from_tasks: bool = True
    sync_task_status: bool = True
    sync_task_assignees: bool = True
    sync_task_due_dates: bool = True
    
    # Column mapping
    status_column_id: str = "status"
    assignee_column_id: str = "person"
    due_date_column_id: str = "date"
    priority_column_id: str = "priority"
    
    # Sync settings
    sync_interval_minutes: int = 15
    enable_webhooks: bool = True
    
    # Notification preferences
    notify_on_status_change: bool = True
    notify_on_assignment: bool = True
    notify_on_due_date_change: bool = True


@dataclass
class MondayQuery:
    """Represents a GraphQL query for Monday.com API."""
    query: str
    variables: Dict[str, Any] = field(default_factory=dict)
    
    def to_request_body(self) -> Dict[str, Any]:
        """Convert to request body format."""
        body = {"query": self.query}
        if self.variables:
            body["variables"] = self.variables
        return body


# Common GraphQL queries
class MondayQueries:
    """Common GraphQL queries for Monday.com API."""
    
    @staticmethod
    def get_boards() -> MondayQuery:
        """Query to get all boards."""
        return MondayQuery(
            query="""
            query {
                boards {
                    id
                    name
                    description
                    columns {
                        id
                        title
                        type
                        settings_str
                    }
                    groups {
                        id
                        title
                        color
                    }
                    owners {
                        id
                        name
                        email
                    }
                }
            }
            """
        )
    
    @staticmethod
    def get_board_items(board_id: str) -> MondayQuery:
        """Query to get items from a specific board."""
        return MondayQuery(
            query="""
            query ($board_id: [Int!]) {
                boards (ids: $board_id) {
                    items {
                        id
                        name
                        group {
                            id
                            title
                        }
                        column_values {
                            id
                            text
                            value
                        }
                        created_at
                        updated_at
                        creator {
                            id
                            name
                            email
                        }
                    }
                }
            }
            """,
            variables={"board_id": [int(board_id)]}
        )
    
    @staticmethod
    def create_item(board_id: str, group_id: str, item_name: str, column_values: Dict[str, Any] = None) -> MondayQuery:
        """Query to create a new item."""
        variables = {
            "board_id": int(board_id),
            "group_id": group_id,
            "item_name": item_name
        }
        
        if column_values:
            variables["column_values"] = column_values
        
        return MondayQuery(
            query="""
            mutation ($board_id: Int!, $group_id: String!, $item_name: String!, $column_values: JSON) {
                create_item (
                    board_id: $board_id,
                    group_id: $group_id,
                    item_name: $item_name,
                    column_values: $column_values
                ) {
                    id
                    name
                    created_at
                }
            }
            """,
            variables=variables
        )
    
    @staticmethod
    def update_item(item_id: str, column_values: Dict[str, Any]) -> MondayQuery:
        """Query to update an item."""
        return MondayQuery(
            query="""
            mutation ($item_id: Int!, $column_values: JSON!) {
                change_multiple_column_values (
                    item_id: $item_id,
                    board_id: null,
                    column_values: $column_values
                ) {
                    id
                    name
                    updated_at
                }
            }
            """,
            variables={
                "item_id": int(item_id),
                "column_values": column_values
            }
        )
    
    @staticmethod
    def delete_item(item_id: str) -> MondayQuery:
        """Query to delete an item."""
        return MondayQuery(
            query="""
            mutation ($item_id: Int!) {
                delete_item (item_id: $item_id) {
                    id
                }
            }
            """,
            variables={"item_id": int(item_id)}
        )