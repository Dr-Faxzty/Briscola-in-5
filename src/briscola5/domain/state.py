from __future__ import annotations

from enum import Enum
from typing import Optional

from .card import Card, Suit
from .trick import PlayedCard

PLAYER_COUNT = 5


class Phase(str, Enum):
    AUCTION = "auction"
    DEAD_TRICK_PLAY = "dead_trick_play"
    DEAD_TRICK_CALL = "dead_trick_call"
    DEAD_TRICK_RESOLVE = "dead_trick_resolve"
    TRICK_PLAY = "trick_play"
    GAME_OVER = "game_over"


class AuctionState:
    __slots__ = (
        "start_player",
        "current_player",
        "last_bid",
        "last_bidder",
        "passed",
    )

    def __init__(self, player_count: int, start_player: int = 0) -> None:
        if player_count != PLAYER_COUNT:
            raise ValueError("AuctionState requires exactly 5 players.")
        if not 0 <= start_player < player_count:
            raise ValueError(f"AuctionState requires exactly {PLAYER_COUNT} players.")

        self.start_player: int = start_player
        self.current_player: int = start_player

        self.last_bid: Optional[int] = None
        self.last_bidder: Optional[int] = None

        self.passed: list[bool] = [False for _ in range(player_count)]

    def is_player_active(self, player_id: int) -> bool:
        return not self.passed[player_id]

    def active_players_count(self) -> int:
        return sum(1 for p in self.passed if not p)

    def __repr__(self) -> str:
        return (
            "AuctionState("
            f"start={self.start_player}, current={self.current_player}, "
            f"last_bid={self.last_bid}, last_bidder={self.last_bidder}, "
            f"passed={self.passed}"
            ")"
        )


class TrickState:
    __slots__ = ("played", "index")

    def __init__(self) -> None:
        self.played: list[PlayedCard] = []
        self.index: int = 0

    def is_complete(self) -> bool:
        return len(self.played) == PLAYER_COUNT


class CallState:
    __slots__ = (
        "caller_player",
        "target_points",
        "trump_suit",
        "called_card",
        "partner_player_internal",
        "partner_revealed",
        "caller_team_won",
    )

    def __init__(self) -> None:
        self.caller_player: Optional[int] = None
        self.target_points: Optional[int] = None
        self.trump_suit: Optional[Suit] = None
        self.called_card: Optional[Card] = None
        self.partner_player_internal: Optional[int] = None
        self.partner_revealed: bool = False
        self.caller_team_won: Optional[bool] = None


class ScoreState:
    __slots__ = ("won_cards", "player_points")

    def __init__(self, player_count: int) -> None:
        self.won_cards: list[list[Card]] = [[] for _ in range(player_count)]
        self.player_points: list[int] = [0 for _ in range(player_count)]


class TurnState:
    __slots__ = ("current_player", "dealer_player")

    def __init__(self) -> None:
        self.current_player: int = 0
        self.dealer_player: int = 0


class GameState:
    __slots__ = (
        "phase",
        "hands",
        "auction",
        "trick",
        "call",
        "score",
        "turn",
    )

    def __init__(self) -> None:
        self.phase: Phase = Phase.AUCTION

        self.turn: TurnState = TurnState()
        self.hands: list[list[Card]] = [[] for _ in range(PLAYER_COUNT)]

        self.auction: AuctionState = AuctionState(player_count=PLAYER_COUNT, start_player=0)
        self.trick: TrickState = TrickState()
        self.call: CallState = CallState()
        self.score: ScoreState = ScoreState(player_count=PLAYER_COUNT)

    def is_game_over(self) -> bool:
        return self.phase == Phase.GAME_OVER

    def assert_player_id(self, player_id: int) -> None:
        if not 0 <= player_id < PLAYER_COUNT:
            raise ValueError(f"Invalid player_id {player_id}")

    def remaining_cards_in_hand(self, player_id: int) -> int:
        self.assert_player_id(player_id)
        return len(self.hands[player_id])

    def current_trick_is_complete(self) -> bool:
        return self.trick.is_complete()

    def team_points_if_known(self) -> Optional[tuple[int, int]]:
        """
        Returns (caller_team_points, others_points) if partner is known internally.
        Pure query; does not determine/assign partner.
        """
        caller = self.call.caller_player
        partner = self.call.partner_player_internal
        if caller is None or partner is None:
            return None

        caller_team = self.score.player_points[caller] + self.score.player_points[partner]
        others = sum(self.score.player_points) - caller_team
        return caller_team, others

    def __repr__(self) -> str:
        return (
            "GameState("
            f"phase={self.phase}, turn={self.turn.current_player}, "
            f"trick_index={self.trick.index}, "
            f"caller={self.call.caller_player}, target={self.call.target_points}, "
            f"trump={self.call.trump_suit}, called={self.call.called_card}, "
            f"points={self.score.player_points}"
            ")"
        )
