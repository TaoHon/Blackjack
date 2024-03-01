from game.deck import Deck
from game.player import Player

import game.utils

from game.state import GameState, PlayerState





class GameManager:
    def __init__(self, num_decks, player_manager, event_bus, logger):
        self.logger = logger

        self.player_manager = player_manager
        self.event_bus = event_bus

        self.deck = Deck(num_decks=num_decks)
        self.deck.shuffle()
        self.dealer = Player(name='dealer')
        self.available_bets = [str(bet) for bet in [0, 1, 2, 5, 25, 100, 500]]
        self.seats = {}  # create a dictionary to keep track of the seats
        self.betting_event = None
        self.waiting_players_to_join = None  # Initialized later
        self.round_counter = 0

    def get_available_bets(self):
        return self.available_bets

    def deal_initial_cards(self):
        for _ in range(2):  # Each player, including the dealer, gets two cards initially.
            for player in self.player_manager.players + [self.dealer]:
                if player.state == PlayerState.SKIPPED_ROUND:
                    continue  # If so, don't deal cards to this player
                player.hit(self.deck)

        self.reshuffle_deck()

    def add_player(self, player):
        self.player_manager.add_player(player)

    def place_bet(self, player_id, bet_amount):
        player = self.player_manager.get_player_via_id(player_id)
        if player:
            self.logger.info(f"Player {player.name}, bet amount: {bet_amount}")
            player.place_initial_bet(bet_amount)
            self.dealer.balance += int(bet_amount)
            # Check all players have placed a bet
            if self.all_player_skipping_the_round():
                self.logger.info("All players skipping their round.")
                self.event_bus.publish('all_players_skipped')
                return True
            if all(p.state is not PlayerState.WAIT_FOR_BET for p in self.player_manager.players):
                self.logger.info("All players have placed their bets.")
                self.event_bus.publish('all_betting_done')
            return True
        else:
            self.logger.error(f"Player with id {player_id} not found.")
        return False

    def reshuffle_deck(self):
        self.deck.shuffle_if_needed()

    def player_turn(self, player):
        self.logger.info(f"Current score: {player.score}")

        actions = ["Hit (h)", "Stand (s)"]
        if player.double_down_allowed():
            actions.append("Double Down (d)")
        if player.split_allowed(self.player_manager.count_split_players(player)):
            actions.append("Split (p)")
        if player.insurance_allowed(self.dealer):  # Assuming a flag to track if insurance is taken
            actions.append("Insurance (i)")

        if player.has_blackjack() or player.has_double_down:
            actions = ["Stand (s)"]

        player.available_actions = game.utils.convert_actions(actions)

    def handle_action(self, player_action, player):
        if player_action == 'h':
            player.hit(self.deck)

        elif player_action == 's':
            player.stand()

        elif player_action == 'd':
            player.double_down(deck=self.deck, dealer=self.dealer)

        elif player_action == 'p':
            # Split logic here; would require managing additional hand
            split_player = player.split(self.deck)
            self.dealer.balance += player.initial_bet
            self.player_manager.insert_split_player(player, split_player)
            self.logger.debug(f"player {player.name} split")

        elif player_action == 'i' and player.insurance_allowed(self.dealer):
            player.take_insurance(self.dealer)

        player.calculate_score()  # Recalculate score after each action

        self.event_bus.publish('player_acted')

    def dealer_turn(self):
        self.dealer.calculate_score()

        # Dealer hits until score is 17 or higher
        while self.dealer.score < 17:
            self.dealer.hit(self.deck)
            self.dealer.calculate_score()

    def determine_winners(self):
        for player in self.player_manager.players:
            player_score = player.score
            if player.is_busted():
                pass
            # Check for insurance payout
            elif self.dealer.has_blackjack() and player.insurance_taken:
                player.balance += player.initial_bet * 1.5  # Insurance bet pays 2:1.
                self.dealer.balance -= player.initial_bet * 1.5

            elif self.dealer.is_busted() or (player_score > self.dealer.score and not self.dealer.has_blackjack()):
                # Check if this is a split hand and add winnings to the original player if so
                target_player = self.find_original_player(player) if player.origin_player_id else player
                self.logger.debug(f"Player {player.name} has bet {player.bet}")
                target_player.balance += player.bet * 2  # Payout for win
                self.dealer.balance -= player.bet * 2

                if target_player.has_blackjack():  # Check for Blackjack
                    target_player.balance += player.initial_bet * 0.5  # Additional payout for Blackjack.
                    self.dealer.balance -= player.initial_bet * 0.5
            elif player_score == self.dealer.score:
                player.balance += player.bet  # Return the player's bet
                self.dealer.balance -= player.bet
            elif self.dealer.score > player_score:
                pass

            self.logger.info(f"Round: {self.round_counter} Player {player.name} balance: {player.balance}")

        self.player_manager.remove_split_player()

        self.logger.info(f"Round: {self.round_counter} Dealer {self.dealer.name} balance: {self.dealer.balance}")


    def find_original_player(self, split_player):
        # This method would search for the original player based on the origin_player_number.
        # Assuming player_number is unique and correctly managed.
        for player in self.player_manager.players:
            if player.id == split_player.origin_player_id:
                return player
        return None

    def cleanup_after_round(self):
        self.logger.info("Cleaning up")
        # Filter out split hands from the list of active players.
        self.player_manager.reset_players()
        self.dealer.reset()
        self.round_counter = self.round_counter + 1
        self.logger.info("Cleaning up done")

    def get_table_state_array(self, hidden_card=False):
        # Initialize the table state with the dealer's hand
        if hidden_card:
            table_state = [900] + [self.dealer.cards[0], 888] + self.dealer.cards[2:]
        else:
            table_state = [900] + self.dealer.cards
        # Append each player's hand to the state, separated by 900 + player number
        for player in self.player_manager.players:
            player_state = [901 + self.player_manager.get_seat_number(player.id)] + player.cards
            table_state.extend(player_state)
        return table_state

    def print_table_state(self, hidden_card=False):
        table_state_array = self.get_table_state_array(hidden_card=hidden_card)
        # Convert card codes back to human-readable format or use directly if they're already in that format
        readable_state = []
        for item in table_state_array:
            if int(item / 100) == 9:
                readable_state.append('----')  # Separator between hands
                if item == 900:
                    readable_state.append("Dealer's hand:")
                else:
                    readable_state.append(
                        f"{self.player_manager.get_player_via_seat(seat_number=item % 9).name}'s hand:")
            elif isinstance(item, int):
                # Here, convert card codes to human-readable format, e.g., 102 -> 'Heart 2'
                readable_state.append(game.utils.convert_card_code(item))
            else:
                readable_state.append(item)  # Player names and dealer label
        print('\n'.join(readable_state))

    def all_player_skipping_the_round(self):
        # Iterate through all players
        for player in self.player_manager.players:
            # If any player is not skipping the round, return False
            if not player.skip_round():
                return False
        # If all players are skipping the round, return True
        return True

