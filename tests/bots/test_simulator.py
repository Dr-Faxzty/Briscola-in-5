import os
import sys
from unittest.mock import patch

import pytest

from briscola5.bots.simulator import game, generate_random_configuration


def test_generate_random_configuration():
    bots, bot_types, num_greedy = generate_random_configuration()

    assert len(bots) == 5
    assert len(bot_types) == 5
    assert 0 <= num_greedy <= 5

    for p_id, bot_type in bot_types.items():
        assert bot_type in ["Greedy", "Random"]


def test_game_execution():
    original_stdout = sys.stdout
    sys.stdout = open(os.devnull, "w")

    try:
        game(num_games=1, show_prints=False)
    except Exception as e:
        sys.stdout = original_stdout
        pytest.fail(f"game crash: {e}")
    finally:
        sys.stdout = original_stdout
