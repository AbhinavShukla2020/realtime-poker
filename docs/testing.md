# Testing and load checks

The unit tests cover card uniqueness, five major hand categories, deterministic
shuffle inputs, tamper detection, private-card projections, turn validation, and
Redis-record round trips. Run them from `backend/` with `pytest -q`.

The included Locust file exercises HTTP table reads. A full WebSocket load run
should model joins, reconnects, actions, and server broadcasts, then report p50,
p95, and p99 message latency for 150 connected players. No latency result is
checked in because it depends on instance type, region, Redis placement, and
whether TLS termination is included.

