class Player:
    def __init__(self, name='Dealer', balance=0, player_number=None, origin_player_number=None):
        self.name = name
        self.balance = balance
        self.insurance_bet = None
        self.cards = []  # List to store the cards in the player's hand.
        self.bet = 0
        self.score = 0
        self.insurance_taken = False
        self.player_number = player_number
        self.origin_player_number = origin_player_number  # None for original hands, set for split hands.

    def hit(self, deck):
        """Adds a card to the player's hand from the deck."""
        self.cards.append(deck.deal_card())
        self.calculate_score()  # Update score with each new card.

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
            suit = '♠♥♣♦'[card // 100 - 1]
            value = card % 100
            if value == 1:
                face_value = 'A'
            elif value == 11:
                face_value = 'J'
            elif value == 12:
                face_value = 'Q'
            elif value == 13:
                face_value = 'K'
            else:
                face_value = str(value)
            hand_representation.append(f"{suit}{face_value}")
        return f"{self.name}'s hand: " + ', '.join(hand_representation)

    def is_busted(self):
        """Checks if the player has busted (score over 21)."""
        return self.score > 21

    def place_bet(self, amount):
        self.bet = amount
        self.balance -= amount

    def double_down(self, deck):
        if len(self.cards) == 2:
            self.place_bet(self.bet)  # Double the bet.
            self.hit(deck)
            print(f"{self.name} doubled down.")
            self.display_hand()
        else:
            print("Double down not allowed.")

    def split(self, deck):
        split_hand = Player(name=f"{self.name} (Split)",
                            balance=0,
                            player_number=self.player_number,
                            origin_player_number=self.player_number or self.origin_player_number)  # Keep original player number if this is already a split hand
        split_hand.place_bet(self.bet)  # Place a bet equal to the original hand.
        self.balance -= self.bet
        split_hand.cards.append(self.cards.pop())  # Move one card to the split hand.
        self.hit(deck)  # Draw new cards for both hands.
        split_hand.hit(deck)
        return split_hand

    def take_insurance(self, insurance_bet):
        self.insurance_bet = insurance_bet




