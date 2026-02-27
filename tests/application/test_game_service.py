from unittest.mock import patch

import pytest

from briscola5.application.game_service import GameService
from briscola5.domain.state import Phase


class TestGameService:

    def test_setup_game_initializes_correctly(self):

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

        service = GameService()
        service.setup_game(dealer_id=0)
        bid_value = 65

        service.auction_phase(player_id=1, offer=bid_value)

        assert service.state.auction.last_bid == bid_value
        assert service.state.auction.last_bidder == 1
        assert service.state.turn.current_player == 2

    def test_full_auction_flow_coverage(self):

        service = GameService()
        service.setup_game(dealer_id=4)

        service.auction_phase(0, 65)
        service.auction_phase(1, 70)
        service.auction_phase(2, None)
        service.auction_phase(3, 60)

        service.auction_phase(3, None)
        service.auction_phase(4, None)
        service.auction_phase(0, None)

        assert service.state.phase == Phase.DEAD_TRICK_CALL
        assert service.state.call.caller_player == 1

    def test_auction_pass_updates_passed_list(self):

        service = GameService()
        service.setup_game(dealer_id=0)

        service.auction_phase(player_id=1, offer=None)

        assert service.state.auction.passed[1] is True
        assert service.state.turn.current_player == 2

    def test_auction_concludes_correctly(self):

        service = GameService()
        service.setup_game(dealer_id=0)

        service.auction_phase(1, 65)
        service.auction_phase(2, None)
        service.auction_phase(3, 75)
        service.auction_phase(4, None)
        service.auction_phase(0, None)
        service.auction_phase(1, None)

        assert service.state.phase == Phase.DEAD_TRICK_CALL
        assert service.state.call.caller_player == 3
        assert service.state.call.target_points == 75

    def test_auction_invalid_bid_too_low(self):

        service = GameService()
        service.setup_game(dealer_id=0)
        service.auction_phase(1, 70)

        service.auction_phase(2, 65)

        assert service.state.auction.last_bid == 70
        assert service.state.auction.last_bidder == 1
        assert service.state.turn.current_player == 2

    def test_auction_wrong_player_turn(self):

        service = GameService()
        service.setup_game(dealer_id=0)

        service.auction_phase(2, 80)

        assert service.state.auction.last_bid is None
        assert service.state.turn.current_player == 1
