from briscola5.bots.greedy_bot import GreedyBot
from briscola5.domain.card import Card, Rank, Suit
from briscola5.domain.state import GameState, PlayedCard


def test_make_bid_weak_hand_returns_none():
    bot = GreedyBot(player_id=1)
    state = GameState()
    state.hands[1] = [Card(Suit.ORO, Rank.DUE), Card(Suit.COPPE, Rank.QUATTRO)]
    state.auction.last_bid = 71
    bid = bot.make_bid(state)
    assert bid is None or bid >= state.auction.last_bid + 1


def test_make_bid_strong_hand_returns_higher_than_current():
    bot = GreedyBot(player_id=1)
    state = GameState()
    state.hands[1] = [
        Card(Suit.ORO, Rank.ASSO),
        Card(Suit.ORO, Rank.TRE),
        Card(Suit.COPPE, Rank.RE),
        Card(Suit.SPADE, Rank.TRE),
    ]
    state.auction.last_bid = 71
    bid = bot.make_bid(state)
    assert bid is not None
    assert bid >= state.auction.last_bid + 1
    assert bid <= 120


def test_make_bid_over_120_returns_none():
    bot = GreedyBot(player_id=1)
    state = GameState()
    state.hands[1] = [
        Card(Suit.ORO, Rank.ASSO),
        Card(Suit.ORO, Rank.TRE),
        Card(Suit.COPPE, Rank.RE),
        Card(Suit.SPADE, Rank.TRE),
    ]
    state.auction.last_bid = 120
    bid = bot.make_bid(state)
    assert bid is None


def test_choose_discard_naked_high_card():
    bot = GreedyBot(player_id=2)
    state = GameState()
    state.hands[2] = [
        Card(Suit.SPADE, Rank.ASSO),
        Card(Suit.ORO, Rank.DUE),
        Card(Suit.ORO, Rank.QUATTRO),
    ]
    discard = bot.choose_discard(state)
    assert discard == 0


def test_choose_discard_normal():
    bot = GreedyBot(player_id=2)
    state = GameState()
    state.hands[2] = [Card(Suit.SPADE, Rank.DUE), Card(Suit.ORO, Rank.QUATTRO)]
    discard = bot.choose_discard(state)
    assert discard in [0, 1]


def test_declare_trump_and_card_returns_most_common_suit():
    bot = GreedyBot(player_id=3)
    state = GameState()
    state.hands[3] = [
        Card(Suit.COPPE, Rank.TRE),
        Card(Suit.COPPE, Rank.DUE),
        Card(Suit.SPADE, Rank.RE),
    ]
    suit, rank = bot.declare_trump_and_card(state)
    assert suit == Suit.COPPE
    assert rank in [Rank.ASSO, Rank.TRE, Rank.RE, Rank.CAVALLO, Rank.DONNA]


def test_play_card_first_turn_plays_weakest():
    bot = GreedyBot(player_id=4)
    state = GameState()
    state.hands[4] = [Card(Suit.BASTONI, Rank.ASSO), Card(Suit.BASTONI, Rank.DUE)]
    state.trick.played = []
    state.call.trump_suit = Suit.SPADE
    card_idx = bot.play_card(state)
    assert card_idx in [0, 1]


def test_play_card_beat_winning_card():
    bot = GreedyBot(player_id=4)
    state = GameState()
    state.hands[4] = [Card(Suit.SPADE, Rank.TRE), Card(Suit.ORO, Rank.DUE)]
    state.call.trump_suit = Suit.SPADE
    pc = PlayedCard(player_id=1, card=Card(Suit.COPPE, Rank.ASSO))
    state.trick.played = [pc]
    card_idx = bot.play_card(state)
    assert card_idx == 0


def test_play_card_cannot_beat_plays_weakest():
    bot = GreedyBot(player_id=4)
    state = GameState()
    state.hands[4] = [Card(Suit.ORO, Rank.DUE)]
    state.call.trump_suit = Suit.SPADE
    pc = PlayedCard(player_id=1, card=Card(Suit.SPADE, Rank.ASSO))
    state.trick.played = [pc]
    card_idx = bot.play_card(state)
    assert card_idx == 0
