from __future__ import annotations
from enum import Enum

class Suit(str, Enum):
    ORO = "oro"
    COPPE = "coppe"
    SPADE = "spade"
    BASTONI = "bastoni"
    
class Rank(str, Enum):
    ASSO = "A"
    TRE = "3"
    RE = "R"
    CAVALLO = "C"
    DONNA = "D"
    SETTE = "7"
    SEI = "6"
    CINQUE = "5"
    QUATTRO = "4"
    DUE = "2"
    
TRICK_STRENGTH: dict[Rank, int] = {
    Rank.ASSO: 10,
    Rank.TRE: 9,
    Rank.RE: 8,
    Rank.CAVALLO: 7,
    Rank.DONNA: 6,
    Rank.SETTE: 5,
    Rank.SEI: 4,
    Rank.CINQUE: 3,
    Rank.QUATTRO: 2,
    Rank.DUE: 1
}

POINTS: dict[Rank, int] = {
    Rank.ASSO: 11,
    Rank.TRE: 10,
    Rank.RE: 4,
    Rank.CAVALLO: 3,
    Rank.DONNA: 2,
    Rank.SETTE: 0,
    Rank.SEI: 0,
    Rank.CINQUE: 0,
    Rank.QUATTRO: 0,
    Rank.DUE: 0
}

class Card:
    __slots__ = ("_suit", "_rank")
    
    def __init__(self, suit: Suit, rank: Rank) -> None:
        self._suit = suit
        self._rank = rank
    
    @property
    def suit(self) -> Suit:
        return self._suit

    @property
    def rank(self) -> Rank:
        return self._rank

    @property
    def points(self) -> int:
        return POINTS[self._rank]

    @property
    def strength(self) -> int:
        return TRICK_STRENGTH[self._rank]

    def __repr__(self) -> str:
        return f"Card({self._suit.value},{self._rank.value})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Card):
            return False
        return self._suit == other._suit and self._rank == other._rank

    def __hash__(self) -> int:
        return hash((self._suit, self._rank))
    
def full_deck() -> list[Card]:
    return [Card(s, r) for s in Suit for r in Rank]


def assert_is_valid_deck(deck: list[Card]) -> None:
    if set(deck) != set(full_deck()):
        raise ValueError("Deck is not a valid 40-card Sicilian deck")