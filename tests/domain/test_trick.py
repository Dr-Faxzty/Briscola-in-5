import pytest

from briscola5.domain.card import Card, Rank, Suit
from briscola5.domain.trick import PlayedCard, resolve_trick, trick_points


def pc(player_id: int, suit: Suit, rank: Rank) -> PlayedCard:
    return PlayedCard(player_id=player_id, card=Card(suit=suit, rank=rank))


def test_trick_points_sums_all_cards() -> None:
    played = [
        pc(0, Suit.ORO, Rank.ASSO),  # 11
        pc(1, Suit.COPPE, Rank.TRE),  # 10
        pc(2, Suit.SPADE, Rank.RE),  # 4
        pc(3, Suit.BASTONI, Rank.DONNA),  # 2
        pc(4, Suit.ORO, Rank.DUE),  # 0
    ]
    assert trick_points(played) == 27


def test_resolve_trick_no_trump_uses_lead_suit() -> None:
    played = [
        pc(0, Suit.ORO, Rank.SETTE),
        pc(1, Suit.COPPE, Rank.ASSO),
        pc(2, Suit.ORO, Rank.TRE),
        pc(3, Suit.SPADE, Rank.RE),
        pc(4, Suit.ORO, Rank.DUE),
    ]
    assert resolve_trick(played, trump_suit=None) == 2


def test_resolve_trick_trump_beats_lead_suit() -> None:
    played = [
        pc(0, Suit.COPPE, Rank.ASSO),
        pc(1, Suit.COPPE, Rank.TRE),
        pc(2, Suit.SPADE, Rank.DUE),
        pc(3, Suit.COPPE, Rank.RE),
        pc(4, Suit.ORO, Rank.ASSO),
    ]
    assert resolve_trick(played, trump_suit=Suit.SPADE) == 2


def test_resolve_trick_highest_trump_wins_if_multiple_trumps() -> None:
    played = [
        pc(0, Suit.BASTONI, Rank.ASSO),
        pc(1, Suit.SPADE, Rank.SETTE),
        pc(2, Suit.SPADE, Rank.TRE),
        pc(3, Suit.SPADE, Rank.DUE),
        pc(4, Suit.COPPE, Rank.ASSO),
    ]
    assert resolve_trick(played, trump_suit=Suit.SPADE) == 2


def test_resolve_trick_no_trump_in_play_falls_back_to_lead_suit() -> None:
    played = [
        pc(0, Suit.COPPE, Rank.RE),
        pc(1, Suit.ORO, Rank.ASSO),
        pc(2, Suit.COPPE, Rank.DUE),
        pc(3, Suit.COPPE, Rank.ASSO),
        pc(4, Suit.BASTONI, Rank.TRE),
    ]
    assert resolve_trick(played, trump_suit=Suit.SPADE) == 3


def test_resolve_trick_requires_5_cards() -> None:
    played = [
        pc(0, Suit.ORO, Rank.ASSO),
        pc(1, Suit.COPPE, Rank.TRE),
        pc(2, Suit.SPADE, Rank.RE),
        pc(3, Suit.BASTONI, Rank.DONNA),
    ]
    with pytest.raises(ValueError):
        resolve_trick(played, trump_suit=Suit.ORO)
