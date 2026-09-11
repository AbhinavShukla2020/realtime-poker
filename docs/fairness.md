# Commit–reveal shuffle

Before dealing, the server creates a 256-bit secret and publishes its SHA-256
commitment. Players may contribute arbitrary entropy. The final seed hashes the
hand ID, server secret, and player contributions sorted by player ID. An
HMAC-SHA256 byte stream drives Fisher–Yates, producing a deterministic deck.

After the hand, the server reveals its secret and the collected entropy. Anyone
can recompute the commitment, seed, and deck prefix with `verify_reveal`. A
server cannot change its secret after publishing the commitment, and no single
player controls the shuffle if at least one input remains unpredictable.

This mechanism audits a completed deal; it does not prevent a malicious server
from aborting a hand before revealing. A production design should record
commitments in an append-only event log and penalize missing reveals.

