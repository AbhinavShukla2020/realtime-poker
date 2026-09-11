from app.game import Table
from app.storage import MemoryTableStore


async def test_memory_store_returns_independent_snapshot():
    store = MemoryTableStore()
    table = Table("room")
    table.join("a", "Ada", 100)
    await store.save(table)
    loaded = await store.load("room")
    loaded.players[0].stack = 1
    reloaded = await store.load("room")
    assert reloaded.players[0].stack == 100

