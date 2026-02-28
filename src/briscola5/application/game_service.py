from __future__ import annotations

import random

from briscola5.domain.card import Card, Rank, Suit, full_deck
from briscola5.domain.state import GameState, Phase
from briscola5.domain.trick import PlayedCard, resolve_trick, trick_points


class GameService:

    def __init__(self):
        self.state = GameState()
        self.deck = full_deck()

    def setup_game(self, dealer_id: int):
        print("--- Start Game ---")
        random.shuffle(self.deck)
        for i in range(5):
            start = i * 8
            end = start + 8
            self.state.hands[i] = self.deck[start:end]

        self.state.turn.dealer_player = dealer_id
        # Il primo a parlare nell'asta è il giocatore dopo il dealer
        self.state.turn.current_player = (dealer_id + 1) % 5
        self.state.phase = Phase.AUCTION

        print(f"Game Setup Complete. Dealer: {dealer_id}")
        print(f"Current Player (Auction): {self.state.turn.current_player}")

    def rotation(self):
        """Rotazione semplice per le fasi di gioco."""
        old_player = self.state.turn.current_player
        self.state.turn.current_player = (self.state.turn.current_player + 1) % 5
        print(f"Player {old_player} played. Next: Player {self.state.turn.current_player}")

    def play_card(self, player_id: int, card_index: int):
        """Gestisce la giocata di una carta e le transizioni del primo giro."""
        if player_id != self.state.turn.current_player:
            print(f"Error: Not your turn! Expected Player {self.state.turn.current_player}")
            return

        # Preleviamo la carta dalla mano e creiamo l'oggetto PlayedCard
        card = self.state.hands[player_id].pop(card_index)
        played_card = PlayedCard(player_id=player_id, card=card)

        # Salviamo la giocata nel TrickState dello stato (self.state.trick.played)
        self.state.trick.played.append(played_card)

        print(f"Player {player_id} plays {card}")

        # Se il trick è completo (5 carte)
        if self.state.current_trick_is_complete():
            if self.state.phase == Phase.DEAD_TRICK_PLAY:
                # Fine primo giro, passiamo alla chiamata
                self.state.phase = Phase.DEAD_TRICK_CALL
                print("\n" + "=" * 40)
                print("GIRO MORTO (FIRST ROUND) FINISHED")
                print("Auction winner must now declare Trump and Called Card.")
                print("=" * 40)
            else:
                # Logica per i giri successivi
                self._finish_normal_trick()
        else:
            self.rotation()

    def make_call(self, suit: Suit, rank: Rank):
        """Dichiarazione briscola/carta e risoluzione del Giro Morto."""
        if self.state.phase != Phase.DEAD_TRICK_CALL:
            print(f"Error: Cannot call in phase {self.state.phase}")
            return

        # Creiamo l'oggetto Card chiamata
        called_card_obj = Card(suit, rank)

        # Aggiorniamo il CallState con i nomi corretti del tuo file state.py
        self.state.call.trump_suit = suit
        self.state.call.called_card = called_card_obj

        print(f"\n>>> CALL DECLARED: {called_card_obj} <<<")

        # Risolviamo il trick usando i dati in self.state.trick.played
        winner_id = resolve_trick(self.state.trick.played, trump_suit=suit)
        points = trick_points(self.state.trick.played)

        # Aggiorniamo lo ScoreState (player_points)
        self.state.score.player_points[winner_id] += points

        print(f"Player {winner_id} wins the first trick with {points} points!")

        # Controllo se il socio è uscito (partner_player_internal)
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
        """Auction management with player skipping logic (passed)."""
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
        # Let's move on to the Dead Loop
        self.state.phase = Phase.DEAD_TRICK_PLAY
        # In the dead round everyone starts playing from the first player after the dealer
        self.state.turn.current_player = (self.state.turn.dealer_player + 1) % 5
        print("\n" + "=" * 30)
        print("AUCTION CONCLUDED")
        print(f"Winner: {winner} | Points: {score}")
        print(f"Now playing: {self.state.phase}")
        print("=" * 30)

    def _finish_normal_trick(self):
        """Placeholder for resolving standard tricks after the call."""


# --- Esempio di Esecuzione ---
if __name__ == "__main__":
    service = GameService()
    service.setup_game(dealer_id=0)  # Dealer è P0, l'asta inizia da P1

    # Flusso Asta: P1 rilancia, gli altri passano
    service.auction_phase(1, 75)
    service.auction_phase(2, None)
    service.auction_phase(3, None)
    service.auction_phase(4, None)
    service.auction_phase(0, None)

    # Fase: DEAD_TRICK_PLAY (Tocca a P1, il primo dopo il dealer P0)
    service.play_card(1, 0)
    service.play_card(2, 0)
    service.play_card(3, 0)
    service.play_card(4, 0)
    service.play_card(0, 0)  # Ultimo del giro morto

    # Fase: DEAD_TRICK_CALL
    # P1 (il vincitore) chiama ORO e ASSO
    service.make_call(Suit.ORO, Rank.ASSO)
