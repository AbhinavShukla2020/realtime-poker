from __future__ import annotations

import asyncio
from collections.abc import Callable

from .game import Table
from .storage import TableStore


class RoomManager:
    def __init__(self, store: TableStore) -> None:
        self.store = store
        self._locks: dict[str, asyncio.Lock] = {}

    def _lock(self, table_id: str) -> asyncio.Lock:
        return self._locks.setdefault(table_id, asyncio.Lock())

    async def create(self, table: Table) -> Table:
        async with self._lock(table.table_id):
            if await self.store.load(table.table_id):
                raise ValueError("table already exists")
            await self.store.save(table)
            return table

    async def get(self, table_id: str) -> Table:
        table = await self.store.load(table_id)
        if table is None:
            raise KeyError(table_id)
        return table

    async def update(self, table_id: str, mutation: Callable[[Table], None]) -> Table:
        async with self._lock(table_id):
            table = await self.get(table_id)
            mutation(table)
            await self.store.save(table)
            return table

