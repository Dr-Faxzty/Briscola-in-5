import pytest

from briscola5.domain.state import PLAYER_COUNT, GameState, Phase


def test_initial_state_defaults() -> None:
    state = GameState()

    assert state.phase == Phase.AUCTION

    assert state.turn.current_player == 0
    assert state.turn.dealer_player == 0

    assert len(state.hands) == PLAYER_COUNT
    for hand in state.hands:
        assert hand == []

    assert state.auction.start_player == 0
    assert state.auction.current_player == 0
    assert state.auction.last_bid is None
    assert state.auction.last_bidder is None
    assert state.auction.passed == [False] * PLAYER_COUNT

    assert state.trick.played == []
    assert state.trick.index == 0
    assert not state.trick.is_complete()

    assert state.call.caller_player is None
    assert state.call.target_points is None
    assert state.call.trump_suit is None
    assert state.call.called_card is None
    assert state.call.partner_player_internal is None
    assert state.call.partner_revealed is False
    assert state.call.caller_team_won is None

    assert state.score.player_points == [0] * PLAYER_COUNT
    for won in state.score.won_cards:
        assert won == []


def test_assert_player_id_valid() -> None:
    state = GameState()
    state.assert_player_id(0)
    state.assert_player_id(PLAYER_COUNT - 1)


def test_assert_player_id_invalid_raises() -> None:
    state = GameState()
    with pytest.raises(ValueError):
        state.assert_player_id(-1)
    with pytest.raises(ValueError):
        state.assert_player_id(PLAYER_COUNT)


def test_remaining_cards_in_hand() -> None:
    state = GameState()
    assert state.remaining_cards_in_hand(0) == 0


def test_current_trick_is_complete() -> None:
    state = GameState()

    assert not state.current_trick_is_complete()

    state.trick.played = [object()] * PLAYER_COUNT
    assert state.current_trick_is_complete()


def test_team_points_if_unknown_returns_none() -> None:
    state = GameState()
    state.call.caller_player = 0
    assert state.team_points_if_known() is None


def test_team_points_if_known() -> None:
    state = GameState()

    state.call.caller_player = 0
    state.call.partner_player_internal = 2

    state.score.player_points[0] = 30
    state.score.player_points[2] = 40
    state.score.player_points[1] = 10
    state.score.player_points[3] = 5
    state.score.player_points[4] = 5

    caller_team, others = state.team_points_if_known()
    assert caller_team == 70
    assert others == 20


def test_is_game_over() -> None:
    state = GameState()
    assert not state.is_game_over()

    state.phase = Phase.GAME_OVER
    assert state.is_game_over()


def test_repr_does_not_crash() -> None:
    state = GameState()
    text = repr(state)
    assert "GameState(" in text
