from __future__ import annotations

import asyncio

from fastapi import WebSocket


class WebSocketHub:
    def __init__(self) -> None:
        self.connections: dict[str, dict[str, WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, table_id: str, player_id: str, socket: WebSocket) -> None:
        await socket.accept()
        async with self._lock:
            old = self.connections.setdefault(table_id, {}).get(player_id)
            self.connections[table_id][player_id] = socket
        if old is not None:
            await old.close(code=4001, reason="reconnected from another client")

    async def disconnect(self, table_id: str, player_id: str, socket: WebSocket) -> None:
        async with self._lock:
            if self.connections.get(table_id, {}).get(player_id) is socket:
                del self.connections[table_id][player_id]

    async def broadcast_state(self, table) -> None:
        connections = list(self.connections.get(table.table_id, {}).items())
        for player_id, socket in connections:
            try:
                await socket.send_json({"type": "state", "state": table.public_state(player_id)})
            except RuntimeError:
                await self.disconnect(table.table_id, player_id, socket)

