import random


class Deck:
    def __init__(self, num_decks=6):
        # Ensure num_decks is between 6 and 8.
        self.num_decks = max(6, min(num_decks, 8))
        self.cards = self._create_deck()
        self.plastic_card_position = random.randint(75, 100)  # Random position near the end of the deck.
        self.shuffle()

    def _create_deck(self):
        # Create multiple decks of cards and add the plastic card.
        cards = [suit * 100 + value for suit in range(1, 5) for value in range(1, 14)] * self.num_decks
        cards.append(0)  # 0 represents the plastic card.
        return cards

    def shuffle(self):
        # Shuffle the deck and insert the plastic card at a random position.
        random.shuffle(self.cards)
        self.cards = self.cards[:self.plastic_card_position] + [0] + self.cards[self.plastic_card_position:]
        random.shuffle(self.cards)  # Shuffle again to mix the plastic card.

    def deal_card(self):
        if not self.cards:
            # This should not happen but adding a check for safety.
            self.cards = self._create_deck()
            self.shuffle()
        return self.cards.pop()

    def check_for_plastic_card(self):
        # Check if the plastic card is near the top of the deck.
        if self.cards[-1] == 0:
            return True
        return False
