import os
import random
import sys
from collections import defaultdict
from typing import Dict, DefaultDict

from briscola5.application.game_service import GameService
from briscola5.bots.greedy_bot import GreedyBot
from briscola5.bots.random_bot import RandomBot
from briscola5.domain.state import Phase
from briscola5.bots.base import BaseBot  # Assumo che esista una base comune Bot


def generate_random_configuration():
    num_greedy = random.randint(0, 5)
    num_random = 5 - num_greedy

    bot_list = ["Random"] * num_random + ["Greedy"] * num_greedy
    random.shuffle(bot_list)

    bots: Dict[int, BaseBot] = {}
    bot_types: Dict[int, str] = {}

    for player_id, bot_type in enumerate(bot_list):
        if bot_type == "Random":
            bots[player_id] = RandomBot(player_id=player_id)
        else:
            bots[player_id] = GreedyBot(player_id=player_id)

        bot_types[player_id] = bot_type

    return bots, bot_types, num_greedy


# pylint: disable=too-many-locals, too-many-nested-blocks, too-many-branches, too-many-statements
def game(num_games: int = 1000, show_prints: bool = True):
    print("=" * 40)
    print(f"Bot VS Bot ({num_games} partite)")
    print("=" * 40)

    win_counts: DefaultDict[int, int] = defaultdict(int)
    bot_type_player_wins: DefaultDict[str, int] = defaultdict(int)
    bot_type_game_wins: DefaultDict[str, int] = defaultdict(int)
    config_stats: DefaultDict[int, int] = defaultdict(int)

    original_stdout = sys.stdout

    for game_idx in range(num_games):
        service = GameService()

        if not show_prints:
            # pylint: disable=consider-using-with
            sys.stdout = open(os.devnull, "w", encoding="utf-8")
        try:

            service.setup_game(dealer_id=game_idx % 5)
            bots, bot_types, num_greedy = generate_random_configuration()
            config_stats[num_greedy] += 1

            while service.state.phase == Phase.AUCTION:
                curr_player = service.state.turn.current_player
                bid = bots[curr_player].make_bid(service.state)
                service.auction_phase(curr_player, bid)

            while service.state.phase == Phase.DEAD_TRICK_PLAY:
                curr_player = service.state.turn.current_player
                bot = bots[curr_player]

                card_index = bot.choose_discard(service.state)
                success = service.play_card(curr_player, card_index)

                if not success and show_prints:
                    print(f"Mossa rifiutata per il P{curr_player}. Provo le altre carte")

                hand = service.state.hands[curr_player]
                fallback_indices = sorted(
                    [i for i in range(len(hand)) if i != card_index],
                    key=lambda idx, h=hand: h[idx].points
                )

                for fallback_idx in fallback_indices:
                    success = service.play_card(curr_player, fallback_idx)
                    if success and show_prints:
                        print(f"Mossa di accettata (indice {fallback_idx}).")
                    if success:
                        break

                if not success:
                    raise RuntimeError("Rifiutate tutte le carte in mano.")

            if service.state.phase == Phase.DEAD_TRICK_CALL:
                caller_id = service.state.call.caller_player
                suit, rank = bots[caller_id].declare_trump_and_card(service.state)
                service.make_call(suit, rank)

            max_turns = 100
            turns_played = 0
            while service.state.phase == Phase.TRICK_PLAY and turns_played < max_turns:
                curr_player = service.state.turn.current_player
                card_index = bots[curr_player].play_card(service.state)
                service.normal_trick_rounds(card_index, curr_player)
                turns_played += 1

            service.end_game()

            caller = service.state.call.caller_player
            partner = service.state.call.partner_player_internal
            team_a = [caller, partner] if partner is not None else [caller]

            winners = (
                team_a
                if service.state.call.caller_team_won
                else [p for p in range(5) if p not in team_a]
            )

            for w in winners:
                win_counts[w] += 1
                bot_type_player_wins[bot_types[w]] += 1

            greedy_winners = sum(1 for w in winners if bot_types[w] == "Greedy")
            random_winners = sum(1 for w in winners if bot_types[w] == "Random")

            if greedy_winners > random_winners:
                bot_type_game_wins["Greedy"] += 1
            elif random_winners > greedy_winners:
                bot_type_game_wins["Random"] += 1
            else:
                bot_type_game_wins["Tie"] += 1
        # pylint: disable=broad-exception-caught
        except Exception as e:
            sys.stdout = original_stdout
            print(f"Errore alla partita {game_idx}: {e}")
            continue
        finally:
            if not show_prints:
                sys.stdout = original_stdout

    print("\nStatistiche configurazioni: ")
    for g in sorted(config_stats.keys()):
        print(f"{g} Greedy vs {5-g} Random: {config_stats[g]} partite")

    print("\nVittorie per giocatore")
    for p in sorted(win_counts.keys()):
        print(f"Player {p}: {win_counts[p]} vittorie")

    print("\n[ Vittorie random e bot ]")
    for t, cnt in bot_type_player_wins.items():
        print(f"{t}: {cnt} punti vittoria totali")

    print("\n[ Vittorie a livello di partita: ]")
    for t in ["Greedy", "Random", "Tie"]:
        cnt = bot_type_game_wins[t]
        perc = (cnt / num_games) * 100
        print(f"{t}: {cnt} ({perc:.1f}%)")

    print("=" * 40)


if __name__ == "__main__":
    game(num_games=1000, show_prints=True)
