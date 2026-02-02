from fastapi import WebSocket
from typing import Dict, Set, List
import asyncio


class ConnectionManager:
    def __init__(self):
        # user_id -> set of websocket connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # project_id -> set of user_ids watching
        self.project_watchers: Dict[int, Set[int]] = {}
        # Lock for thread-safe operations
        self.lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user_id: int):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()

        async with self.lock:
            if user_id not in self.active_connections:
                self.active_connections[user_id] = set()
            self.active_connections[user_id].add(websocket)

        print(f"✓ User {user_id} connected. Total connections: {self.get_total_connections()}")

    def disconnect(self, websocket: WebSocket, user_id: int):
        """Remove a WebSocket connection"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

        # Remove from project watchers
        for project_id in list(self.project_watchers.keys()):
            self.project_watchers[project_id].discard(user_id)
            if not self.project_watchers[project_id]:
                del self.project_watchers[project_id]

        print(f"✓ User {user_id} disconnected. Total connections: {self.get_total_connections()}")

    async def watch_project(self, user_id: int, project_id: int):
        """Register user as watching a project"""
        async with self.lock:
            if project_id not in self.project_watchers:
                self.project_watchers[project_id] = set()
            self.project_watchers[project_id].add(user_id)

    async def unwatch_project(self, user_id: int, project_id: int):
        """Unregister user from watching a project"""
        async with self.lock:
            if project_id in self.project_watchers:
                self.project_watchers[project_id].discard(user_id)

    async def send_personal_message(self, message: dict, user_id: int):
        """Send message to specific user"""
        if user_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    print(f"Error sending to user {user_id}: {e}")
                    disconnected.add(connection)

            # Clean up disconnected connections
            for conn in disconnected:
                self.disconnect(conn, user_id)

    async def broadcast_to_project(self, project_id: int, message: dict, exclude_user: int | None = None):
        """Broadcast message to all users watching a project"""
        if project_id not in self.project_watchers:
            return

        watchers = self.project_watchers[project_id].copy()
        if exclude_user:
            watchers.discard(exclude_user)

        for user_id in watchers:
            await self.send_personal_message(message, user_id)

    async def broadcast_to_all(self, message: dict):
        """Broadcast message to all connected users"""
        for user_id in list(self.active_connections.keys()):
            await self.send_personal_message(message, user_id)

    def get_total_connections(self) -> int:
        """Get total number of active connections"""
        return sum(len(conns) for conns in self.active_connections.values())

    def get_online_users(self) -> List[int]:
        """Get list of currently online user IDs"""
        return list(self.active_connections.keys())


# Global manager instance
manager = ConnectionManager()