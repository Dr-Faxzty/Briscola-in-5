from __future__ import annotations

from typing import Sequence

from .card import Card, Suit


class PlayedCard:
    __slots__ = ("player_id", "card")

    def __init__(self, player_id: int, card: Card) -> None:
        self.player_id = player_id
        self.card = card

    def __repr__(self) -> str:
        return f"PlayedCard(player_id={self.player_id}, card={self.card!r})"


def trick_points(played: Sequence[PlayedCard]) -> int:
    return sum(pc.card.points for pc in played)


def resolve_trick(
    played: Sequence[PlayedCard], 
    trump_suit: Suit | None
    ) -> int:
    if len(played) != 5:
        raise ValueError(f"Expected 5 played cards, got {len(played)}")

    lead_suit = played[0].card.suit

    if (
        trump_suit is not None and any(
            pc.card.suit == trump_suit for pc in played
            )
        ):
        winning_suit = trump_suit
    else:
        winning_suit = lead_suit

    eligible = [pc for pc in played if pc.card.suit == winning_suit]
    winner = max(eligible, key=lambda pc: pc.card.strength)
    return winner.player_id
