import unittest
from game.deck import Deck  # Adjust the import path based on your project structure


class TestDeck(unittest.TestCase):
    def test_deck_initialization(self):
        """Test that the deck initializes with the correct number of cards including the plastic card."""
        for num_decks in range(6, 9):  # Testing for 6 to 8 decks
            deck = Deck(num_decks)
            expected_card_count = num_decks * 52   # 52 cards per deck
            self.assertEqual(len(deck.cards), expected_card_count,
                             f"Deck should contain {expected_card_count} cards for {num_decks} decks.")

    def test_shuffle(self):
        """Test that the deck is shuffled properly (cards are not in sequential order)."""
        for num_decks in range(6, 9):  # Testing for 6 to 8 decks
            deck = Deck(num_decks)
            initial_order = deck.cards[:]
            deck.shuffle()
            self.assertNotEqual(initial_order, deck.cards, "Deck should be shuffled and not in initial order.")
            self.assertEqual(len(deck.cards), num_decks * 52 + 1,
                             "Number of cards in deck should be 53 (52 cards + 1 plastic card).")

    def test_deal_card(self):
        """Test dealing a card removes it from the deck."""
        for num_decks in range(6, 9):  # Testing for 6 to 8 decks
            deck = Deck(num_decks)
            deck.shuffle()
            dealt_card = deck.deal_card()
            self.assertEqual(len(deck.cards), num_decks * 52 - 1 + 1, "Deck should have one less card after dealing.")
            self.assertEqual(deck.cards.count(dealt_card), num_decks - 1)

    def test_check_for_plastic_card(self):
        """Test the detection of the plastic card."""
        deck = Deck()
        # Ensure the plastic card is at the end for this test
        deck.cards = deck.cards[:-1] + [0]  # Move plastic card to the end if not already
        self.assertTrue(deck.check_for_plastic_card(),
                        "Should return True when the plastic card is at the top of the deck.")
        deck.deal_card()  # Remove the plastic card
        self.assertFalse(deck.check_for_plastic_card(),
                         "Should return False when the plastic card is not at the top of the deck.")


if __name__ == '__main__':
    unittest.main()
