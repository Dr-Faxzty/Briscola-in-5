from __future__ import annotations

from unittest.mock import patch

from briscola5.application.game_service import GameService
from briscola5.domain.card import Rank, Suit
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
        bid_value = 65

        service.auction_phase(player_id=1, offer=bid_value)

        assert service.state.auction.last_bid == bid_value
        assert service.state.auction.last_bidder == 1
        assert service.state.turn.current_player == 2

    def test_full_flow_until_call(self):
        """Verify the complete flow: Auction -> Dead Trick Play -> Call."""
        service = GameService()
        service.setup_game(dealer_id=0)

        service.auction_phase(1, 80)
        service.auction_phase(2, None)
        service.auction_phase(3, None)
        service.auction_phase(4, None)
        service.auction_phase(0, None)

        assert service.state.phase == Phase.DEAD_TRICK_PLAY

        for p_id in [1, 2, 3, 4, 0]:
            service.play_card(p_id, 0)

        assert service.state.phase == Phase.DEAD_TRICK_CALL
        assert len(service.state.trick.played) == 5

        service.make_call(Suit.ORO, Rank.ASSO)

        assert service.state.phase == Phase.TRICK_PLAY
        assert service.state.call.trump_suit == Suit.ORO
        assert service.state.call.called_card.rank == Rank.ASSO

    def test_auction_concludes_to_dead_trick_play(self):
        """Verify that auction conclusion leads to DEAD_TRICK_PLAY phase."""
        service = GameService()
        service.setup_game(dealer_id=0)

        service.auction_phase(1, 65)
        service.auction_phase(2, None)
        service.auction_phase(3, 75)
        service.auction_phase(4, None)
        service.auction_phase(0, None)
        service.auction_phase(1, None)

        assert service.state.phase == Phase.DEAD_TRICK_PLAY
        assert service.state.call.caller_player == 3
        assert service.state.call.target_points == 75

    def test_play_card_wrong_turn(self):
        """Verify that playing a card out of turn is rejected."""
        service = GameService()
        service.setup_game(dealer_id=0)
        service.state.phase = Phase.DEAD_TRICK_PLAY
        service.state.turn.current_player = 1

        service.play_card(player_id=2, card_index=0)

        assert len(service.state.trick.played) == 0
        assert len(service.state.hands[2]) == 8

    def test_make_call_reveals_partner_in_first_round(self):
        """Verify that the partner is identified if they played the called card in round 1."""
        service = GameService()
        service.setup_game(dealer_id=0)

        service.state.phase = Phase.DEAD_TRICK_CALL
        from briscola5.domain.card import Card
        from briscola5.domain.trick import PlayedCard

        called_card = Card(Suit.ORO, Rank.ASSO)
        service.state.trick.played = [
            PlayedCard(1, Card(Suit.ORO, Rank.RE)),
            PlayedCard(2, called_card),
            PlayedCard(3, Card(Suit.COPPE, Rank.DUE)),
            PlayedCard(4, Card(Suit.SPADE, Rank.TRE)),
            PlayedCard(0, Card(Suit.BASTONI, Rank.SETTE)),
        ]

        service.make_call(Suit.ORO, Rank.ASSO)

        assert service.state.call.partner_player_internal == 2
        assert service.state.call.partner_revealed is True
