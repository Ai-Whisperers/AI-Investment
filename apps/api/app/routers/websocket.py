"""
WebSocket router for real-time updates.
Implements latest WebSocket patterns with authentication and error handling.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException, status
from typing import Optional
import uuid
import logging
import asyncio
from datetime import datetime

from ..core.websocket_manager import manager, WSMessage
from ..core.security import decode_access_token
from ..core.database import get_db
from sqlalchemy.orm import Session
from ..models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_current_user_ws(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
) -> Optional[dict]:
    """
    Authenticate WebSocket connection using query parameter token.
    
    Args:
        websocket: The WebSocket connection
        token: JWT token passed as query parameter
        
    Returns:
        User data if authenticated, None for anonymous connections
    """
    if not token:
        # Allow anonymous connections with limited access
        return None
    
    try:
        payload = decode_access_token(token)
        return {"user_id": payload.get("sub"), "authenticated": True}
    except Exception as e:
        logger.warning(f"Invalid WebSocket token: {e}")
        # Still allow connection but as anonymous
        return None


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    client_id: Optional[str] = Query(None)
):
    """
    Main WebSocket endpoint for real-time updates.
    
    Query Parameters:
        token: Optional JWT token for authenticated connections
        client_id: Optional client identifier (generated if not provided)
    
    Message Format:
        Send: {"type": "subscribe", "room": "prices"}
        Receive: {"type": "prices", "action": "update", "data": {...}}
    """
    # Generate client ID if not provided
    if not client_id:
        client_id = str(uuid.uuid4())
    
    # Authenticate user if token provided
    user_data = await get_current_user_ws(websocket, token)
    
    # Prepare metadata
    metadata = {
        "connected_at": datetime.utcnow().isoformat(),
        "ip_address": websocket.client.host if websocket.client else "unknown",
        "authenticated": user_data is not None
    }
    
    if user_data:
        metadata.update(user_data)
    
    # Connect the client
    await manager.connect(websocket, client_id, metadata)
    
    # Auto-subscribe authenticated users to their portfolio updates
    if user_data and user_data.get("user_id"):
        await manager.subscribe_to_room(client_id, "portfolio")
    
    # Default subscriptions for all users
    await manager.subscribe_to_room(client_id, "system")
    
    try:
        # Keep connection alive and handle messages
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            # Process the message
            await manager.handle_client_message(client_id, data)
            
    except WebSocketDisconnect:
        # Client disconnected normally
        manager.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected normally")
        
    except Exception as e:
        # Unexpected error
        logger.error(f"WebSocket error for client {client_id}: {e}")
        manager.disconnect(client_id)
        
        # Try to send error message before closing
        try:
            error_msg = WSMessage(
                type="error",
                action="connection_error",
                data={"error": str(e)}
            )
            await websocket.send_text(error_msg.to_json())
        except:
            pass


@router.websocket("/ws/prices")
async def websocket_prices(
    websocket: WebSocket,
    symbols: Optional[str] = Query(None)
):
    """
    Dedicated WebSocket endpoint for price updates only.
    
    Query Parameters:
        symbols: Comma-separated list of symbols to subscribe to
    
    This endpoint auto-subscribes to price updates for specified symbols.
    """
    client_id = str(uuid.uuid4())
    
    metadata = {
        "endpoint": "prices",
        "symbols": symbols.split(",") if symbols else [],
        "connected_at": datetime.utcnow().isoformat()
    }
    
    await manager.connect(websocket, client_id, metadata)
    await manager.subscribe_to_room(client_id, "prices")
    
    try:
        # Send initial price snapshot if symbols specified
        if symbols:
            # TODO: Fetch current prices for symbols and send
            initial_msg = WSMessage(
                type="prices",
                action="snapshot",
                data={
                    "symbols": metadata["symbols"],
                    "message": "Price feed connected"
                }
            )
            await manager.send_personal_message(initial_msg, client_id)
        
        # Keep connection alive
        while True:
            # Just maintain connection, prices will be broadcast automatically
            data = await websocket.receive_text()
            
            # Handle ping/pong for keepalive
            if data == "ping":
                await websocket.send_text("pong")
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info(f"Price feed client {client_id} disconnected")
    except Exception as e:
        logger.error(f"Price feed error for {client_id}: {e}")
        manager.disconnect(client_id)


@router.websocket("/ws/signals")
async def websocket_signals(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    min_confidence: float = Query(0.7)
):
    """
    Dedicated WebSocket endpoint for signal alerts.
    
    Query Parameters:
        token: Optional JWT token for authenticated features
        min_confidence: Minimum confidence threshold for signals (0.0-1.0)
    
    Authenticated users get personalized signals based on their portfolio.
    """
    client_id = str(uuid.uuid4())
    user_data = await get_current_user_ws(websocket, token)
    
    metadata = {
        "endpoint": "signals",
        "min_confidence": min_confidence,
        "authenticated": user_data is not None,
        "connected_at": datetime.utcnow().isoformat()
    }
    
    if user_data:
        metadata.update(user_data)
    
    await manager.connect(websocket, client_id, metadata)
    await manager.subscribe_to_room(client_id, "signals")
    
    try:
        # Send welcome message with settings
        welcome_msg = WSMessage(
            type="signals",
            action="connected",
            data={
                "min_confidence": min_confidence,
                "authenticated": metadata["authenticated"],
                "message": "Signal feed connected. High-confidence signals will be delivered in real-time."
            }
        )
        await manager.send_personal_message(welcome_msg, client_id)
        
        # Keep connection alive
        while True:
            data = await websocket.receive_text()
            
            # Allow updating confidence threshold
            if data.startswith("confidence:"):
                try:
                    new_confidence = float(data.split(":")[1])
                    if 0.0 <= new_confidence <= 1.0:
                        metadata["min_confidence"] = new_confidence
                        manager.client_metadata[client_id] = metadata
                        
                        confirm_msg = WSMessage(
                            type="signals",
                            action="settings_updated",
                            data={"min_confidence": new_confidence}
                        )
                        await manager.send_personal_message(confirm_msg, client_id)
                except:
                    pass
                    
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info(f"Signal feed client {client_id} disconnected")
    except Exception as e:
        logger.error(f"Signal feed error for {client_id}: {e}")
        manager.disconnect(client_id)


@router.get("/ws/stats")
async def get_websocket_stats():
    """
    Get WebSocket connection statistics.
    
    Returns:
        Current statistics about WebSocket connections
    """
    stats = manager.get_stats()
    health = await manager.health_check()
    
    return {
        "stats": stats,
        "health": health,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/ws/broadcast/system")
async def broadcast_system_message(
    message: str,
    severity: str = "info"
):
    """
    Broadcast a system message to all connected clients.
    Admin endpoint for system announcements.
    
    Args:
        message: The message to broadcast
        severity: Message severity (info, warning, error, success)
    """
    # TODO: Add admin authentication
    
    from ..core.websocket_manager import broadcast_system_message as broadcast
    await broadcast(message, severity)
    
    return {
        "status": "broadcasted",
        "message": message,
        "severity": severity,
        "recipients": len(manager.active_connections)
    }


# Background task to periodically clean up stale connections
async def cleanup_stale_connections():
    """Periodic task to clean up stale WebSocket connections."""
    while True:
        await asyncio.sleep(60)  # Run every minute
        try:
            health = await manager.health_check()
            if health["removed_connections"] > 0:
                logger.info(f"Cleaned up {health['removed_connections']} stale connections")
        except Exception as e:
            logger.error(f"Error in connection cleanup: {e}")