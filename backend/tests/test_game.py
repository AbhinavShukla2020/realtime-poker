import pytest

from app.game import Street, Table


def table_with_players():
    table = Table("test")
    table.join("a", "Ada", 1000)
    table.join("b", "Ben", 1000)
    return table


def test_start_deals_private_cards_and_commitment():
    table = table_with_players()
    value = table.start_hand({"a": "one"})
    assert table.street == Street.PREFLOP
    assert all(len(player.cards) == 2 for player in table.players)
    assert len(value) == 64


def test_public_state_hides_other_hole_cards():
    table = table_with_players()
    table.start_hand()
    state = table.public_state("a")
    assert len(state["players"][0]["cards"]) == 2
    assert state["players"][1]["cards"] == []


def test_table_round_trips_private_redis_record():
    table = table_with_players()
    table.start_hand()
    restored = Table.from_record(table.to_record())
    assert restored.to_record() == table.to_record()


def test_out_of_turn_action_is_rejected():
    table = table_with_players()
    table.start_hand()
    wrong = table.players[(table.turn_index + 1) % 2]
    with pytest.raises(ValueError, match="turn"):
        table.act(wrong.player_id, "fold")

