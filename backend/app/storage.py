from __future__ import annotations

import json
from typing import Protocol

from redis.asyncio import Redis

from .game import Table


class TableStore(Protocol):
    async def load(self, table_id: str) -> Table | None: ...

    async def save(self, table: Table) -> None: ...


class RedisTableStore:
    def __init__(self, redis: Redis, ttl_seconds: int = 900) -> None:
        self.redis = redis
        self.ttl_seconds = ttl_seconds

    async def load(self, table_id: str) -> Table | None:
        payload = await self.redis.get(f"poker:table:{table_id}")
        if payload is None:
            return None
        return Table.from_record(json.loads(payload))

    async def save(self, table: Table) -> None:
        await self.redis.set(
            f"poker:table:{table.table_id}",
            json.dumps(table.to_record(), separators=(",", ":")),
            ex=self.ttl_seconds,
        )


class MemoryTableStore:
    def __init__(self) -> None:
        self.tables: dict[str, dict[str, object]] = {}

    async def load(self, table_id: str) -> Table | None:
        record = self.tables.get(table_id)
        return Table.from_record(record) if record else None

    async def save(self, table: Table) -> None:
        self.tables[table.table_id] = table.to_record()

