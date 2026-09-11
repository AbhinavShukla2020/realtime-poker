# River Room — Real-Time Multiplayer Poker

River Room is a full-stack Texas Hold'em project with an authoritative FastAPI
server, React client, WebSocket updates, Redis table recovery, PostgreSQL account
and hand-history models, and an auditable SHA-256 commit–reveal shuffle.

## Run locally

```bash
docker compose up --build
curl -X POST http://localhost:8000/tables \
  -H 'content-type: application/json' -d '{"table_id":"demo"}'
```

Open `http://localhost:5173`, join table `demo` from two browser windows, and
start a hand. The backend test suite runs separately:

```bash
cd backend
python -m pip install -e '.[dev]'
pytest -q
```

## Design highlights

- The server validates turns, bets, card visibility, and street transitions.
- Each state mutation is serialized and persisted as a recoverable Redis record.
- A reconnect with the same player ID receives the current private projection.
- The shuffle publishes a pre-deal commitment and a post-hand reveal that can be
  independently verified.
- Seven-card showdown evaluation enumerates five-card combinations with complete
  tie breakers.

See `docs/architecture.md`, `docs/fairness.md`, and `docs/testing.md` for the
tradeoffs and validation procedure. The baseline intentionally omits side pots,
tournament rules, authentication tokens, and multi-node room ownership.

