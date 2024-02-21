import unittest
from game.player import Player
from game.deck import Deck


class FakeDeck:
    """A fake deck class for testing that simply returns a predetermined card."""

    def __init__(self, cards):
        self.cards = cards  # A list of cards to "deal" in order.

    def deal_card(self):
        return self.cards.pop(0)


class TestPlayer(unittest.TestCase):
    def test_player_initialization(self):
        player = Player(name="TestPlayer", balance=1000)
        self.assertEqual(player.name, "TestPlayer")
        self.assertEqual(player.balance, 1000)

    def test_player_betting(self):
        player = Player(balance=1000)
        player.place_bet(200)
        self.assertEqual(player.balance, 800)

    def test_player_hit(self):
        player = Player()
        deck = Deck()
        initial_card_count = len(player.cards)
        player.hit(deck)
        self.assertEqual(len(player.cards), initial_card_count + 1)

    def test_calculate_score(self):
        player = Player()
        player.cards = [1, 5, 10]  # Ace, 5, 10
        player.calculate_score()
        self.assertEqual(player.score, 16)

        player.cards = [1, 10]  # Ace, 10
        player.calculate_score()
        self.assertEqual(player.score, 21)

        player.cards = [1, 1, 1]  # Ace, Ace, Ace
        player.calculate_score()
        self.assertEqual(player.score, 13)

        player.cards = [10, 10, 10]  # 10, 10, 10
        player.calculate_score()
        self.assertEqual(player.score, 30)

        player.cards = [1, 1, 10]  # Ace, Ace, 10
        player.calculate_score()
        self.assertEqual(player.score, 12)

        player.cards = [1, 1, 10, 10]  # Ace, Ace, 10, 10
        player.calculate_score()
        self.assertEqual(player.score, 22)

    def test_display_hand(self):
        player = Player(name="TestPlayer")
        player.cards = [101, 202, 313]  # ♠A, ♥2, ♣K
        hand_representation = player.display_hand()
        self.assertEqual(hand_representation, "TestPlayer's hand: ♠A, ♥2, ♣K")

        player.cards = [110, 111, 112, 113]  # ♠10, ♠J, ♠Q, ♠K
        hand_representation = player.display_hand()
        self.assertEqual(hand_representation, "TestPlayer's hand: ♠10, ♠J, ♠Q, ♠K")

    def test_split(self):
        # Setup: Create a player with a hand that can be split and a fake deck.
        cards = [102, 102]  # Two Hearts, assuming 2 as the card value for simplicity.
        deck = FakeDeck(cards + [103, 104])  # Additional cards to draw after splitting.
        player = Player(name="Test Player", balance=100, id=1)
        player.hit(deck)  # Pre-set the player's hand to be splittable.
        player.hit(deck)  # Pre-set the player's hand to be splittable.
        player.place_bet(10)

        # Execute: Split the hand.
        split_hand = player.split(deck)

        # Verify: The original and split hands are correct.
        self.assertIsNotNone(split_hand, "Split hand should not be None.")
        self.assertEqual(len(player.cards), 2, "Original player should have 2 cards after splitting.")
        self.assertEqual(len(split_hand.cards), 2, "Split hand should have 2 cards.")
        self.assertEqual(player.cards[0], 102, "Original hand's first card should be 102.")
        self.assertEqual(split_hand.cards[0], 102, "Split hand's first card should be 102.")
        self.assertIn(split_hand.cards[1], [103, 104], "Split hand's second card should be one of the new cards.")
        self.assertEqual(player.balance, 80, "Player's balance should be adjusted for the bet.")
        self.assertEqual(player.id, split_hand.origin_player_number,
                         "Split hand should retain the origin player number.")

    def test_double_down(self):
        player = Player(name="TestPlayer", balance=1000)
        deck = Deck()
        player.cards = [1, 5]  # Ace, 5
        initial_balance = player.balance
        initial_card_count = len(player.cards)

        player.double_down(deck)

        self.assertEqual(player.balance, initial_balance - player.bet, "Player's balance should be adjusted for the bet.")
        self.assertEqual(len(player.cards), initial_card_count + 1, "Player should receive one additional card.")

        player.cards = [1, 5, 10]  # Ace, 5, 10
        initial_balance = player.balance
        initial_card_count = len(player.cards)

        player.double_down(deck)

        self.assertEqual(player.balance, initial_balance, "Player's balance should not change if double down is not allowed.")
        self.assertEqual(len(player.cards), initial_card_count, "Player's hand should not change if double down is not allowed.")

        player.cards = [1]  # Ace
        initial_balance = player.balance
        initial_card_count = len(player.cards)

        player.double_down(deck)

        self.assertEqual(player.balance, initial_balance, "Player's balance should not change if double down is not allowed.")
        self.assertEqual(len(player.cards), initial_card_count, "Player's hand should not change if double down is not allowed.")


if __name__ == '__main__':
    unittest.main()
