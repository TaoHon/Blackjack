import random
import utils.log_setup


class Deck:
    def __init__(self, num_decks=6):
        # Ensure num_decks is between 6 and 8.
        self.num_decks = max(6, min(num_decks, 8))
        self.cards = self._create_deck()
        self.plastic_card_pos = 0
        self.maximum_deck_size = num_decks * 52
        self.logger = utils.log_setup.setup_logger(name=__name__)

    def _create_deck(self):
        # Create multiple decks of cards
        cards = [suit * 100 + value for suit in range(1, 5) for value in range(1, 14)] * self.num_decks

        return cards

    def shuffle(self):
        self.cards = self._create_deck()
        random.shuffle(self.cards)
        self.plastic_card_pos = self.random_plastic_card_index()

    def deal_card(self):
        if not self.cards:
            # This should not happen but adding a check for safety.
            self.cards = self._create_deck()
            self.shuffle()
        return self.cards.pop()

    def random_plastic_card_index(self):
        half_length = self.maximum_deck_size // 2  # Integer division to get half-length of cards
        full_length = self.maximum_deck_size * 52

        return random.randint(half_length - half_length // 4, half_length + half_length // 4)

    def shuffle_if_needed(self):
        if len(self.cards) < (self.maximum_deck_size - self.plastic_card_pos):
            self.shuffle()
            self.logger.info("Shuffled")

    def need_shuffle(self):
        if len(self.cards) < (self.maximum_deck_size - self.plastic_card_pos):
            return True
        return False
