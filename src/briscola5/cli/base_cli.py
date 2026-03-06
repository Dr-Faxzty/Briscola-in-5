import os
from typing import Any

from briscola5.application.game_service import GameService
from briscola5.bots.greedy_bot import GreedyBot
from briscola5.bots.random_bot import RandomBot
from briscola5.domain.card import Rank, Suit
from briscola5.domain.state import Phase


class Col:
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


class CLI:
    def __init__(self, player_id: int = 0):
        self.service = GameService()
        self.human_id = player_id
        self.bots: dict[int, Any] = {}

    def clear_screen(self):
        os.system("cls" if os.name == "nt" else "clear")

    def print_header(self, title: str):
        self.clear_screen()
        print(f"{Col.CYAN}{Col.BOLD}" + "=" * 50)
        print(f" {title.center(48)} ")
        print("=" * 50 + f"{Col.RESET}")

    def setup_bots(self):
        print(f"\n{Col.YELLOW}--- CHOOSE YOUR OPPONENTS ---{Col.RESET}")
        print(f"  {Col.GREEN}1.{Col.RESET} 4 x RandomBot {Col.CYAN}(Random Moves){Col.RESET}")
        print(f"  {Col.GREEN}2.{Col.RESET} 4 x GreedyBot {Col.CYAN}(Strategy){Col.RESET}\n")

        while True:
            choice = input(f"Choose {Col.GREEN}1{Col.RESET} or {Col.GREEN}2{Col.RESET}: ").strip()
            if choice in ["1", "2"]:
                break
            print(f"{Col.RED}[!] Invalid input. Choose 1 or 2.{Col.RESET}")

        bot_class: type[Any]
        if choice == "1":
            bot_class = RandomBot
            print(f"\n{Col.GREEN}[+] You chose Level 1: Playing with 4 RandomBots.{Col.RESET}")
        else:
            bot_class = GreedyBot
            print(f"\n{Col.GREEN}[+] You chose Level 2: Playing with 4 GreedyBots.{Col.RESET}")

        for i in range(5):
            if i != self.human_id:
                self.bots[i] = bot_class(player_id=i)

        input(f"\n{Col.BOLD}Press ENTER to start the game...{Col.RESET}")

    def _handle_human_bid(self, minimum: int, current: int):
        self.display_hand()
        while True:
            prompt = (
                f"{Col.YELLOW}> Your turn! Enter a bid ({minimum}-120) or 'pass': {Col.RESET}"
            )
            choice = input(prompt).strip().lower()

            if choice == "pass":
                self.service.auction_phase(self.human_id, None)
                print(f"{Col.RED}You passed.{Col.RESET}")
                break
            if choice.isdigit():
                bid_val = int(choice)
                if 71 <= bid_val <= 120 and (current == 0 or bid_val > current):
                    self.service.auction_phase(self.human_id, bid_val)
                    print(f"{Col.GREEN}You offered: {bid_val}{Col.RESET}")
                    break
                print(f"{Col.RED}[!] Offer must be between {minimum} and 120.{Col.RESET}")
            else:
                print(f"{Col.RED}[!] Unrecognized input.{Col.RESET}")

    def run_action(self):
        print(f"\n{Col.MAGENTA}{Col.BOLD}--- AUCTION STARTS ---{Col.RESET}")

        while self.service.state.phase == Phase.AUCTION:
            curr_p = self.service.state.turn.current_player
            curr_bid = self.service.state.auction.last_bid or 0

            if curr_p == self.human_id:
                self._handle_human_bid(max(71, curr_bid + 1), curr_bid)
            else:
                bot = self.bots[curr_p]
                bid = bot.make_bid(self.service.state)
                self.service.auction_phase(curr_p, bid)
                if bid is None:
                    msg = f"{Col.RED}PASSED{Col.RESET}"
                else:
                    msg = f"{Col.GREEN}OFFERED {bid}{Col.RESET}"
                print(f"Player {curr_p} ({bot.__class__.__name__}) -> {msg}")

        caller = self.service.state.call.caller_player
        target = self.service.state.call.target_points
        print(f"\n{Col.MAGENTA}--- AUCTION ENDED ---{Col.RESET}")
        print(
            f"Caller: {Col.BOLD}Player {caller}{Col.RESET} | "
            f"Target: {Col.BOLD}{Col.YELLOW}{target} pt{Col.RESET}"
        )

    def _human_discard(self, curr_p: int):
        self.display_hand()
        while True:
            choice = input(
                f"{Col.YELLOW}> Your turn! Index to discard [0-7]: {Col.RESET}"
            ).strip()
            if not choice.isdigit():
                print(f"{Col.RED}[!] Enter a number.{Col.RESET}")
                continue
            idx = int(choice)
            if 0 <= idx < len(self.service.state.hands[self.human_id]):
                card = self.service.state.hands[self.human_id][idx]
                if self.service.play_card(curr_p, idx):
                    print(
                        f"{Col.GREEN}[+] Discarded:{Col.RESET} "
                        f"{card.rank.name} of {card.suit.name}"
                    )
                    break
                print(f"{Col.RED}[!] Rejected by server.{Col.RESET}")
            else:
                print(f"{Col.RED}[!] Invalid index.{Col.RESET}")

    def _human_call(self):
        suits = list(Suit)
        print(f"\n{Col.CYAN}--- Choose Trump Suit ---{Col.RESET}")
        for i, s in enumerate(suits):
            print(f"  [{Col.GREEN}{i}{Col.RESET}] {s.name}")
        while True:
            s_idx = input(f"{Col.YELLOW}Suit number: {Col.RESET}").strip()
            if s_idx.isdigit() and 0 <= int(s_idx) < len(suits):
                chosen_suit = suits[int(s_idx)]
                break
            print(f"{Col.RED}[!] Invalid choice.{Col.RESET}")

        ranks = list(Rank)
        print(f"\n{Col.CYAN}--- Choose Called Card Rank ---{Col.RESET}")
        for i, r in enumerate(ranks):
            print(f"  [{Col.GREEN}{i}{Col.RESET}] {r.name}")
        while True:
            r_idx = input(f"{Col.YELLOW}Rank number: {Col.RESET}").strip()
            if r_idx.isdigit() and 0 <= int(r_idx) < len(ranks):
                chosen_rank = ranks[int(r_idx)]
                break
            print(f"{Col.RED}[!] Invalid choice.{Col.RESET}")

        self.service.make_call(chosen_suit, chosen_rank)
        print(
            f"\n{Col.MAGENTA}[!] You called: "
            f"{Col.BOLD}{chosen_rank.name} of {chosen_suit.name}!{Col.RESET}"
        )

    def dead_trick(self):
        print(f"\n{Col.BLUE}" + "=" * 50)
        print("--- DEAD LOOP (Discard Phase) ---".center(50))
        print("=" * 50 + f"{Col.RESET}")

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
                    print(
                        f"{Col.RED}[!] Bot {curr_p} error. Forcing fallback discard.{Col.RESET}"
                    )
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
                    print(
                        f"\n{Col.MAGENTA}[!] Player {c_id} called: "
                        f"{Col.BOLD}{rank.name} of {suit.name}!{Col.RESET}"
                    )

    def _handle_human_turn(self, curr_p: int):
        trick_idx = self.service.state.trick.index + 1
        trump = self.service.state.call.trump_suit
        trump_str = trump.name if trump else "??"

        print(
            f"\n{Col.CYAN}--- TRICK {trick_idx}/8 | "
            f"Trump: {Col.BOLD}{trump_str}{Col.RESET}{Col.CYAN} ---{Col.RESET}"
        )

        if not self.service.state.trick.played:
            print(f"{Col.YELLOW}Table is empty. You lead!{Col.RESET}")
        else:
            print(f"{Col.BOLD}Table:{Col.RESET}")
            for pc in self.service.state.trick.played:
                print(
                    f"  - Player {pc.player_id}: {Col.YELLOW}{pc.card.rank.name}{Col.RESET} "
                    f"of {Col.CYAN}{pc.card.suit.name}{Col.RESET}"
                )

        self.display_hand()
        while True:
            choice = input(f"{Col.YELLOW}> Your turn! Play card index: {Col.RESET}").strip()
            if choice.isdigit():
                idx = int(choice)
                if 0 <= idx < len(self.service.state.hands[self.human_id]):
                    self.service.normal_trick_rounds(idx, curr_p)
                    break
                print(f"{Col.RED}[!] Invalid index.{Col.RESET}")
            else:
                print(f"{Col.RED}[!] Enter a number.{Col.RESET}")

    def run_tricks(self):
        print(f"\n{Col.GREEN}" + "=" * 50)
        print("--- MAIN TRICKS ---".center(50))
        print("=" * 50 + f"{Col.RESET}")

        while self.service.state.phase == Phase.TRICK_PLAY:
            curr_p = self.service.state.turn.current_player
            if curr_p == self.human_id:
                self._handle_human_turn(curr_p)
            else:
                bot = self.bots[curr_p]
                idx = bot.play_card(self.service.state)
                card = self.service.state.hands[curr_p][idx]
                print(
                    f"Player {curr_p} played: {Col.YELLOW}{card.rank.name}{Col.RESET} "
                    f"of {Col.CYAN}{card.suit.name}{Col.RESET}"
                )
                self.service.normal_trick_rounds(idx, curr_p)

        if self.service.state.phase == Phase.GAME_OVER:
            self.print_results()

    def print_results(self):
        print(f"\n{Col.MAGENTA}{Col.BOLD}" + "=" * 50)
        print("--- GAME OVER ---".center(50))
        print("=" * 50 + f"{Col.RESET}")

        self.service.end_game()
        res = self.service.state.team_points_if_known()

        if res:
            pts_team, pts_others = res
            target = self.service.state.call.target_points or 61

            team_col = Col.GREEN if pts_team >= target else Col.RED
            def_col = Col.GREEN if pts_others > (120 - target) else Col.RED

            print(f"\nTarget: {Col.BOLD}{target}{Col.RESET}")
            print(f"Team Points: {Col.BOLD}{team_col}{pts_team}{Col.RESET}")
            print(f"Defense Points: {Col.BOLD}{def_col}{pts_others}{Col.RESET}\n")

            if self.service.state.call.caller_team_won:
                print(f"{Col.GREEN}{Col.BOLD}*** TEAM WINS! ***{Col.RESET}")
            else:
                print(f"{Col.RED}{Col.BOLD}*** DEFENSE WINS! ***{Col.RESET}")
        print("\n")

    def display_hand(self):
        hand = self.service.state.hands[self.human_id]
        hand.sort(key=lambda c: (c.suit.value, -c.strength))

        print(f"\n{Col.CYAN}" + "-" * 40)
        print(f"{Col.BOLD}Your Hand:{Col.RESET}")
        print(f"{Col.CYAN}" + "-" * 40 + f"{Col.RESET}")

        for i, c in enumerate(hand):
            pts_str = f"{c.points} pt"
            pts_color = Col.GREEN if c.points > 0 else Col.RESET
            print(
                f" [{Col.YELLOW}{i}{Col.RESET}] {c.rank.name:7} of {c.suit.name:8} "
                f"{pts_color}({pts_str:>5}){Col.RESET}"
            )

        print(f"{Col.CYAN}" + "-" * 40 + f"{Col.RESET}")

    def start_game(self):
        self.print_header("BRISCOLA IN 5 - SICILIANA")
        self.setup_bots()
        self.service.setup_game(dealer_id=4)
        self.run_action()
        self.dead_trick()
        self.run_tricks()


if __name__ == "__main__":
    CLI().start_game()
