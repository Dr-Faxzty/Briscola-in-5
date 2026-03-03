from collections import Counter

from briscola5.bots.base import BaseBot
from briscola5.domain.card import Card, Rank, Suit
from briscola5.domain.state import GameState


def evaluate_trump_suit(hand: list[Card], suit: Suit) -> float:
    cards = [c for c in hand if c.suit == suit]
    count = len(cards)

    points = sum(c.points for c in cards)
    strength_score = sum(c.strength for c in cards)
    length_bonus = count * 2

    has_ace = any(c.rank == Rank.ASSO for c in cards)
    has_three = any(c.rank == Rank.TRE for c in cards)
    combo_bonus = 5 if has_ace and has_three else 0

    return points + length_bonus + combo_bonus + strength_score * 0.2


def estimate_hand_strength(hand: list[Card]) -> float:
    base_points = sum(c.points for c in hand)
    best_trump_value = max(evaluate_trump_suit(hand, s) for s in Suit)
    return base_points + best_trump_value


def max_bid(strength: float) -> int:
    s_min = 15.0
    s_max = 80.0
    normalized = (strength - s_min) / (s_max - s_min)
    normalized = max(0.0, min(1.0, normalized))
    bid = 71 + normalized * (120 - 71)
    return int(round(bid))


def choose_bid(hand: list[Card], current_bid: int) -> int | None:
    strength = estimate_hand_strength(hand)
    bid = max_bid(strength)

    if current_bid >= bid:
        return None
    return max(current_bid + 1, 71)


class GreedyBot(BaseBot):

    def make_bid(self, state: GameState) -> int | None:
        hand = state.hands[self.player_id]
        current_bid = state.auction.last_bid if state.auction.last_bid is not None else 70
        return choose_bid(hand, current_bid)

    def choose_discard(self, state: GameState) -> int:
        hand = state.hands[self.player_id]
        suit_counts = Counter(card.suit for card in hand)
        dangerous_ranks = [Rank.ASSO, Rank.TRE, Rank.RE]

        naked_high_cards = [
            i
            for i, card in enumerate(hand)
            if suit_counts[card.suit] == 1 and card.rank in dangerous_ranks
        ]
        if naked_high_cards:
            return max(naked_high_cards, key=lambda i: hand[i].strength)

        return min(range(len(hand)), key=lambda i: (hand[i].points, hand[i].strength))

    def declare_trump_and_card(self, state: GameState) -> tuple[Suit, Rank]:
        hand = state.hands[self.player_id]
        suit_counts = Counter(card.suit for card in hand)
        best_suit = suit_counts.most_common(1)[0][0]

        ranks_in_hand = [card.rank for card in hand if card.suit == best_suit]
        call_priority = [Rank.ASSO, Rank.TRE, Rank.RE, Rank.CAVALLO, Rank.DONNA]

        target_rank = Rank.ASSO
        for rank in call_priority:
            if rank not in ranks_in_hand:
                target_rank = rank
                break

        return best_suit, target_rank

    def play_card(self, state: GameState) -> int:
        hand = state.hands[self.player_id]
        played = state.trick.played
        trump_suit = state.call.trump_suit

        if not played:

            return min(range(len(hand)), key=lambda i: (hand[i].points, hand[i].strength))

        winning_card = played[0].card
        for pc in played[1:]:
            c = pc.card
            if c.suit == trump_suit and winning_card.suit != trump_suit:
                winning_card = c
            elif c.suit == winning_card.suit and c.strength > winning_card.strength:
                winning_card = c

        beating_indices = [
            i
            for i, card in enumerate(hand)
            if (card.suit == trump_suit and winning_card.suit != trump_suit)
            or (card.suit == winning_card.suit and card.strength > winning_card.strength)
        ]

        trick_points = sum(pc.card.points for pc in played)

        if trick_points >= 10 and beating_indices:
            return min(beating_indices, key=lambda i: hand[i].strength)

        return min(range(len(hand)), key=lambda i: (hand[i].points, hand[i].strength))
