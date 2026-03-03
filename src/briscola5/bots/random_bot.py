import random

from briscola5.bots.base import BaseBot
from briscola5.domain.card import Rank, Suit, full_deck
from briscola5.domain.state import GameState


class RandomBot(BaseBot):

    def make_bid(self, state: GameState) -> int | None:

        current_bid = state.auction.last_bid
        min_bid = (current_bid + 1) if current_bid is not None else 71

        if min_bid > 120:
            return None

        if random.choice([True, False]):
            return None

        return random.randint(min_bid, 120)

    def choose_discard(self, state: GameState) -> int:

        hand = state.hands[self.player_id]
        return random.choice(range(len(hand)))

    def declare_trump_and_card(self, state: GameState) -> tuple[Suit, Rank]:
        trump_suit = random.choice(list(Suit))
        hand = state.hands[self.player_id]

        valid_card = [
            card for card in full_deck() if card not in hand and card.suit == trump_suit
        ]

        called_card = random.choice(valid_card)
        return trump_suit, called_card.rank

    def play_card(self, state: GameState) -> int:
        hand = state.hands[self.player_id]
        return random.choice(range(len(hand)))
