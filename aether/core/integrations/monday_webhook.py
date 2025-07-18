"""
Monday.com webhook handler for real-time updates.
"""

import hashlib
import hmac
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from shared.utils.logging import get_logger
from core.database import get_database_manager
from .monday_types import MondayWebhook, MondayItem, MondayColumnValue

logger = get_logger(__name__)


class MondayWebhookHandler:
    """
    Handles webhooks from Monday.com for real-time synchronization.
    
    Processes events like:
    - Item creation
    - Status changes
    - Column value updates
    - Item assignments
    """
    
    def __init__(self, webhook_secret: Optional[str] = None):
        """Initialize webhook handler."""
        self.webhook_secret = webhook_secret
        self.db_manager = get_database_manager()
        
        # Event handlers mapping
        self.event_handlers = {
            "create_item": self._handle_item_created,
            "change_column_value": self._handle_column_changed,
            "change_status_column": self._handle_status_changed,
            "delete_item": self._handle_item_deleted,
            "create_update": self._handle_update_created,
            "edit_update": self._handle_update_edited
        }
        
        logger.info("Monday.com webhook handler initialized")
    
    def verify_webhook_signature(self, request: Request, payload: bytes) -> bool:
        """
        Verify webhook signature for security.
        
        Args:
            request: FastAPI request object
            payload: Raw request payload
        
        Returns:
            True if signature is valid
        """
        if not self.webhook_secret:
            logger.warning("No webhook secret configured, skipping signature verification")
            return True
        
        signature = request.headers.get("Authorization")
        if not signature:
            logger.error("No signature provided in webhook request")
            return False
        
        # Monday.com sends signature as "Bearer <signature>"
        if signature.startswith("Bearer "):
            signature = signature[7:]
        
        # Calculate expected signature
        expected_signature = hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures
        is_valid = hmac.compare_digest(signature, expected_signature)
        
        if not is_valid:
            logger.error("Invalid webhook signature")
        
        return is_valid
    
    async def process_webhook(self, request: Request) -> Dict[str, Any]:
        """
        Process incoming webhook from Monday.com.
        
        Args:
            request: FastAPI request object
        
        Returns:
            Processing result
        """
        try:
            # Get raw payload for signature verification
            payload = await request.body()
            
            # Verify signature
            if not self.verify_webhook_signature(request, payload):
                raise HTTPException(status_code=401, detail="Invalid webhook signature")
            
            # Parse JSON payload
            try:
                webhook_data = json.loads(payload.decode())
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in webhook payload: {e}")
                raise HTTPException(status_code=400, detail="Invalid JSON payload")
            
            # Extract event information
            event_type = webhook_data.get("type")
            if not event_type:
                logger.error("No event type in webhook payload")
                raise HTTPException(status_code=400, detail="Missing event type")
            
            # Process the event
            result = await self._process_event(event_type, webhook_data)
            
            logger.info(f"Successfully processed Monday.com webhook: {event_type}")
            return {
                "status": "success",
                "event_type": event_type,
                "processed_at": datetime.utcnow().isoformat(),
                "result": result
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error processing Monday.com webhook: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def _process_event(self, event_type: str, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a specific webhook event.
        
        Args:
            event_type: Type of event
            webhook_data: Webhook payload data
        
        Returns:
            Processing result
        """
        handler = self.event_handlers.get(event_type)
        if not handler:
            logger.warning(f"No handler for event type: {event_type}")
            return {"status": "ignored", "reason": "No handler available"}
        
        try:
            return await handler(webhook_data)
        except Exception as e:
            logger.error(f"Error handling {event_type} event: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _handle_item_created(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle item creation event."""
        try:
            # Extract item data
            item_data = webhook_data.get("event", {})
            board_id = str(item_data.get("boardId", ""))
            item_id = str(item_data.get("itemId", ""))
            item_name = item_data.get("itemName", "")
            
            logger.info(f"Monday.com item created: {item_name} (ID: {item_id}) in board {board_id}")
            
            # Store item information in local database
            async with self.db_manager.get_session() as db_session:
                await self._store_item_mapping(db_session, item_id, board_id, item_name)
            
            # Trigger any necessary Aether actions
            await self._trigger_item_created_actions(item_id, item_name, board_id)
            
            return {
                "status": "processed",
                "action": "item_created",
                "item_id": item_id,
                "item_name": item_name,
                "board_id": board_id
            }
            
        except Exception as e:
            logger.error(f"Error handling item creation: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _handle_column_changed(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle column value change event."""
        try:
            # Extract change data
            event_data = webhook_data.get("event", {})
            item_id = str(event_data.get("itemId", ""))
            board_id = str(event_data.get("boardId", ""))
            column_id = event_data.get("columnId", "")
            column_title = event_data.get("columnTitle", "")
            previous_value = event_data.get("previousValue", {})
            new_value = event_data.get("value", {})
            
            logger.info(f"Monday.com column changed: {column_title} in item {item_id}")
            
            # Process specific column types
            if column_id == "status":
                await self._handle_status_update(item_id, board_id, previous_value, new_value)
            elif column_id in ["person", "people"]:
                await self._handle_assignment_update(item_id, board_id, previous_value, new_value)
            elif column_id in ["date", "due_date"]:
                await self._handle_due_date_update(item_id, board_id, previous_value, new_value)
            elif column_id == "priority":
                await self._handle_priority_update(item_id, board_id, previous_value, new_value)
            
            # Update local database
            async with self.db_manager.get_session() as db_session:
                await self._update_item_column(db_session, item_id, column_id, new_value)
            
            return {
                "status": "processed",
                "action": "column_changed",
                "item_id": item_id,
                "column_id": column_id,
                "column_title": column_title,
                "previous_value": previous_value,
                "new_value": new_value
            }
            
        except Exception as e:
            logger.error(f"Error handling column change: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _handle_status_changed(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle status change event."""
        try:
            event_data = webhook_data.get("event", {})
            item_id = str(event_data.get("itemId", ""))
            board_id = str(event_data.get("boardId", ""))
            previous_status = event_data.get("previousValue", {}).get("label", "")
            new_status = event_data.get("value", {}).get("label", "")
            
            logger.info(f"Monday.com status changed: {previous_status} -> {new_status} for item {item_id}")
            
            # Update corresponding Aether task status
            await self._sync_status_to_aether_task(item_id, new_status)
            
            # Trigger notifications if needed
            if new_status.lower() in ["done", "completed"]:
                await self._trigger_completion_notification(item_id, board_id)
            elif new_status.lower() in ["stuck", "blocked"]:
                await self._trigger_blocked_notification(item_id, board_id)
            
            return {
                "status": "processed",
                "action": "status_changed",
                "item_id": item_id,
                "previous_status": previous_status,
                "new_status": new_status
            }
            
        except Exception as e:
            logger.error(f"Error handling status change: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _handle_item_deleted(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle item deletion event."""
        try:
            event_data = webhook_data.get("event", {})
            item_id = str(event_data.get("itemId", ""))
            board_id = str(event_data.get("boardId", ""))
            
            logger.info(f"Monday.com item deleted: {item_id} from board {board_id}")
            
            # Remove from local database
            async with self.db_manager.get_session() as db_session:
                await self._remove_item_mapping(db_session, item_id)
            
            # Update corresponding Aether task
            await self._handle_task_deletion(item_id)
            
            return {
                "status": "processed",
                "action": "item_deleted",
                "item_id": item_id,
                "board_id": board_id
            }
            
        except Exception as e:
            logger.error(f"Error handling item deletion: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _handle_update_created(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle update/comment creation event."""
        try:
            event_data = webhook_data.get("event", {})
            item_id = str(event_data.get("itemId", ""))
            update_id = str(event_data.get("updateId", ""))
            update_text = event_data.get("textBody", "")
            creator_id = str(event_data.get("creatorId", ""))
            
            logger.info(f"Monday.com update created on item {item_id}: {update_text[:50]}...")
            
            # Store update in local database
            async with self.db_manager.get_session() as db_session:
                await self._store_item_update(db_session, item_id, update_id, update_text, creator_id)
            
            # Process update for potential task extraction
            await self._process_update_for_tasks(item_id, update_text)
            
            return {
                "status": "processed",
                "action": "update_created",
                "item_id": item_id,
                "update_id": update_id,
                "creator_id": creator_id
            }
            
        except Exception as e:
            logger.error(f"Error handling update creation: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _handle_update_edited(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle update/comment edit event."""
        try:
            event_data = webhook_data.get("event", {})
            item_id = str(event_data.get("itemId", ""))
            update_id = str(event_data.get("updateId", ""))
            update_text = event_data.get("textBody", "")
            
            logger.info(f"Monday.com update edited on item {item_id}")
            
            # Update in local database
            async with self.db_manager.get_session() as db_session:
                await self._update_item_update(db_session, update_id, update_text)
            
            return {
                "status": "processed",
                "action": "update_edited",
                "item_id": item_id,
                "update_id": update_id
            }
            
        except Exception as e:
            logger.error(f"Error handling update edit: {e}")
            return {"status": "error", "error": str(e)}
    
    # Helper methods for database operations
    
    async def _store_item_mapping(self, db_session: AsyncSession, item_id: str, board_id: str, item_name: str):
        """Store Monday.com item mapping in database."""
        # This would store the mapping in your database
        # Implementation depends on your database schema
        logger.info(f"Storing Monday.com item mapping: {item_id} -> {item_name}")
    
    async def _update_item_column(self, db_session: AsyncSession, item_id: str, column_id: str, new_value: Any):
        """Update item column value in database."""
        logger.info(f"Updating item {item_id} column {column_id}")
    
    async def _remove_item_mapping(self, db_session: AsyncSession, item_id: str):
        """Remove item mapping from database."""
        logger.info(f"Removing Monday.com item mapping: {item_id}")
    
    async def _store_item_update(self, db_session: AsyncSession, item_id: str, update_id: str, update_text: str, creator_id: str):
        """Store item update in database."""
        logger.info(f"Storing update {update_id} for item {item_id}")
    
    async def _update_item_update(self, db_session: AsyncSession, update_id: str, update_text: str):
        """Update existing item update in database."""
        logger.info(f"Updating update {update_id}")
    
    # Helper methods for Aether integration
    
    async def _trigger_item_created_actions(self, item_id: str, item_name: str, board_id: str):
        """Trigger actions when a new item is created."""
        logger.info(f"Triggering actions for new item: {item_name}")
        # Could trigger notifications, create corresponding Aether tasks, etc.
    
    async def _handle_status_update(self, item_id: str, board_id: str, previous_value: Dict, new_value: Dict):
        """Handle status column updates."""
        logger.info(f"Processing status update for item {item_id}")
    
    async def _handle_assignment_update(self, item_id: str, board_id: str, previous_value: Dict, new_value: Dict):
        """Handle assignment column updates."""
        logger.info(f"Processing assignment update for item {item_id}")
    
    async def _handle_due_date_update(self, item_id: str, board_id: str, previous_value: Dict, new_value: Dict):
        """Handle due date column updates."""
        logger.info(f"Processing due date update for item {item_id}")
    
    async def _handle_priority_update(self, item_id: str, board_id: str, previous_value: Dict, new_value: Dict):
        """Handle priority column updates."""
        logger.info(f"Processing priority update for item {item_id}")
    
    async def _sync_status_to_aether_task(self, item_id: str, new_status: str):
        """Sync Monday.com status change to corresponding Aether task."""
        # Map Monday.com status to Aether task status
        status_mapping = {
            "not started": "todo",
            "working on it": "in_progress",
            "done": "completed",
            "stuck": "blocked",
            "cancelled": "cancelled"
        }
        
        aether_status = status_mapping.get(new_status.lower(), "todo")
        logger.info(f"Syncing status {new_status} -> {aether_status} for item {item_id}")
        
        # Update corresponding Aether task
        # Implementation would depend on your task management system
    
    async def _trigger_completion_notification(self, item_id: str, board_id: str):
        """Trigger notification when item is completed."""
        logger.info(f"Triggering completion notification for item {item_id}")
        # Could send notifications, update metrics, etc.
    
    async def _trigger_blocked_notification(self, item_id: str, board_id: str):
        """Trigger notification when item is blocked."""
        logger.info(f"Triggering blocked notification for item {item_id}")
        # Could send alerts, escalate to managers, etc.
    
    async def _handle_task_deletion(self, item_id: str):
        """Handle deletion of corresponding Aether task."""
        logger.info(f"Handling task deletion for Monday.com item {item_id}")
        # Update or archive corresponding Aether task
    
    async def _process_update_for_tasks(self, item_id: str, update_text: str):
        """Process item update for potential new task extraction."""
        logger.info(f"Processing update for task extraction: {update_text[:50]}...")
        # Could extract new tasks from update comments
        # Use task extractor to find actionable items in comments


# Global webhook handler instance
_webhook_handler: Optional[MondayWebhookHandler] = None


def get_monday_webhook_handler(webhook_secret: Optional[str] = None) -> MondayWebhookHandler:
    """
    Get global Monday.com webhook handler instance.
    
    Args:
        webhook_secret: Optional webhook secret for signature verification
    
    Returns:
        MondayWebhookHandler instance
    """
    global _webhook_handler
    if _webhook_handler is None:
        _webhook_handler = MondayWebhookHandler(webhook_secret)
    return _webhook_handler