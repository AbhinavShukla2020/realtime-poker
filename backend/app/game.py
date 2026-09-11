from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum

from .cards import Card, best_hand
from .fairness import FairShuffle


class Street(str, Enum):
    WAITING = "waiting"
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    COMPLETE = "complete"


@dataclass
class Player:
    player_id: str
    name: str
    stack: int
    cards: list[Card] = field(default_factory=list)
    bet: int = 0
    folded: bool = False
    connected: bool = True


@dataclass
class Table:
    table_id: str
    small_blind: int = 5
    big_blind: int = 10
    players: list[Player] = field(default_factory=list)
    street: Street = Street.WAITING
    community: list[Card] = field(default_factory=list)
    pot: int = 0
    current_bet: int = 0
    dealer_index: int = -1
    turn_index: int = 0
    hand_id: str | None = None
    shuffle: FairShuffle | None = None
    shoe: list[Card] = field(default_factory=list)
    audit: dict[str, object] | None = None

    def join(self, player_id: str, name: str, stack: int) -> Player:
        if self.street not in {Street.WAITING, Street.COMPLETE}:
            raise ValueError("cannot join during a hand")
        if any(player.player_id == player_id for player in self.players):
            raise ValueError("player is already seated")
        if len(self.players) >= 9:
            raise ValueError("table is full")
        player = Player(player_id, name, stack)
        self.players.append(player)
        return player

    def start_hand(self, entropy: dict[str, str] | None = None) -> str:
        eligible = [player for player in self.players if player.stack > 0]
        if len(eligible) < 2:
            raise ValueError("at least two funded players are required")
        self.hand_id = uuid.uuid4().hex
        self.shuffle = FairShuffle(self.hand_id)
        for player_id, value in (entropy or {}).items():
            self.shuffle.add_player_entropy(player_id, value)
        self.shoe = self.shuffle.deal()
        self.community.clear()
        self.pot = self.current_bet = 0
        self.dealer_index = (self.dealer_index + 1) % len(self.players)
        for player in self.players:
            player.cards = [self.shoe.pop(0), self.shoe.pop(0)]
            player.bet = 0
            player.folded = player.stack <= 0
        self.street = Street.PREFLOP
        if len(self.players) == 2:
            small_index, big_index = self.dealer_index, (self.dealer_index + 1) % 2
            self.turn_index = self.dealer_index
        else:
            small_index = (self.dealer_index + 1) % len(self.players)
            big_index = (self.dealer_index + 2) % len(self.players)
            self.turn_index = (self.dealer_index + 3) % len(self.players)
        self._commit(self.players[small_index], min(self.small_blind, self.players[small_index].stack))
        self._commit(self.players[big_index], min(self.big_blind, self.players[big_index].stack))
        self.current_bet = self.players[big_index].bet
        return self.shuffle.server_commitment

    def act(self, player_id: str, action: str, amount: int = 0) -> None:
        player = self.players[self.turn_index]
        if player.player_id != player_id:
            raise ValueError("not this player's turn")
        if action == "fold":
            player.folded = True
        elif action == "check":
            if player.bet != self.current_bet:
                raise ValueError("cannot check while facing a bet")
        elif action == "call":
            self._commit(player, min(player.stack, self.current_bet - player.bet))
        elif action == "raise":
            if amount <= self.current_bet:
                raise ValueError("raise must exceed the current bet")
            self._commit(player, min(player.stack, amount - player.bet))
            self.current_bet = player.bet
        else:
            raise ValueError("unknown action")
        if len(self.active_players) == 1:
            self._finish()
            return
        self._advance_turn()

    @property
    def active_players(self) -> list[Player]:
        return [player for player in self.players if not player.folded and player.cards]

    def _commit(self, player: Player, amount: int) -> None:
        player.stack -= amount
        player.bet += amount
        self.pot += amount

    def _advance_turn(self) -> None:
        for _ in self.players:
            self.turn_index = (self.turn_index + 1) % len(self.players)
            if not self.players[self.turn_index].folded:
                return

    def next_street(self) -> None:
        if self.street == Street.PREFLOP:
            self.community.extend(self.shoe[:3])
            del self.shoe[:3]
            self.street = Street.FLOP
        elif self.street == Street.FLOP:
            self.community.append(self.shoe.pop(0))
            self.street = Street.TURN
        elif self.street == Street.TURN:
            self.community.append(self.shoe.pop(0))
            self.street = Street.RIVER
        elif self.street == Street.RIVER:
            self._finish()
            return
        else:
            raise ValueError("street cannot advance")
        for player in self.players:
            player.bet = 0
        self.current_bet = 0
        self.turn_index = (self.dealer_index + 1) % len(self.players)

    def _finish(self) -> None:
        contenders = self.active_players
        if len(contenders) > 1:
            ranks = {player.player_id: best_hand(player.cards + self.community) for player in contenders}
            winning_rank = max(ranks.values())
            winners = [player for player in contenders if ranks[player.player_id] == winning_rank]
        else:
            winners = contenders
        share, remainder = divmod(self.pot, len(winners))
        for index, winner in enumerate(winners):
            winner.stack += share + (1 if index < remainder else 0)
        self.pot = 0
        self.street = Street.COMPLETE
        self.audit = self.shuffle.reveal() if self.shuffle else None

    def public_state(self, viewer_id: str | None = None) -> dict[str, object]:
        players = []
        for player in self.players:
            payload = asdict(player)
            payload["cards"] = [str(card) for card in player.cards] if viewer_id == player.player_id else []
            players.append(payload)
        return {
            "table_id": self.table_id,
            "street": self.street,
            "community": [str(card) for card in self.community],
            "pot": self.pot,
            "current_bet": self.current_bet,
            "turn_player_id": self.players[self.turn_index].player_id if self.players else None,
            "players": players,
            "hand_id": self.hand_id,
            "commitment": self.shuffle.server_commitment if self.shuffle else None,
            "audit": self.audit,
        }

    def to_record(self) -> dict[str, object]:
        return {
            "table_id": self.table_id,
            "small_blind": self.small_blind,
            "big_blind": self.big_blind,
            "players": [
                {
                    **asdict(player),
                    "cards": [str(card) for card in player.cards],
                }
                for player in self.players
            ],
            "street": self.street.value,
            "community": [str(card) for card in self.community],
            "pot": self.pot,
            "current_bet": self.current_bet,
            "dealer_index": self.dealer_index,
            "turn_index": self.turn_index,
            "hand_id": self.hand_id,
            "shuffle": self.shuffle.reveal() if self.shuffle else None,
            "shoe": [str(card) for card in self.shoe],
            "audit": self.audit,
        }

    @classmethod
    def from_record(cls, record: dict[str, object]) -> "Table":
        table = cls(
            table_id=str(record["table_id"]),
            small_blind=int(record["small_blind"]),
            big_blind=int(record["big_blind"]),
        )
        table.players = [
            Player(
                player_id=str(player["player_id"]),
                name=str(player["name"]),
                stack=int(player["stack"]),
                cards=[Card.parse(card) for card in player["cards"]],
                bet=int(player["bet"]),
                folded=bool(player["folded"]),
                connected=bool(player["connected"]),
            )
            for player in record["players"]
        ]
        table.street = Street(str(record["street"]))
        table.community = [Card.parse(card) for card in record["community"]]
        table.pot = int(record["pot"])
        table.current_bet = int(record["current_bet"])
        table.dealer_index = int(record["dealer_index"])
        table.turn_index = int(record["turn_index"])
        table.hand_id = record.get("hand_id")
        table.shoe = [Card.parse(card) for card in record["shoe"]]
        table.audit = record.get("audit")
        shuffle_record = record.get("shuffle")
        if shuffle_record:
            table.shuffle = FairShuffle(
                hand_id=str(shuffle_record["hand_id"]),
                server_secret=str(shuffle_record["server_secret"]),
                player_entropy=dict(shuffle_record["player_entropy"]),
            )
        return table
