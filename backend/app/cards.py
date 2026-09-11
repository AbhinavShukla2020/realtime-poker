from __future__ import annotations

import itertools
from collections import Counter
from dataclasses import dataclass
from enum import IntEnum

RANKS = "23456789TJQKA"
SUITS = "cdhs"


@dataclass(frozen=True, order=True)
class Card:
    rank: int
    suit: str

    @classmethod
    def parse(cls, value: str) -> "Card":
        if len(value) != 2 or value[0] not in RANKS or value[1] not in SUITS:
            raise ValueError(f"invalid card: {value}")
        return cls(RANKS.index(value[0]) + 2, value[1])

    def __str__(self) -> str:
        return RANKS[self.rank - 2] + self.suit


def deck() -> list[Card]:
    return [Card(rank, suit) for suit in SUITS for rank in range(2, 15)]


class Category(IntEnum):
    HIGH_CARD = 0
    PAIR = 1
    TWO_PAIR = 2
    TRIPS = 3
    STRAIGHT = 4
    FLUSH = 5
    FULL_HOUSE = 6
    QUADS = 7
    STRAIGHT_FLUSH = 8


def _straight_high(ranks: list[int]) -> int | None:
    unique = sorted(set(ranks), reverse=True)
    if 14 in unique:
        unique.append(1)
    for start in range(len(unique) - 4):
        window = unique[start : start + 5]
        if window[0] - window[4] == 4:
            return window[0]
    return None


def rank_five(cards: tuple[Card, ...]) -> tuple[int, ...]:
    ranks = [card.rank for card in cards]
    counts = Counter(ranks)
    groups = sorted(((count, rank) for rank, count in counts.items()), reverse=True)
    flush = len({card.suit for card in cards}) == 1
    straight = _straight_high(ranks)
    if flush and straight:
        return (Category.STRAIGHT_FLUSH, straight)
    if groups[0][0] == 4:
        return (Category.QUADS, groups[0][1], groups[1][1])
    if groups[0][0] == 3 and groups[1][0] == 2:
        return (Category.FULL_HOUSE, groups[0][1], groups[1][1])
    if flush:
        return (Category.FLUSH, *sorted(ranks, reverse=True))
    if straight:
        return (Category.STRAIGHT, straight)
    if groups[0][0] == 3:
        kickers = sorted((rank for rank in ranks if rank != groups[0][1]), reverse=True)
        return (Category.TRIPS, groups[0][1], *kickers)
    pairs = sorted((rank for count, rank in groups if count == 2), reverse=True)
    if len(pairs) == 2:
        kicker = max(rank for rank in ranks if rank not in pairs)
        return (Category.TWO_PAIR, *pairs, kicker)
    if len(pairs) == 1:
        kickers = sorted((rank for rank in ranks if rank != pairs[0]), reverse=True)
        return (Category.PAIR, pairs[0], *kickers)
    return (Category.HIGH_CARD, *sorted(ranks, reverse=True))


def best_hand(cards: list[Card]) -> tuple[int, ...]:
    if not 5 <= len(cards) <= 7:
        raise ValueError("best_hand expects five to seven cards")
    return max(rank_five(combo) for combo in itertools.combinations(cards, 5))

