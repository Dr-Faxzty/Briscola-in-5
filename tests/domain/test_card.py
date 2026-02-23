import pytest
from briscola5.domain.card import (
    Card,
    Suit,
    Rank,
    POINTS,
    TRICK_STRENGTH,
    full_deck,
    assert_is_valid_deck,
)


@pytest.mark.parametrize("rank,expected", list(POINTS.items()))
def test_card_points(rank: Rank, expected: int) -> None:
    card = Card(Suit.ORO, rank)
    assert card.points == expected


@pytest.mark.parametrize("rank,expected", list(TRICK_STRENGTH.items()))
def test_card_strength(rank: Rank, expected: int) -> None:
    card = Card(Suit.COPPE, rank)
    assert card.strength == expected


def test_full_deck_has_40_unique_cards() -> None:
    deck = full_deck()
    assert len(deck) == 40
    assert len(set(deck)) == 40


def test_invalid_deck_length_raises() -> None:
    deck = full_deck()[:-1]
    with pytest.raises(ValueError):
        assert_is_valid_deck(deck)


def test_invalid_deck_duplicates_raises() -> None:
    deck = full_deck()
    deck[-1] = deck[0]
    with pytest.raises(ValueError):
        assert_is_valid_deck(deck)
