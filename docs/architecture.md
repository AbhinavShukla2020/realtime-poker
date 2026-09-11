# Architecture

The backend is authoritative: clients submit commands and render state, but they
never decide which actions are valid or which cards were dealt. Every table
mutation is serialized through a per-room asyncio lock and the resulting private
state is written to Redis. The private record includes the deck and unrevealed
server secret; the public projection hides opponents' hole cards.

PostgreSQL stores accounts and completed hand histories. Redis holds short-lived
table state so a process restart or reconnect does not lose an active hand. A
WebSocket hub routes a different public projection to each seat. Reconnecting
with the same player ID replaces the older connection and immediately receives
the latest Redis snapshot.

The single-process lock is sufficient for the included deployment. Running more
than one API replica requires a distributed lock or a single table-owner worker,
plus Redis pub/sub for cross-process WebSocket fan-out.

