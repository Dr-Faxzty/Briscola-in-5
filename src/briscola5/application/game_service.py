from __future__ import annotations

import random

from briscola5.domain.card import Card, full_deck
from briscola5.domain.state import GameState, Phase


class GameService:

    def __init__(self):
        self.state = GameState()
        self.deck = full_deck()

    def setup_game(self, dealer_id, int=0):
        print("Start Game")
        random.shuffle(self.deck)
        for i in range(5):
            start = i * 8
            end = start + 8
            self.state.hands[i] = self.deck[start:end]
        self.state.turn.dealer_player = dealer_id
        self.state.turn.current_player = (dealer_id + 1) % 5
        self.state.phase = Phase.AUCTION
        print("Game Setup Complete")
        print("Current Player: ", self.state.turn.current_player)
        print("Begun Auction Phase")
        pass

    def rotation(self):
        old_player = self.state.turn.current_player
        self.state.turn.current_player = (self.state.turn.current_player + 1) % 5
        print(
            "Player ",
            old_player,
            " has completed their turn. It is now Player ",
            self.state.turn.current_player,
            "'s turn.",
        )
        pass

    def debug_status(self):
        """Utility for Debug."""
        print("-" * 30)
        print(f"Phase: {self.state.phase}")
        print(f"Turn: Player {self.state.turn.current_player}")
        print(f"Card : {len(self.state.hands[0])}")
        print("-" * 30)

    def auction_phase(self, player_id: int, offer: int | None):
        auction = self.state.auction
        if player_id != self.state.turn.current_player:
            print(f"Error: It's the player's turn {self.state.turn.current_player}")
            return

        if offer is None:
            auction.passed[player_id] = True
            print(f"Player {player_id} has PACE.")

        else:

            last_bid = auction.last_bid if auction.last_bid is not None else 60

            if offer <= last_bid:
                print(f"Error: The offer {offer} it's too low (Last: {last_bid})")
                return

            auction.last_bid = offer
            auction.last_bidder = player_id
            print(f"Player {player_id} tip {offer}!")

        if auction.active_players_count() == 1:
            self._conclude_auction()
        else:
            self._next_player_auction()

    def _next_player_auction(self):
        """Find the next player who hasn't passed yet."""
        current = self.state.turn.current_player
        while True:
            current = (current + 1) % 5
            if not self.state.auction.passed[current]:
                self.state.turn.current_player = current
                break

    def _conclude_auction(self):
        winner = self.state.auction.last_bidder
        score = self.state.auction.last_bid

        self.state.call.caller_player = winner
        self.state.call.target_points = score

        self.state.phase = Phase.DEAD_TRICK_CALL

        print("\n" + "=" * 30)
        print(f"AUCTION CLOSED!")
        print(f"Winner: Player {winner} with {score} points.")
        print(f"New Phase: {self.state.phase}")
        print("=" * 30)


if __name__ == "__main__":
    service = GameService()
    service.setup_game(dealer_id=0)

    service.auction_phase(1, 65)
    service.auction_phase(2, None)
    service.auction_phase(3, 70)
    service.auction_phase(4, None)
    service.auction_phase(0, None)
    service.auction_phase(1, None)
