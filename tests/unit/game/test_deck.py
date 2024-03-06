import unittest
import sys
import os
import random

from game.deck import Deck


class TestDeck(unittest.TestCase):
    def setUp(self):
        self.deck = Deck(6)

    def tearDown(self):
        pass

    def test_init(self):
        self.assertEqual(self.deck.num_decks, 6)
        # total number of decks multiplied by the number of cards in a deck.
        self.assertEqual(len(self.deck.cards), 52 * 6)
        self.assertEqual(self.deck.maximum_deck_size, 52 * 6)
        self.assertEqual(self.deck.plastic_card_pos, 0)

    def test_create_deck(self):
        # we have 4 suits and each suit has 13 cards from 1 to 13
        # so total number of unique cards is 4*13=52
        self.assertEqual(len(set(self.deck._create_deck())), 52)

    def test_shuffle(self):
        initial_deck = self.deck.cards.copy()
        self.deck.shuffle()
        self.assertNotEqual(initial_deck, self.deck.cards)

    def test_deal_card(self):
        initial_len = len(self.deck.cards)
        self.deck.deal_card()
        self.assertEqual(len(self.deck.cards), initial_len - 1)

        self.deck.cards = []
        self.deck.deal_card()
        self.assertEqual(len(self.deck.cards), initial_len - 1)

    def test_random_plastic_card_index(self):
        index = self.deck.random_plastic_card_index()
        half_length = self.deck.maximum_deck_size // 2
        full_length = self.deck.maximum_deck_size * 52
        self.assertTrue(half_length - half_length // 4 <= index <= half_length + half_length // 4)


if __name__ == '__main__':
    unittest.main()
