from briscola5.application.game_service import GameService
from briscola5.bots.random_bot import RandomBot
from briscola5.domain.state import Phase


def test_game_with_random_bots():
    service = GameService()
    service.setup_game(dealer_id=0)

    bots = {i: RandomBot(player_id=i) for i in range(5)}

    while service.state.phase == Phase.AUCTION:
        curr_player = service.state.turn.current_player
        bot = bots[curr_player]
        bid = bot.make_bid(service.state)
        service.auction_phase(curr_player, bid)

    while service.state.phase == Phase.DEAD_TRICK_PLAY:
        curr_player = service.state.turn.current_player
        bot = bots[curr_player]
        card_index = bot.choose_discard(service.state)
        service.play_card(curr_player, card_index)

    if service.state.phase == Phase.DEAD_TRICK_CALL:
        caller_id = service.state.call.caller_player
        bot = bots[caller_id]
        suit, rank = bot.declare_trump_and_card(service.state)
        service.make_call(suit, rank)

    max_turn = 40
    turn_played = 0

    while service.state.phase == Phase.TRICK_PLAY and turn_played < max_turn:
        curr_player = service.state.turn.current_player
        bot = bots[curr_player]
        card_index = bot.play_card(service.state)
        service.normal_trick_rounds(card_index, curr_player)
        turn_played += 1

    assert service.state.phase == Phase.GAME_OVER, "Partita non terminata correttamente"

    service.end_game()
    assert service.state.call.caller_team_won is not None
