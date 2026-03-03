from abc import ABC, abstractmethod

from briscola5.domain.card import Rank, Suit
from briscola5.domain.state import GameState


class BaseBot(ABC):

    def __init__(self, player_id: int) -> None:
        self.player_id = player_id

    @abstractmethod
    def make_bid(self, state: GameState) -> int | None:

        pass

    @abstractmethod
    def choose_discard(self, state: GameState) -> int:

        pass

    @abstractmethod
    def declare_trump_and_card(self, state: GameState) -> tuple[Suit, Rank]:

        pass

    @abstractmethod
    def play_card(self, state: GameState) -> int:

        pass
