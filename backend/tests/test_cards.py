import pytest

from app.cards import Card, Category, best_hand, deck


def cards(values: str):
    return [Card.parse(value) for value in values.split()]


def test_deck_has_fifty_two_unique_cards():
    values = deck()
    assert len(values) == len(set(values)) == 52


@pytest.mark.parametrize(
    ("values", "category"),
    [
        ("As Ks Qs Js Ts 2c 3d", Category.STRAIGHT_FLUSH),
        ("Ah Ad Ac As 2d 3d 4d", Category.QUADS),
        ("Kh Kd Ks 2c 2d 8h 9s", Category.FULL_HOUSE),
        ("Ah 2h 3h 4h 8h Kd Qs", Category.FLUSH),
        ("Ah 2d 3s 4c 5h Kd Qs", Category.STRAIGHT),
    ],
)
def test_best_hand_categories(values, category):
    assert best_hand(cards(values))[0] == category

