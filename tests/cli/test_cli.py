from unittest.mock import patch

from briscola5.cli.base_cli import CLI
from briscola5.domain.state import Phase


class Player:
    def __init__(self):
        self.card_attempt = 0

    def __call__(self, prompt):
        text = str(prompt).lower()

        if "1 or 2" in text:
            return "1"
        elif "press enter" in text:
            return ""
        elif "bid" in text:
            return "120"
        elif "seed" in text:
            return "0"
        elif "card number" in text:
            return "0"
        else:
            valore = str(self.card_attempt % 8)
            self.card_attempt += 1
            return valore


@patch("builtins.input", side_effect=Player())
@patch("os.system")
@patch("builtins.print")
def test_cli(mock_print, mock_os_system, mock_input):
    cli = CLI(player_id=0)
    cli.start_game()
    assert cli.service.state.phase == Phase.GAME_OVER
