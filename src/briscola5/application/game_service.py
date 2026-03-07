from __future__ import annotations

import random

from briscola5.domain.card import Card, Rank, Suit, full_deck
from briscola5.domain.color_cli import Col
from briscola5.domain.state import GameState, Phase
from briscola5.domain.trick import PlayedCard, resolve_trick, trick_points


class GameService:
    """Service to orchestrate the Briscola in 5 game logic and transitions."""

    def __init__(self):
        self.state = GameState()
        self.deck = full_deck()

    def setup_game(self, dealer_id: int):
        """Initializes the deck, deals hands, and sets the starting auction player."""
        print(f"{Col.BOLD}--- Start Game ---{Col.RESET}")
        random.shuffle(self.deck)
        for i in range(5):
            start = i * 8
            end = start + 8
            self.state.hands[i] = self.deck[start:end]
        self.state.turn.dealer_player = dealer_id
        self.state.turn.current_player = (dealer_id + 1) % 5
        self.state.phase = Phase.AUCTION

        print(f"{Col.BOLD}Game Setup Complete. Dealer: {dealer_id}{Col.RESET}")
        print(f"{Col.BOLD}Current Player (Auction): {self.state.turn.current_player}{Col.RESET}")

    def rotation(self):
        """Standard rotation for the current player."""
        old_player = self.state.turn.current_player
        self.state.turn.current_player = (self.state.turn.current_player + 1) % 5
        print(f"{Col.BOLD}Player {old_player}{Col.RESET}")
        print(f"{Col.BOLD}played. Next: Player {self.state.turn.current_player}{Col.RESET}")

    def play_card(self, player_id: int, card_index: int) -> bool:
        """Handles playing a card and transitions between game phases."""
        if player_id != self.state.turn.current_player:
            print(f"{Col.RED}Error: Not your turn!{Col.RESET}")
            print(f"{Col.RED}Expected Player {self.state.turn.current_player}{Col.RESET}")
            return False
        if self.state.phase is Phase.DEAD_TRICK_PLAY:
            if self.state.call.target_points is None:
                print(f"{Col.RED}Error: Cannot play card.{Col.RESET}")
                print(f"{Col.RED}Target points not set in call.{Col.RESET}")
                return False
            pt = self.state.call.target_points
            for card_played in self.state.trick.played:
                pt += card_played.card.points
            if self.state.hands[player_id][card_index].points + pt > 120:
                print(f"{Col.RED}Error:{Col.BOLD}")
                print(
                    f"{Col.RED}Cannot play {self.state.hands[player_id][card_index]}{Col.RESET}"
                )
                return False
        card = self.state.hands[player_id].pop(card_index)
        played_card = PlayedCard(player_id=player_id, card=card)
        self.state.trick.played.append(played_card)
        print(f"{Col.BOLD}Player {player_id} plays {card}{Col.RESET}")

        if self.state.current_trick_is_complete():
            if self.state.phase == Phase.DEAD_TRICK_PLAY:
                self.state.phase = Phase.DEAD_TRICK_CALL
                print("\n" + "=" * 40)
                print(f"{Col.BOLD}DEAD TRICK (FIRST ROUND) FINISHED{Col.RESET}")
                print(f"{Col.BOLD}Auction winner must now{Col.RESET}")
                print(f"{Col.BOLD}declare Trump and Called Card.{Col.RESET}")
                print("=" * 40)
            else:
                self._finish_normal_trick()
        else:
            self.rotation()
        return True

    def make_call(self, suit: Suit, rank: Rank)->bool:
        """Declares the trump suit and called card, resolving the first trick."""
        if self.state.phase != Phase.DEAD_TRICK_CALL:
            print(f"{Col.RED}Error: Cannot call in phase {self.state.phase}{Col.RESET}")
            return False

        called_card_obj = Card(suit, rank)
        if called_card_obj in self.state.hands[self.state.call.caller_player]:
            print(f"{Col.RED}Error: Called card {called_card_obj} are in caller's hand!{Col.RESET}")
            return False
        self.state.call.trump_suit = suit
        self.state.call.called_card = called_card_obj

        print(f"{Col.BOLD}\n>>> CALL DECLARED: {called_card_obj} <<<{Col.RESET}")

        winner_id = resolve_trick(self.state.trick.played, trump_suit=suit)
        points = trick_points(self.state.trick.played)
        self.state.score.player_points[winner_id] += points

        print(f"{Col.GREEN}Player {winner_id} wins the first trick with {points}{Col.RESET}")

        for pc in self.state.trick.played:
            if pc.card == called_card_obj:
                self.state.call.partner_player_internal = pc.player_id
                self.state.call.partner_revealed = True
                print(f"{Col.MAGENTA}!! PARTNER REVEALED: Player {pc.player_id} !!{Col.RESET}")

        self.state.trick.played = []
        self.state.trick.index += 1
        self.state.phase = Phase.TRICK_PLAY
        self.state.turn.current_player = winner_id
        print(f"{Col.BOLD}New Phase: {self.state.phase}.{Col.RESET}")
        print(f"{Col.BOLD}Player {winner_id} starts next round.{Col.RESET}")
        return True

    def auction_phase(self, player_id: int, offer: int | None):
        """Manages auction bids and determines the caller."""
        auction = self.state.auction
        if player_id != self.state.turn.current_player:
            print(f"{Col.RED}Error: Expected Player {self.state.turn.current_player}{Col.RESET}")
            return
        if offer is None:
            auction.passed[player_id] = True
            print(f"{Col.RED}Player {player_id} PASSED.{Col.RESET}")
        else:
            last_bid = auction.last_bid if auction.last_bid is not None else 70
            if offer <= last_bid:
                print(f"{Col.RED}Error: Bid {offer} too low (Last: {last_bid}){Col.RESET}")
                return
            auction.last_bid = offer
            auction.last_bidder = player_id
            print(f"{Col.GREEN}Player {player_id} bids {offer}!{Col.RESET}")

        if auction.active_players_count() == 1 and auction.last_bidder is not None:
            self._conclude_auction()
        elif auction.active_players_count() == 0 and auction.last_bidder is None:

            print(f"{Col.RED}Error: No valid bids placed. Cannot conclude auction.{Col.RESET}")
            print(f"{Col.RED}All players passed. Restarting game...{Col.RESET}")
            self.setup_game(self.state.turn.dealer_player)
            return
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
        print(f"{Col.BOLD}AUCTION CONCLUDED{Col.RESET}")
        print(f"{Col.GREEN}Winner: {winner} | Points: {score}{Col.RESET}")
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
                    print(
                        f"{Col.MAGENTA}!PARTNER DISCOVERED: Player {pc.player_id} !!{Col.RESET}"
                    )

        print(f"{Col.GREEN}Player {winner_id} wins the trick with {points} points.{Col.RESET}")
        self.state.trick.played = []
        self.state.trick.index += 1
        self.state.turn.current_player = winner_id

        if self.state.remaining_cards_in_hand(winner_id) == 0:
            self.state.phase = Phase.GAME_OVER

    def normal_trick_rounds(self, card_index: int, player_id: int):
        """Entry point for executing a move in normal play phase."""
        if player_id != self.state.turn.current_player:
            print(
                f"{Col.RED}Error:It's Player{self.state.turn.current_player}'s turn.{Col.RESET}"
            )
            return
        self.play_card(player_id, card_index)

    def end_game(self):
        """Calculates final scores and declares the winning team."""
        caller = self.state.call.caller_player
        partner = self.state.call.partner_player_internal
        target = self.state.call.target_points

        if caller is None or target is None:
            print(f"{Col.RED}Error: Cannot end game.{Col.RESET}")
            print(f"{Col.RED}Auction data missing (caller or target is None).{Col.RESET}")
            return

        caller_points = self.state.score.player_points[caller]

        partner_points = 0
        if partner is not None:
            partner_points = self.state.score.player_points[partner]

        team_points = caller_points + partner_points

        print("*" * 30)
        print(f"\n{Col.BOLD}--- FINAL RESULTS ---{Col.RESET}")
        print(f"Caller (P{caller}): {caller_points} | Partner (P{partner}): {partner_points}")
        print(f"Total Team: {team_points} / Target: {target}")

        if team_points >= target:
            print(f"{Col.GREEN}>>> CALLER'S TEAM WINS! <<<{Col.RESET}")
            self.state.call.caller_team_won = True
        else:
            print(f"{Col.GREEN}>>> OPPOSING TEAM WINS! <<<{Col.RESET}")
            self.state.call.caller_team_won = False
        print("*" * 30)
