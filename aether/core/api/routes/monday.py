"""
Monday.com integration API routes.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_database_session
from core.integrations.monday_com import get_monday_integration
from core.integrations.monday_webhook import get_monday_webhook_handler
from core.integrations.monday_types import (
    MondayAuthConfig, MondayPreferences, MondayBoard, MondayItem,
    MondaySyncResult
)
from shared.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/monday", tags=["monday"])


@router.post("/webhook")
async def monday_webhook(request: Request):
    """
    Handle webhooks from Monday.com.
    
    This endpoint receives real-time updates from Monday.com when:
    - Items are created, updated, or deleted
    - Column values change
    - Status updates occur
    - Comments/updates are added
    """
    try:
        webhook_handler = get_monday_webhook_handler()
        result = await webhook_handler.process_webhook(request)
        
        logger.info(f"Processed Monday.com webhook: {result.get('event_type')}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing Monday.com webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process webhook"
        )


@router.get("/boards")
async def get_boards():
    """Get all accessible Monday.com boards."""
    try:
        monday_integration = get_monday_integration()
        boards = monday_integration.get_boards()
        
        return {
            "success": True,
            "boards": [
                {
                    "id": board.id,
                    "name": board.name,
                    "description": board.description,
                    "columns": len(board.columns),
                    "groups": len(board.groups),
                    "owners": len(board.owners)
                }
                for board in boards
            ],
            "count": len(boards)
        }
        
    except Exception as e:
        logger.error(f"Error getting Monday.com boards: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve boards"
        )


@router.get("/boards/{board_id}")
async def get_board(board_id: str):
    """Get details of a specific Monday.com board."""
    try:
        monday_integration = get_monday_integration()
        board = monday_integration.get_board(board_id)
        
        if not board:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Board {board_id} not found"
            )
        
        return {
            "success": True,
            "board": {
                "id": board.id,
                "name": board.name,
                "description": board.description,
                "columns": [
                    {
                        "id": col.id,
                        "title": col.title,
                        "type": col.type,
                        "settings": col.settings
                    }
                    for col in board.columns
                ],
                "groups": [
                    {
                        "id": group.id,
                        "title": group.title,
                        "color": group.color
                    }
                    for group in board.groups
                ],
                "owners": [
                    {
                        "id": owner.id,
                        "name": owner.name,
                        "email": owner.email
                    }
                    for owner in board.owners
                ]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Monday.com board {board_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve board"
        )


@router.get("/boards/{board_id}/items")
async def get_board_items(board_id: str):
    """Get all items from a specific Monday.com board."""
    try:
        monday_integration = get_monday_integration()
        items = monday_integration.get_board_items(board_id)
        
        return {
            "success": True,
            "items": [
                {
                    "id": item.id,
                    "name": item.name,
                    "group_id": item.group_id,
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                    "updated_at": item.updated_at.isoformat() if item.updated_at else None,
                    "column_values": [
                        {
                            "column_id": cv.column_id,
                            "value": cv.value,
                            "text": cv.text
                        }
                        for cv in item.column_values
                    ]
                }
                for item in items
            ],
            "count": len(items),
            "board_id": board_id
        }
        
    except Exception as e:
        logger.error(f"Error getting items from board {board_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve board items"
        )


@router.post("/boards/{board_id}/items")
async def create_item(
    board_id: str,
    item_data: Dict[str, Any]
):
    """Create a new item in a Monday.com board."""
    try:
        monday_integration = get_monday_integration()
        
        item_name = item_data.get("name", "")
        if not item_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Item name is required"
            )
        
        group_id = item_data.get("group_id")
        column_values = item_data.get("column_values", {})
        
        item_id = monday_integration.create_item(
            board_id=board_id,
            item_name=item_name,
            group_id=group_id,
            column_values=column_values
        )
        
        if not item_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create item"
            )
        
        return {
            "success": True,
            "item_id": item_id,
            "message": f"Item '{item_name}' created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating item in board {board_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create item"
        )


@router.put("/items/{item_id}")
async def update_item(
    item_id: str,
    update_data: Dict[str, Any]
):
    """Update an existing Monday.com item."""
    try:
        monday_integration = get_monday_integration()
        
        column_values = update_data.get("column_values", {})
        if not column_values:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Column values are required for update"
            )
        
        success = monday_integration.update_item(item_id, column_values)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update item"
            )
        
        return {
            "success": True,
            "item_id": item_id,
            "message": "Item updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating item {item_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update item"
        )


@router.delete("/items/{item_id}")
async def delete_item(item_id: str):
    """Delete a Monday.com item."""
    try:
        monday_integration = get_monday_integration()
        
        success = monday_integration.delete_item(item_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete item"
            )
        
        return {
            "success": True,
            "item_id": item_id,
            "message": "Item deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting item {item_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete item"
        )


@router.post("/sync/tasks")
async def sync_tasks_to_monday(
    sync_data: Dict[str, Any],
    db_session: AsyncSession = Depends(get_database_session)
):
    """Sync Aether tasks to Monday.com."""
    try:
        monday_integration = get_monday_integration()
        
        # This would typically get tasks from the database
        # For now, we'll use mock data or expect tasks in the request
        tasks = sync_data.get("tasks", [])
        
        if not tasks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No tasks provided for sync"
            )
        
        # Convert task data to task objects if needed
        # This depends on your task model structure
        
        sync_result = monday_integration.sync_with_tasks(tasks)
        
        return {
            "success": sync_result.success,
            "items_created": sync_result.items_created,
            "items_updated": sync_result.items_updated,
            "boards_accessed": sync_result.boards_accessed,
            "errors": sync_result.errors,
            "sync_time": sync_result.sync_time.isoformat() if sync_result.sync_time else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing tasks to Monday.com: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync tasks"
        )


@router.post("/items/{item_id}/progress")
async def track_progress(
    item_id: str,
    progress_data: Dict[str, Any]
):
    """Track progress on a Monday.com item."""
    try:
        monday_integration = get_monday_integration()
        
        progress_percentage = progress_data.get("progress", 0)
        notes = progress_data.get("notes", "")
        
        if not isinstance(progress_percentage, (int, float)) or progress_percentage < 0 or progress_percentage > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Progress must be a number between 0 and 100"
            )
        
        success = monday_integration.track_progress(item_id, progress_percentage, notes)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to track progress"
            )
        
        return {
            "success": True,
            "item_id": item_id,
            "progress": progress_percentage,
            "message": "Progress updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking progress for item {item_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to track progress"
        )


@router.post("/items/{item_id}/assign")
async def assign_item(
    item_id: str,
    assignment_data: Dict[str, Any]
):
    """Assign a Monday.com item to a user."""
    try:
        monday_integration = get_monday_integration()
        
        user_id = assignment_data.get("user_id", "")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID is required for assignment"
            )
        
        success = monday_integration.assign_item(item_id, user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to assign item"
            )
        
        return {
            "success": True,
            "item_id": item_id,
            "user_id": user_id,
            "message": "Item assigned successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning item {item_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign item"
        )


@router.post("/items/{item_id}/due-date")
async def set_due_date(
    item_id: str,
    date_data: Dict[str, Any]
):
    """Set due date for a Monday.com item."""
    try:
        monday_integration = get_monday_integration()
        
        due_date_str = date_data.get("due_date", "")
        if not due_date_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Due date is required"
            )
        
        try:
            due_date = datetime.fromisoformat(due_date_str.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid due date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
            )
        
        success = monday_integration.set_due_date(item_id, due_date)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to set due date"
            )
        
        return {
            "success": True,
            "item_id": item_id,
            "due_date": due_date.isoformat(),
            "message": "Due date set successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting due date for item {item_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set due date"
        )


@router.get("/status")
async def get_monday_status():
    """Get Monday.com integration status."""
    try:
        monday_integration = get_monday_integration()
        
        # Test connection by getting boards
        boards = monday_integration.get_boards()
        
        return {
            "success": True,
            "status": "connected",
            "mock_mode": monday_integration.mock_mode,
            "api_version": monday_integration.auth_config.api_version,
            "boards_accessible": len(boards),
            "last_checked": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error checking Monday.com status: {e}")
        return {
            "success": False,
            "status": "error",
            "error": str(e),
            "last_checked": datetime.utcnow().isoformat()
        }