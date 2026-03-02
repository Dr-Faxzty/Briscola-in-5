from __future__ import annotations

from unittest.mock import patch

from briscola5.application.game_service import GameService
from briscola5.domain.card import Card, Rank, Suit
from briscola5.domain.state import Phase


class TestGameService:
    """Test suite for the GameService orchestration logic."""

    def test_setup_game_initializes_correctly(self):
        """Verify that the game starts with the correct hands and initial phase."""
        service = GameService()
        dealer_id = 0

        with patch("random.shuffle"):
            service.setup_game(dealer_id=dealer_id)

        assert service.state.phase == Phase.AUCTION
        assert service.state.turn.dealer_player == dealer_id
        assert service.state.turn.current_player == 1

        for i in range(5):
            assert len(service.state.hands[i]) == 8

    def test_auction_bid_updates_state(self):
        """Verify that a valid bid updates the auction state."""
        service = GameService()
        service.setup_game(dealer_id=0)
        bid_value = 75

        service.auction_phase(player_id=1, offer=bid_value)

        assert service.state.auction.last_bid == bid_value
        assert service.state.auction.last_bidder == 1
        assert service.state.turn.current_player == 2

    def test_full_flow_to_game_over(self):
        """Verify the complete flow from Auction to Game Over."""
        service = GameService()
        service.setup_game(dealer_id=0)

        service.auction_phase(1, 80)
        for p in [2, 3, 4, 0]:
            service.auction_phase(p, None)
        assert service.state.phase == Phase.DEAD_TRICK_PLAY

        for p_id in [1, 2, 3, 4, 0]:
            service.play_card(p_id, 0)
        assert service.state.phase == Phase.DEAD_TRICK_CALL

        service.make_call(Suit.ORO, Rank.ASSO)
        assert service.state.phase == Phase.TRICK_PLAY

        for _ in range(5):
            p_to_play = service.state.turn.current_player
            service.normal_trick_rounds(0, p_to_play)

        assert service.state.trick.index == 2

        assert len(service.state.hands[0]) == 6

    def test_rotation_with_skipped_players(self):
        """Make sure the turn skips whoever passes and returns to P1 if P0 passes."""
        service = GameService()
        service.setup_game(dealer_id=0)

        service.auction_phase(1, 75)
        service.auction_phase(2, None)
        service.auction_phase(3, 80)
        service.auction_phase(4, 85)
        service.auction_phase(0, None)

        assert service.state.turn.current_player == 1

    def test_auction_all_pass_logic(self):
        """Test the case where almost everyone passes immediately."""
        service = GameService()
        service.setup_game(dealer_id=0)

        service.auction_phase(1, 75)
        service.auction_phase(2, None)
        service.auction_phase(3, None)
        service.auction_phase(4, None)
        service.auction_phase(0, None)

        assert service.state.phase == Phase.DEAD_TRICK_PLAY
        assert service.state.call.caller_player == 1

    def test_error_branches_coverage(self, capsys):

        service = GameService()
        service.setup_game(dealer_id=0)

        service.auction_phase(player_id=3, offer=70)

        service.auction_phase(1, 75)
        service.auction_phase(2, 70)

        service.play_card(player_id=4, card_index=0)

        service.make_call(Suit.ORO, Rank.ASSO)

        captured = capsys.readouterr()
        assert "Error" in captured.out

    def test_partner_reveal_mid_game(self):
        """Check the partner's discovery and the end of the game."""
        service = GameService()
        service.setup_game(dealer_id=0)

        service.state.call.caller_player = 0
        service.state.call.target_points = 71

        service.state.phase = Phase.TRICK_PLAY
        service.state.call.trump_suit = Suit.ORO
        service.state.call.called_card = Card(Suit.ORO, Rank.ASSO)
        service.state.call.partner_revealed = False

        for i in range(5):
            service.state.hands[i] = [Card(Suit.COPPE, Rank.DUE)]

        service.state.hands[2] = [Card(Suit.ORO, Rank.ASSO)]
        service.state.turn.current_player = 0

        for _ in range(5):
            curr = service.state.turn.current_player
            service.normal_trick_rounds(0, curr)

        assert service.state.call.partner_revealed is True
        assert service.state.phase == Phase.GAME_OVER

        service.end_game()

    def test_show_hand_output(self, capsys):
        """Verify that show_hand prints correctly using actual Card repr."""
        service = GameService()
        service.state.hands[0] = [Card(Suit.ORO, Rank.ASSO)]
        service.show_hand(0)
        captured = capsys.readouterr()
        assert "0: Card(oro,A)" in captured.out
