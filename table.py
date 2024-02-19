import deck
import player


class Table:
    def __init__(self, num_players):
        self.deck = deck.Deck()
        self.deck.shuffle()
        self.players = [player.Player(f'Player {i}') for i in range(1, num_players + 1)]
        self.dealer = player.Player()

    def deal_initial_cards(self):
        for _ in range(2):  # Each player, including the dealer, gets two cards initially.
            for player in self.players + [self.dealer]:
                player.hit(self.deck)
        if self.deck.check_for_plastic_card():
            self.reshuffle_deck()

    def reshuffle_deck(self):
        # Check for reshuffle if the plastic card was drawn
        print("Time to reshuffle the deck.")
        self.deck.shuffle()

    def play_round(self):
        if len(self.deck.cards) < 20:  # Check if there are enough cards to play
            self.deck.shuffle()  # Reshuffle if the deck is low

        self.handle_bets()  # Handle initial betting
        self.deal_initial_cards()

        # Player actions
        for player in self.players:
            self.player_turn(player)

        # Dealer's turn
        self.dealer_turn()

        # Determine winners
        self.determine_winners()

        # Check for reshuffle if the plastic card was drawn
        if self.deck.check_for_plastic_card():
            self.reshuffle_deck()

    def player_turn(self, player):
        double_down_allowed = False  # Assuming double down is allowed only on the initial hand.
        split_allowed = len(player.cards) == 2 and player.cards[0] % 100 == player.cards[1] % 100
        insurance_allowed = self.dealer.cards[0] % 100 == 1  # Dealer's face-up card is an Ace.

        while True:
            print(f"{player.name}'s turn. Current hand: {player.display_hand()}")
            print(f"Current score: {player.score}")

            # Check for Blackjack
            player.calculate_score()  # Recalculate score after each action
            if player.score == 21:
                return
            
            actions = ["Hit (h)", "Stand (s)"]

            if double_down_allowed:
                actions.append("Double Down (d)")
            if split_allowed:
                actions.append("Split (p)")
            if insurance_allowed and not player.insurance_taken:  # Assuming a flag to track if insurance is taken
                actions.append("Insurance (i)")

            action_str = ", ".join(actions)
            player_action = input(f"Choose an action: {action_str}: ").lower()

            if player_action == 'h':
                player.hit(self.deck)
                print(f"New card added: {player.cards[-1]}")
                double_down_allowed = False  # Can no longer double down after hitting
                if player.is_busted():
                    print(f"{player.name} has busted!")
                    break
            elif player_action == 's':
                print(f"{player.name} stands.")
                break
            elif player_action == 'd' and double_down_allowed:
                if player.double_down(self.deck):  # Assuming this method returns False if not allowed or fails
                    print("Doubled down and drew one card.")
                    print(f"New card: {player.cards[-1]}, New score: {player.score}")
                    break
                else:
                    print("Cannot double down. Insufficient funds or already hit.")
            elif player_action == 'p':
                # Split logic here; would require managing additional hand
                split_player = player.split(self.deck)
                self.players.append(split_player)

            elif player_action == 'i' and insurance_allowed and not player.insurance_taken:
                insurance_bet = player.bet / 2
                player.take_insurance(insurance_bet)  # Deduct the insurance bet from the player's balance.
                player.insurance_taken = True
                print(f"Insurance bet of {insurance_bet} taken.")
            else:
                print("Invalid action or not allowed at this time.")

            player.calculate_score()  # Recalculate score after each action

    def dealer_turn(self):
        self.dealer.calculate_score()
        print(f"Dealer's starting hand: {self.dealer.cards[0]}, score: {self.dealer.score}")  # Only reveal one card

        # Dealer hits until score is 17 or higher
        while self.dealer.score < 17:
            self.dealer.hit(self.deck)
            self.dealer.calculate_score()

        # Reveal hole card and final score
        print(f"Dealer's final hand: {self.dealer.display_hand()}, score: {self.dealer.score}")

        if self.dealer.is_busted():
            print("Dealer busts!")
        else:
            print(f"Dealer stands with score: {self.dealer.score}")
            
    def determine_winners(self):
        dealer_score = self.dealer.score
        dealer_busted = self.dealer.is_busted()
        dealer_has_blackjack = dealer_score == 21 and len(self.dealer.cards) == 2
        print(f"Dealer's final hand: {self.dealer.display_hand()}, score: {dealer_score}")

        for player in self.players:
            player_score = player.score
            print(f"\n{player.name}'s final hand: {player.display_hand()}, score: {player_score}")

            # Check for insurance payout
            if dealer_has_blackjack and player.insurance_taken:
                print(f"{player.name} took insurance and dealer has Blackjack. Insurance pays out.")
                player.balance += player.insurance_bet * 3  # Insurance bet pays 2:1.

            if player.is_busted():
                print(f"{player.name} busts. Dealer wins.")
            elif dealer_busted or (player_score > dealer_score and not dealer_has_blackjack):
                print(f"{player.name} wins.")
                # Check if this is a split hand and add winnings to the original player if so
                target_player = self.find_original_player(player) if player.origin_player_number else player
                target_player.balance += player.bet * 2  # Payout for win
                if player_score == 21 and len(player.cards) == 2:  # Check for Blackjack
                    print(f"{player.name} has Blackjack! Additional winnings awarded.")
                    target_player.balance += player.bet * 0.5  # Additional payout for Blackjack.
            elif player_score == dealer_score and not dealer_has_blackjack:
                print("Push. Bet returned to player.")
                player.balance += player.bet  # Return the player's bet
            else:
                if not dealer_has_blackjack or not player.insurance_taken:
                    print(f"Dealer wins against {player.name}.")

            # Reset player's bet, insurance for the next round
            player.bet = 0
            player.insurance_taken = False
            player.insurance_bet = 0

        # Remove split hands after payouts
        self.players = [p for p in self.players if p.origin_player_number is None]

    def find_original_player(self, split_player):
        # This method would search for the original player based on the origin_player_number.
        # Assuming player_number is unique and correctly managed.
        for player in self.players:
            if player.player_number == split_player.origin_player_number:
                return player
        return None

    def handle_bets(self):
        for player in self.players:
            while True:
                try:
                    bet_amount = int(input(f"{player.name}, place your bet: "))
                    player.place_bet(bet_amount)
                    break
                except ValueError:
                    print("Please enter a valid number.")

    def check_continue_playing(self):
        for player in list(self.players):  # Iterate over a copy of the list to allow modification.
            choice = input(f"{player.name}, do you want to continue playing? (yes/no): ")
            if choice.lower() != 'yes':
                self.players.remove(player)

    def cleanup_after_round(self):
        # Filter out split hands from the list of active players.
        self.players = [player for player in self.players if player.origin_player_number is None]

        # reset each remaining player's state as needed for the next round.
        for player in self.players:
            player.cards = []
            player.score = 0
            player.bet = 0
            player.insurance_bet = None
            player.insurance_taken = False

        self.dealer.cards = []
        self.dealer.score = 0
        self.dealer.bet = 0
        self.dealer.insurance_bet = None
        self.dealer.insurance_taken = False


