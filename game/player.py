import logging

import utils.log_setup
from fastapi import WebSocket
import game.utils
from game.state import PlayerState


class Player:
    id_counter = 0

    def __init__(self, logger=logging.Logger, name='Dealer', balance=0, id=None, origin_player_id=None,
                 websocket: WebSocket = None):
        self.logger = logger
        self.state = PlayerState.WAIT_FOR_BET
        self.name = name
        self.balance = balance
        self.cards = []  # List to store the cards in the player's hand.
        self.score = 0
        self.id = id
        self.origin_player_id = origin_player_id  # None for original hands, set for split hands.

        self.insurance_taken = False
        self.available_actions = []
        self.bet = 0
        self.websocket = websocket
        self.has_double_down = False
        self.initial_bet = 0
        self.split_counter = 0

        self.logger = utils.log_setup.setup_logger(name=__name__)

    def transition_state(self, new_state):
        """Transition to a new state and call the corresponding method."""
        self.state = new_state
        self.logger.info(f"Player {self.name} transitioned to {self.state}")

    def reset(self):
        self.insurance_taken = False
        self.available_actions = []
        self.bet = 0

        self.cards = []
        self.score = 0
        self.split_counter = 0
        self.transition_state(PlayerState.WAIT_FOR_BET)

        self.has_double_down = False
        self.initial_bet = 0

    def has_blackjack(self):
        self.calculate_score()
        return self.score == 21 and len(self.cards) == 2

    def hit(self, deck):
        """Adds a card to the player's hand from the deck."""
        self.cards.append(deck.deal_card())
        self.logger.debug(f"player {self.name} hit")
        if self.is_busted():
            self.busted()
            self.logger.debug(f"player {self.name} busted")

    def calculate_score(self):
        """Calculates the current score of the player's hand."""
        self.score = 0
        ace_count = 0

        # Calculate score and count aces.
        for card in self.cards:
            value = card % 100  # Extract card value
            if value >= 11:  # Jack, Queen, King
                self.score += 10
            elif value == 1:  # Ace
                ace_count += 1
                self.score += 11  # Assume Ace is 11 initially
            else:  # Number cards
                self.score += value

        # Adjust for aces if score is over 21
        while self.score > 21 and ace_count > 0:
            self.score -= 10  # Convert an Ace from 11 to 1
            ace_count -= 1

    def display_hand(self):
        """Displays the player's hand with J, Q, K, and A represented correctly."""
        hand_representation = []
        for card in self.cards:
            hand_representation.append(game.utils.convert_card_code(card))
        return f"{self.name}'s hand: " + ', '.join(hand_representation)

    def is_busted(self):
        """Checks if the player has busted (score over 21)."""
        self.calculate_score()
        return self.score > 21

    def place_bet(self, amount):
        amount = int(amount)
        self.bet = amount
        self.balance -= amount

    def place_initial_bet(self, amount):
        self.place_bet(amount)
        self.initial_bet += amount

        if self.skip_round():
            self.transition_state(PlayerState.SKIPPED_ROUND)
        else:
            self.transition_state(PlayerState.AWAITING_MY_TURN)

    def double_down_allowed(self):
        return len(self.cards) == 2

    def insurance_allowed(self, dealer):
        if (int(dealer.cards[0]) % 100 == 1
                and not self.insurance_taken and len(dealer.cards) == 2):
            return True
        return False

    def split_allowed(self):
        if len(self.cards) == 2 and self.cards[0] % 100 == self.cards[1] % 100:
            # check split times
            if (self.cards[0] % 100 != 1) and self.split_counter < 3:
                self.split_counter += 1
                return True
            elif (self.cards[0] % 100 == 1) and self.split_counter < 1:
                self.split_counter += 1
                return True
            else:
                return False
        else:
            return False

    def split(self, deck):
        self.logger.info(f'player {self.name} split')
        split_hand = Player(name=f"{self.name} (Split)",
                            balance=0,
                            id=self.id,
                            origin_player_id=self.id or self.origin_player_id)  # Keep original player number if this is already a split hand
        # Place a bet equal to the original hand.
        self.balance -= self.initial_bet
        split_hand.bet = self.initial_bet
        self.bet += self.initial_bet
        split_hand.cards.append(self.cards.pop())  # Move one card to the split hand.
        self.hit(deck)  # Draw new cards for both hands.
        split_hand.hit(deck)
        return split_hand

    def take_insurance(self, dealer):
        insurance_bet = self.initial_bet / 2
        dealer.balance += insurance_bet
        self.insurance_taken = True

    def stand(self):
        self.logger.debug(f"player {self.name} stand")
        self.transition_state(PlayerState.HAS_ACTED)

    def busted(self):
        self.transition_state(PlayerState.HAS_ACTED)

    def skip_round(self):
        if self.initial_bet == 0:
            return True
        return False

    def publish_result(self):
        self.transition_state(PlayerState.RESULT_NOTIFIED)

    def double_down(self, deck, dealer):
        self.balance -= self.initial_bet
        dealer.balance = dealer.balance + self.initial_bet
        self.bet += self.initial_bet
        self.has_double_down = True
        self.hit(deck)
