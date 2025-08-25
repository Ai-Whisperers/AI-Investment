"""
WebSocket connection manager for real-time updates.
Implements the latest WebSocket patterns with FastAPI.
"""

import json
from typing import Dict, List, Set
from dataclasses import dataclass, asdict
from datetime import datetime
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
import logging

logger = logging.getLogger(__name__)


@dataclass
class WSMessage:
    """WebSocket message structure."""
    type: str  # 'price', 'signal', 'news', 'portfolio', 'system'
    action: str  # 'update', 'create', 'delete', 'alert'
    data: dict
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_json(self) -> str:
        """Convert message to JSON string."""
        msg_dict = asdict(self)
        msg_dict['timestamp'] = self.timestamp.isoformat()
        return json.dumps(msg_dict)


class ConnectionManager:
    """
    Manages WebSocket connections with room-based subscriptions.
    Implements connection pooling and message broadcasting.
    """
    
    def __init__(self):
        # Active connections by client ID
        self.active_connections: Dict[str, WebSocket] = {}
        
        # Room subscriptions (room -> set of client IDs)
        self.rooms: Dict[str, Set[str]] = {
            "prices": set(),
            "signals": set(),
            "news": set(),
            "portfolio": set(),
            "system": set(),
        }
        
        # Client metadata
        self.client_metadata: Dict[str, dict] = {}
        
        # Message queue for buffering
        self.message_queue: Dict[str, List[WSMessage]] = {}
        
        # Stats
        self.stats = {
            "total_connections": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "errors": 0
        }
    
    async def connect(self, websocket: WebSocket, client_id: str, metadata: dict = None) -> None:
        """
        Accept a new WebSocket connection.
        
        Args:
            websocket: The WebSocket connection
            client_id: Unique client identifier
            metadata: Optional client metadata (user info, preferences)
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.client_metadata[client_id] = metadata or {}
        self.message_queue[client_id] = []
        self.stats["total_connections"] += 1
        
        # Send welcome message
        welcome_msg = WSMessage(
            type="system",
            action="connected",
            data={
                "client_id": client_id,
                "available_rooms": list(self.rooms.keys()),
                "server_time": datetime.utcnow().isoformat()
            }
        )
        await self.send_personal_message(welcome_msg, client_id)
        
        logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, client_id: str) -> None:
        """
        Remove a client connection and clean up subscriptions.
        
        Args:
            client_id: The client to disconnect
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            
            # Remove from all rooms
            for room in self.rooms.values():
                room.discard(client_id)
            
            # Clean up metadata and queue
            self.client_metadata.pop(client_id, None)
            self.message_queue.pop(client_id, None)
            
            logger.info(f"Client {client_id} disconnected. Remaining connections: {len(self.active_connections)}")
    
    async def subscribe_to_room(self, client_id: str, room: str) -> bool:
        """
        Subscribe a client to a specific room for updates.
        
        Args:
            client_id: The client ID
            room: The room name to subscribe to
            
        Returns:
            True if subscription successful, False otherwise
        """
        if room not in self.rooms:
            logger.warning(f"Room {room} does not exist")
            return False
        
        if client_id not in self.active_connections:
            logger.warning(f"Client {client_id} not connected")
            return False
        
        self.rooms[room].add(client_id)
        
        # Send confirmation
        confirm_msg = WSMessage(
            type="system",
            action="subscribed",
            data={"room": room, "subscribers": len(self.rooms[room])}
        )
        await self.send_personal_message(confirm_msg, client_id)
        
        logger.info(f"Client {client_id} subscribed to room {room}")
        return True
    
    async def unsubscribe_from_room(self, client_id: str, room: str) -> bool:
        """
        Unsubscribe a client from a room.
        
        Args:
            client_id: The client ID
            room: The room to unsubscribe from
            
        Returns:
            True if unsubscription successful, False otherwise
        """
        if room in self.rooms:
            self.rooms[room].discard(client_id)
            
            # Send confirmation
            confirm_msg = WSMessage(
                type="system",
                action="unsubscribed",
                data={"room": room}
            )
            await self.send_personal_message(confirm_msg, client_id)
            
            logger.info(f"Client {client_id} unsubscribed from room {room}")
            return True
        return False
    
    async def send_personal_message(self, message: WSMessage, client_id: str) -> bool:
        """
        Send a message to a specific client.
        
        Args:
            message: The message to send
            client_id: The target client
            
        Returns:
            True if sent successfully, False otherwise
        """
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_text(message.to_json())
                self.stats["messages_sent"] += 1
                return True
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                self.stats["errors"] += 1
                self.disconnect(client_id)
                return False
        return False
    
    async def broadcast_to_room(self, message: WSMessage, room: str) -> int:
        """
        Broadcast a message to all clients in a room.
        
        Args:
            message: The message to broadcast
            room: The target room
            
        Returns:
            Number of clients the message was sent to
        """
        if room not in self.rooms:
            logger.warning(f"Room {room} does not exist")
            return 0
        
        sent_count = 0
        disconnected_clients = []
        
        for client_id in self.rooms[room]:
            if client_id in self.active_connections:
                websocket = self.active_connections[client_id]
                try:
                    await websocket.send_text(message.to_json())
                    sent_count += 1
                    self.stats["messages_sent"] += 1
                except Exception as e:
                    logger.error(f"Error broadcasting to {client_id}: {e}")
                    self.stats["errors"] += 1
                    disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)
        
        logger.debug(f"Broadcasted to {sent_count} clients in room {room}")
        return sent_count
    
    async def broadcast_to_all(self, message: WSMessage) -> int:
        """
        Broadcast a message to all connected clients.
        
        Args:
            message: The message to broadcast
            
        Returns:
            Number of clients the message was sent to
        """
        sent_count = 0
        disconnected_clients = []
        
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(message.to_json())
                sent_count += 1
                self.stats["messages_sent"] += 1
            except Exception as e:
                logger.error(f"Error broadcasting to {client_id}: {e}")
                self.stats["errors"] += 1
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)
        
        logger.debug(f"Broadcasted to {sent_count} clients")
        return sent_count
    
    async def handle_client_message(self, client_id: str, message: str) -> None:
        """
        Process a message received from a client.
        
        Args:
            client_id: The sender client ID
            message: The raw message string
        """
        self.stats["messages_received"] += 1
        
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            action = data.get("action")
            
            if msg_type == "subscribe":
                room = data.get("room")
                if room:
                    await self.subscribe_to_room(client_id, room)
            
            elif msg_type == "unsubscribe":
                room = data.get("room")
                if room:
                    await self.unsubscribe_from_room(client_id, room)
            
            elif msg_type == "ping":
                # Respond with pong
                pong_msg = WSMessage(
                    type="pong",
                    action="response",
                    data={"client_time": data.get("timestamp")}
                )
                await self.send_personal_message(pong_msg, client_id)
            
            else:
                # Echo back for unknown message types (for debugging)
                echo_msg = WSMessage(
                    type="echo",
                    action="received",
                    data={"original": data}
                )
                await self.send_personal_message(echo_msg, client_id)
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from {client_id}: {e}")
            error_msg = WSMessage(
                type="error",
                action="invalid_message",
                data={"error": "Invalid JSON format"}
            )
            await self.send_personal_message(error_msg, client_id)
        except Exception as e:
            logger.error(f"Error handling message from {client_id}: {e}")
            self.stats["errors"] += 1
    
    def get_stats(self) -> dict:
        """
        Get connection manager statistics.
        
        Returns:
            Dictionary with current stats
        """
        return {
            **self.stats,
            "active_connections": len(self.active_connections),
            "room_subscribers": {room: len(clients) for room, clients in self.rooms.items()}
        }
    
    async def health_check(self) -> dict:
        """
        Perform health check on all connections.
        
        Returns:
            Health status of the WebSocket system
        """
        healthy_connections = 0
        unhealthy_connections = []
        
        for client_id, websocket in list(self.active_connections.items()):
            try:
                # Send a ping to check connection
                ping_msg = WSMessage(
                    type="ping",
                    action="health_check",
                    data={}
                )
                await websocket.send_text(ping_msg.to_json())
                healthy_connections += 1
            except:
                unhealthy_connections.append(client_id)
        
        # Clean up unhealthy connections
        for client_id in unhealthy_connections:
            self.disconnect(client_id)
        
        return {
            "status": "healthy" if healthy_connections > 0 or len(self.active_connections) == 0 else "degraded",
            "healthy_connections": healthy_connections,
            "removed_connections": len(unhealthy_connections),
            "total_active": len(self.active_connections)
        }


# Global connection manager instance
manager = ConnectionManager()


# Utility functions for external use
async def broadcast_price_update(symbol: str, price: float, change: float) -> None:
    """Broadcast price update to subscribed clients."""
    message = WSMessage(
        type="prices",
        action="update",
        data={
            "symbol": symbol,
            "price": price,
            "change": change,
            "change_percent": (change / price * 100) if price > 0 else 0
        }
    )
    await manager.broadcast_to_room(message, "prices")


async def broadcast_signal_alert(signal_type: str, signal_data: dict) -> None:
    """Broadcast signal alert to subscribed clients."""
    message = WSMessage(
        type="signals",
        action="alert",
        data={
            "signal_type": signal_type,
            **signal_data
        }
    )
    await manager.broadcast_to_room(message, "signals")


async def broadcast_news_update(news_data: dict) -> None:
    """Broadcast news update to subscribed clients."""
    message = WSMessage(
        type="news",
        action="update",
        data=news_data
    )
    await manager.broadcast_to_room(message, "news")


async def broadcast_portfolio_update(user_id: str, portfolio_data: dict) -> None:
    """Send portfolio update to specific user."""
    # Find client_id by user_id from metadata
    for client_id, metadata in manager.client_metadata.items():
        if metadata.get("user_id") == user_id:
            message = WSMessage(
                type="portfolio",
                action="update",
                data=portfolio_data
            )
            await manager.send_personal_message(message, client_id)


async def broadcast_system_message(message: str, severity: str = "info") -> None:
    """Broadcast system-wide message to all clients."""
    msg = WSMessage(
        type="system",
        action="announcement",
        data={
            "message": message,
            "severity": severity  # 'info', 'warning', 'error', 'success'
        }
    )
    await manager.broadcast_to_all(msg)