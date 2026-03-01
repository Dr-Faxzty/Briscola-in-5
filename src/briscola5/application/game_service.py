from __future__ import annotations

import random

from briscola5.domain.card import Card, Rank, Suit, full_deck
from briscola5.domain.state import GameState, Phase
from briscola5.domain.trick import PlayedCard, resolve_trick, trick_points


class GameService:
    """Service to orchestrate the Briscola in 5 game logic and transitions."""

    def __init__(self):
        self.state = GameState()
        self.deck = full_deck()

    def setup_game(self, dealer_id: int):
        """Initializes the deck, deals hands, and sets the starting auction player."""
        print("--- Start Game ---")
        random.shuffle(self.deck)
        for i in range(5):
            start = i * 8
            end = start + 8
            self.state.hands[i] = self.deck[start:end]

        self.state.turn.dealer_player = dealer_id
        self.state.turn.current_player = (dealer_id + 1) % 5
        self.state.phase = Phase.AUCTION

        print(f"Game Setup Complete. Dealer: {dealer_id}")
        print(f"Current Player (Auction): {self.state.turn.current_player}")

    def rotation(self):
        """Standard rotation for the current player."""
        old_player = self.state.turn.current_player
        self.state.turn.current_player = (self.state.turn.current_player + 1) % 5
        print(f"Player {old_player} played. Next: Player {self.state.turn.current_player}")

    def play_card(self, player_id: int, card_index: int):
        """Handles playing a card and transitions between game phases."""
        if player_id != self.state.turn.current_player:
            print(f"Error: Not your turn! Expected Player {self.state.turn.current_player}")
            return

        card = self.state.hands[player_id].pop(card_index)
        played_card = PlayedCard(player_id=player_id, card=card)

        self.state.trick.played.append(played_card)
        print(f"Player {player_id} plays {card}")

        if self.state.current_trick_is_complete():
            if self.state.phase == Phase.DEAD_TRICK_PLAY:
                self.state.phase = Phase.DEAD_TRICK_CALL
                print("\n" + "=" * 40)
                print("DEAD TRICK (FIRST ROUND) FINISHED")
                print("Auction winner must now declare Trump and Called Card.")
                print("=" * 40)
            else:
                self._finish_normal_trick()
        else:
            self.rotation()

    def make_call(self, suit: Suit, rank: Rank):
        """Declares the trump suit and called card, resolving the first trick."""
        if self.state.phase != Phase.DEAD_TRICK_CALL:
            print(f"Error: Cannot call in phase {self.state.phase}")
            return

        called_card_obj = Card(suit, rank)
        self.state.call.trump_suit = suit
        self.state.call.called_card = called_card_obj

        print(f"\n>>> CALL DECLARED: {called_card_obj} <<<")

        winner_id = resolve_trick(self.state.trick.played, trump_suit=suit)
        points = trick_points(self.state.trick.played)
        self.state.score.player_points[winner_id] += points

        print(f"Player {winner_id} wins the first trick with {points} points!")

        for pc in self.state.trick.played:
            if pc.card == called_card_obj:
                self.state.call.partner_player_internal = pc.player_id
                self.state.call.partner_revealed = True
                print(f"!! PARTNER REVEALED: Player {pc.player_id} !!")

        self.state.trick.played = []
        self.state.trick.index += 1
        self.state.phase = Phase.TRICK_PLAY
        self.state.turn.current_player = winner_id
        print(f"New Phase: {self.state.phase}. Player {winner_id} starts next round.")

    def auction_phase(self, player_id: int, offer: int | None):
        """Manages auction bids and determines the caller."""
        auction = self.state.auction
        if player_id != self.state.turn.current_player:
            print(f"Error: Expected Player {self.state.turn.current_player}")
            return

        if offer is None:
            auction.passed[player_id] = True
            print(f"Player {player_id} PASSED.")
        else:
            last_bid = auction.last_bid if auction.last_bid is not None else 60
            if offer <= last_bid:
                print(f"Error: Bid {offer} too low (Last: {last_bid})")
                return
            auction.last_bid = offer
            auction.last_bidder = player_id
            print(f"Player {player_id} bids {offer}!")

        if auction.active_players_count() == 1:
            self._conclude_auction()
        else:
            self._next_player_auction()

    def _next_player_auction(self):
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
        self.state.phase = Phase.DEAD_TRICK_PLAY
        self.state.turn.current_player = (self.state.turn.dealer_player + 1) % 5

        print("\n" + "=" * 30)
        print("AUCTION CONCLUDED")
        print(f"Winner: {winner} | Points: {score}")
        print("=" * 30)

    def show_hand(self, player_id: int):
        """Prints the current hand of a player using proper enumeration."""
        hand = self.state.hands[player_id]
        print("=" * 30)
        print(f"Player {player_id} hand:")

        for i, card in enumerate(hand):
            print(f"{i}: {card}")
        print("=" * 30)

    def _finish_normal_trick(self):
        """Resolves a standard trick during TRICK_PLAY phase."""
        trump = self.state.call.trump_suit
        winner_id = resolve_trick(self.state.trick.played, trump_suit=trump)
        points = trick_points(self.state.trick.played)
        self.state.score.player_points[winner_id] += points

        if not self.state.call.partner_revealed:
            for pc in self.state.trick.played:
                if pc.card == self.state.call.called_card:
                    self.state.call.partner_player_internal = pc.player_id
                    self.state.call.partner_revealed = True
                    print(f"!! PARTNER DISCOVERED: Player {pc.player_id} !!")

        print(f"Player {winner_id} wins the trick with {points} points.")
        self.state.trick.played = []
        self.state.trick.index += 1
        self.state.turn.current_player = winner_id

        if self.state.remaining_cards_in_hand(winner_id) == 0:
            self.state.phase = Phase.GAME_OVER

    def normal_trick_rounds(self, card_index: int, player_id: int):
        """Entry point for executing a move in normal play phase."""
        if player_id != self.state.turn.current_player:
            print(f"Error: It's Player {self.state.turn.current_player}'s turn.")
            return
        self.play_card(player_id, card_index)

    def end_game(self):
        """Calculates final scores and declares the winning team."""
        caller = self.state.call.caller_player
        partner = self.state.call.partner_player_internal
        target = self.state.call.target_points

        if caller is None or target is None:
            print("Error: Cannot end game. Auction data missing (caller or target is None).")
            return

        caller_points = self.state.score.player_points[caller]

        partner_points = 0
        if partner is not None:
            partner_points = self.state.score.player_points[partner]

        team_points = caller_points + partner_points

        print("*" * 30)
        print("\n--- FINAL RESULTS ---")
        print(f"Caller (P{caller}): {caller_points} | Partner (P{partner}): {partner_points}")
        print(f"Total Team: {team_points} / Target: {target}")

        if team_points >= target:
            print(">>> CALLER'S TEAM WINS! <<<")
            self.state.call.caller_team_won = True
        else:
            print(">>> OPPOSING TEAM WINS! <<<")
            self.state.call.caller_team_won = False
        print("*" * 30)
