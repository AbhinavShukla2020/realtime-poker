from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass, field

from .cards import Card, deck


def commitment(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()


def derive_seed(hand_id: str, server_secret: str, player_entropy: dict[str, str]) -> bytes:
    material = [hand_id, server_secret]
    material.extend(f"{player}:{player_entropy[player]}" for player in sorted(player_entropy))
    return hashlib.sha256("|".join(material).encode()).digest()


def shuffled_deck(seed: bytes) -> list[Card]:
    """Fisher-Yates using HMAC-SHA256 as a deterministic random stream."""

    cards = deck()
    counter = 0
    for upper in range(len(cards) - 1, 0, -1):
        digest = hmac.new(seed, counter.to_bytes(8, "big"), hashlib.sha256).digest()
        index = int.from_bytes(digest[:8], "big") % (upper + 1)
        cards[upper], cards[index] = cards[index], cards[upper]
        counter += 1
    return cards


@dataclass
class FairShuffle:
    hand_id: str
    server_secret: str = field(default_factory=lambda: secrets.token_hex(32))
    player_entropy: dict[str, str] = field(default_factory=dict)

    @property
    def server_commitment(self) -> str:
        return commitment(self.server_secret)

    def add_player_entropy(self, player_id: str, entropy: str) -> None:
        if not entropy:
            raise ValueError("entropy must not be empty")
        self.player_entropy[player_id] = entropy

    def deal(self) -> list[Card]:
        return shuffled_deck(derive_seed(self.hand_id, self.server_secret, self.player_entropy))

    def reveal(self) -> dict[str, object]:
        return {
            "hand_id": self.hand_id,
            "server_secret": self.server_secret,
            "server_commitment": self.server_commitment,
            "player_entropy": dict(self.player_entropy),
        }


def verify_reveal(reveal: dict[str, object], observed_cards: list[str]) -> bool:
    secret = str(reveal["server_secret"])
    if commitment(secret) != reveal["server_commitment"]:
        return False
    seed = derive_seed(str(reveal["hand_id"]), secret, dict(reveal["player_entropy"]))
    expected = [str(card) for card in shuffled_deck(seed)[: len(observed_cards)]]
    return hmac.compare_digest("|".join(expected), "|".join(observed_cards))

