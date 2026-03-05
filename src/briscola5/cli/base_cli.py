import os
from typing import Any

from briscola5.application.game_service import GameService
from briscola5.bots.greedy_bot import GreedyBot
from briscola5.bots.random_bot import RandomBot
from briscola5.domain.card import Rank, Suit
from briscola5.domain.state import Phase


class CLI:
    def __init__(self, player_id: int = 0):
        self.service = GameService()
        self.human_id = player_id
        self.bots: dict[int, Any] = {}

    def clear_screen(self):
        os.system("cls" if os.name == "nt" else "clear")

    def print_header(self, title: str):
        self.clear_screen()
        print("=" * 50)
        print(f"🃏 {title.center(46)} 🃏")
        print("=" * 50)

    def setup_bots(self):
        print("\n--- CHOICE YOUR OPPONENT --")
        print("1. (4 x RandomBot - Random Moves)")
        print("2. (4 x GreedyBot - Advanced Strategy)")

        while True:
            choice = input("Insert 1 or 2: ").strip()
            if choice in ["1", "2"]:
                break
            print("Invalid input. Choose 1 or 2.")
        bot_class: type[Any]
        if choice == "1":
            bot_class = RandomBot
            print("\nYou chose Level 1: Playing with 4 RandomBots.")
        else:
            bot_class = GreedyBot
            print("\nYou chose Level 2: Playing with 4 GreedyBots.")

        for i in range(5):
            if i != self.human_id:
                self.bots[i] = bot_class(player_id=i)

        input("\nPress ENTER to start the game...")

    def _handle_human_bid(self, minimum: int, current: int):
        while True:
            prompt = f"Your turn! Enter a bid ({minimum}-120) or 'pass': "
            choice = input(prompt).strip().lower()

            if choice == "pass":
                self.service.auction_phase(self.human_id, None)
                print("You passed.")
                break
            if choice.isdigit():
                bid_val = int(choice)
                if 71 <= bid_val <= 120 and (current == 0 or bid_val > current):
                    self.service.auction_phase(self.human_id, bid_val)
                    print(f"You offered: {bid_val}")
                    break
                print(f" Offer must be between {minimum} and 120.")
            else:
                print(" Unrecognized input.")

    def run_action(self):
        print("\n-- AUCTION STARTS --")

        while self.service.state.phase == Phase.AUCTION:
            curr_p = self.service.state.turn.current_player
            curr_bid = self.service.state.auction.last_bid or 0

            if curr_p == self.human_id:
                self._handle_human_bid(max(71, curr_bid + 1), curr_bid)
            else:
                bot = self.bots[curr_p]
                bid = bot.make_bid(self.service.state)
                self.service.auction_phase(curr_p, bid)
                msg = "PASSED" if bid is None else f"OFFERED {bid}"
                print(f"Player {curr_p} ({bot.__class__.__name__}) {msg}")

        caller = self.service.state.call.caller_player
        target = self.service.state.call.target_points
        print(f"\nAUCTION ENDED! Caller: Player {caller} | Target: {target}")

    def _human_discard(self, curr_p: int):
        self.display_hand()
        while True:
            choice = input("Your turn! Index to discard [0-7]: ").strip()
            if not choice.isdigit():
                print("Enter a number.")
                continue
            idx = int(choice)
            if 0 <= idx < len(self.service.state.hands[self.human_id]):
                card = self.service.state.hands[self.human_id][idx]
                if self.service.play_card(curr_p, idx):
                    print(f"Discarded: {card.rank.name} of {card.suit.name}")
                    break
                print("Rejected by server.")
            else:
                print("Invalid index.")

    def _human_call(self):
        suits = list(Suit)
        print("\nChoose Trump Suit:")
        for i, s in enumerate(suits):
            print(f"[{i}] {s.name}")
        while True:
            s_idx = input("Suit number: ").strip()
            if s_idx.isdigit() and 0 <= int(s_idx) < len(suits):
                chosen_suit = suits[int(s_idx)]
                break
            print("Invalid choice.")

        ranks = list(Rank)
        print("\nChoose Called Card Rank:")
        for i, r in enumerate(ranks):
            print(f"[{i}] {r.name}")
        while True:
            r_idx = input("Rank number: ").strip()
            if r_idx.isdigit() and 0 <= int(r_idx) < len(ranks):
                chosen_rank = ranks[int(r_idx)]
                break
            print("Invalid choice.")

        self.service.make_call(chosen_suit, chosen_rank)
        print(f"\nYou called: {chosen_rank.name} of {chosen_suit.name}!")

    def dead_trick(self):
        print("\n" + "=" * 50)
        print("--- DEAD LOOP (Discard Phase) ---".center(50))
        print("=" * 50)

        while self.service.state.phase == Phase.DEAD_TRICK_PLAY:
            curr_p = self.service.state.turn.current_player
            if curr_p == self.human_id:
                self._human_discard(curr_p)
            else:
                bot = self.bots[curr_p]
                idx = bot.choose_discard(self.service.state)
                if self.service.play_card(curr_p, idx):
                    print(f"Player {curr_p} ({bot.__class__.__name__}) discarded.")
                else:
                    print(f"Bot {curr_p} logic error. Forcing fallback discard.")
                    self.service.play_card(curr_p, 0)

        if self.service.state.phase == Phase.DEAD_TRICK_CALL:
            c_id = self.service.state.call.caller_player
            if c_id is not None:
                if c_id == self.human_id:
                    self._human_call()
                else:
                    bot = self.bots[c_id]
                    suit, rank = bot.declare_trump_and_card(self.service.state)
                    self.service.make_call(suit, rank)
                    print(f"\nP{c_id} called: {rank.name} of {suit.name}!")

    def _handle_human_turn(self, curr_p: int):

        trick_idx = self.service.state.trick.index + 1
        trump = self.service.state.call.trump_suit
        if not self.service.state.trick.played:
            print(f"\n--- TRICK {trick_idx}/8 | Trump: {trump.name if trump else '??'} ---")
            print("Table is empty. You lead!")
        else:
            print("Table:")
            for pc in self.service.state.trick.played:
                print(f"  - P{pc.player_id}: {pc.card.rank.name} of {pc.card.suit.name}")

        self.display_hand()
        while True:
            choice = input("Your turn! Play card index: ").strip()
            if choice.isdigit():
                idx = int(choice)
                if 0 <= idx < len(self.service.state.hands[self.human_id]):
                    self.service.normal_trick_rounds(idx, curr_p)
                    break
                print("Invalid index.")
            else:
                print("Enter a number.")

    def run_tricks(self):
        print("\n" + "=" * 50)
        print("--- MAIN TRICKS ---".center(50))
        print("=" * 50)

        while self.service.state.phase == Phase.TRICK_PLAY:
            curr_p = self.service.state.turn.current_player
            if curr_p == self.human_id:
                self._handle_human_turn(curr_p)
            else:
                bot = self.bots[curr_p]
                idx = bot.play_card(self.service.state)
                card = self.service.state.hands[curr_p][idx]
                print(f"Player {curr_p} played: {card.rank.name} of {card.suit.name}")
                self.service.normal_trick_rounds(idx, curr_p)

        if self.service.state.phase == Phase.GAME_OVER:
            self.print_results()

    def print_results(self):
        print("\n" + "=" * 50)
        print("--- GAME OVER ---".center(50))
        print("=" * 50)
        self.service.end_game()
        res = self.service.state.team_points_if_known()
        if res:
            pts_team, pts_others = res
            target = self.service.state.call.target_points
            print(f"\nTarget: {target} | Team: {pts_team} | Defense: {pts_others}")
            msg = (
                " TEAM WINS!" if self.service.state.call.caller_team_won else " DEFENSE WINS!"
            )
            print(msg)

    def display_hand(self):
        hand = self.service.state.hands[self.human_id]
        print("\nYour Hand:")
        for i, c in enumerate(hand):
            print(f"[{i}] {c.rank.name} of {c.suit.name} ({c.points} pt)")
        print("-" * 40)

    def start_game(self):
        self.print_header("BRISCOLA IN 5 - SICILIANA")
        self.setup_bots()
        self.service.setup_game(dealer_id=4)
        self.run_action()
        self.dead_trick()
        self.run_tricks()


if __name__ == "__main__":
    CLI().start_game()
