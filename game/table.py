import asyncio

from game.deck import Deck
from game.player import Player

import game.utils
import game.player_agent
import logging
from game.game_state import GameState
from asyncio import Event


class Table:
    def __init__(self, num_seats, num_decks=6):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.deck = Deck(num_decks=num_decks)
        self.deck.shuffle()
        self.players = []
        self.dealer = Player()
        self.num_seats = num_seats
        self.player_agent = game.player_agent.PlayerAgent()
        self.available_bets = [0, 5, 10, 20, 50, 100]
        self.state = GameState.WAITING_FOR_PLAYERS_TO_JOIN  # Initial state
        self.available_seats = list(range(1, num_seats + 1))  # create a list of available seats
        self.seats = {}  # create a dictionary to keep track of the seats
        self.waiting_players_to_join = Event()
        self.betting_event = Event()
        self.player_ready_status = {}

    def get_state(self):
        return self.state

    def get_available_bets(self):
        return self.available_bets

    def deal_initial_cards(self):
        for _ in range(2):  # Each player, including the dealer, gets two cards initially.
            for player in self.players + [self.dealer]:
                player.hit(self.deck)
        if self.deck.check_for_plastic_card():
            self.reshuffle_deck()

        self.transition_state(GameState.PLAYER_TURNS)

    def get_seat_number(self, player_id):
        for seat, id in self.seats.items():
            if id == player_id:
                return seat
        return None

    def transition_state(self, new_state):
        """Transition to a new state and call the corresponding method."""
        self.state = new_state
        self.logger.info(f"Transitioned to {self.state}")
        if new_state == GameState.WAITING_FOR_PLAYERS_TO_JOIN:
            self.waiting_players_to_join.clear()
        elif new_state == GameState.BETTING:
            self.waiting_players_to_join.set()
            self.betting_event.clear()
        elif new_state == GameState.DEALING_INITIAL_CARDS:
            self.betting_event.set()
            self.deal_initial_cards()
        elif new_state == GameState.PLAYER_TURNS:
            for player in self.players:
                player.turn_event.clear()
                self.player_turn(player)
                player.turn_event.set()
        elif new_state == GameState.AWAITING_PLAYER_ACTION:
            pass
        elif new_state == GameState.DEALER_TURN:
            self.dealer_turn()
        elif new_state == GameState.DETERMINE_WINNERS:
            self.determine_winners()
        elif new_state == GameState.RESHUFFLE:
            self.reshuffle_deck()
        elif new_state == GameState.ROUND_END:
            self.cleanup_after_round()


    def get_available_seats(self) -> int:
        available_seats = self.num_seats - len(self.players)
        return available_seats

    def add_player(self, player):
        if not self.available_seats:
            logging.info(f"{player.name} cannot join the game. Table is full.")
            return False
        elif not self.player_exists(player.name):
            seat = self.available_seats.pop(0)
            self.seats[seat] = player.id  # assign seat to player
            self.logger.info(f"Adding {player.name} to seat {seat}, there are {len(self.available_seats)} seats left.")
            self.players.append(player)

            if not self.available_seats:
                self.player_ready_status = {player.id: asyncio.Future() for player in self.players}
                self.logger.info(f"No more seats left to join the game. Table is full.")
                self.logger.info(f"Game will start soon.")
                self.transition_state(GameState.BETTING)

        return True

    def remove_player(self, player):
        seat_to_remove = None
        for seat, player_name in self.seats.items():
            if player_name == player.name:
                seat_to_remove = seat
                break

        if seat_to_remove is not None:
            self.available_seats.insert(0, seat_to_remove)  # make the seat available again (adding at front to keep original order)
            self.available_seats.sort()  # sort the seats in ascending order
            del self.seats[seat_to_remove]  # remove player from seats dictionary

        self.players.remove(player)

    def player_exists(self, player_id: str):
        for player in self.players:
            if player.id == player_id:
                return True
        return False

    def get_player_via_id(self, player_id):
        for player in self.players:
            if player.id == player_id:
                return player
        return None

    def get_player_with_no_bet(self):
        for player in self.players:
            if player.bet is None:
                return player
        return None

    def get_player_via_seat(self, seat_number):
        for seat, player_id in self.seats.items():
            if seat == seat_number:
                return self.get_player_via_id(player_id)
        return None

    def place_bet(self, player_id, bet_amount):
        player = self.get_player_via_id(player_id)
        if player:
            self.logger.info(f"Player {player.name}, bet amount: {bet_amount}")
            player.place_bet(bet_amount)
            # Check all players have placed a bet
            if all(p.bet is not None for p in self.players):
                self.logger.info("All players have placed their bets.")
                self.transition_state(GameState.DEALING_INITIAL_CARDS)
            else:
                self.logger.info("Not all players have placed their bets yet.")
            return True
        else:
            self.logger.error(f"Player with id {player_id} not found.")
        return False

    def reshuffle_deck(self):
        # Check for reshuffle if the plastic card was drawn
        print("Time to reshuffle the deck.")
        self.deck.shuffle()

    def play_round(self):
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

        self.logger.info(f"Current score: {player.score}")

        actions = ["Hit (h)", "Stand (s)"]

        if double_down_allowed:
            actions.append("Double Down (d)")
        if split_allowed:
            actions.append("Split (p)")
        if insurance_allowed and not player.insurance_taken:  # Assuming a flag to track if insurance is taken
            actions.append("Insurance (i)")

        # Check for Blackjack
        player.calculate_score()  # Recalculate score after each action
        if player.score == 21:
            actions = ["Stand (s)"]

        player.available_actions = game.utils.convert_actions(actions)

        self.transition_state(GameState.AWAITING_PLAYER_ACTION)
        self.player_ready_status[player.id].set_result(True)  # Notify the system that player is ready

    def handle_action(self, player_action, player):
        double_down_allowed = False  # Assuming double down is allowed only on the initial hand.
        insurance_allowed = self.dealer.cards[0] % 100 == 1  # Dealer's face-up card is an Ace.
        if player_action == 'h':
            player.hit(self.deck)
            print(f"New card added: {player.cards[-1]}")
            self.transition_state(GameState.PLAYER_TURNS)
            if player.is_busted():
                print(f"{player.name} has busted!")
        elif player_action == 's':
            print(f"{player.name} stands.")
        elif player_action == 'd' and double_down_allowed:
            if player.double_down(self.deck):  # Assuming this method returns False if not allowed or fails
                print("Doubled down and drew one card.")
                print(f"New card: {player.cards[-1]}, New score: {player.score}")
            else:
                print("Cannot double down.")

        elif player_action == 'p':
            # Split logic here; would require managing additional hand
            split_player = player.split(self.deck)
            self.players.append(split_player)
            self.transition_state(GameState.PLAYER_TURNS)

        elif player_action == 'i' and insurance_allowed and not player.insurance_taken:
            insurance_bet = player.bet / 2
            player.take_insurance(insurance_bet)  # Deduct the insurance bet from the player's balance.
            player.insurance_taken = True
            print(f"Insurance bet of {insurance_bet} taken.")
            player.turn_event.clear()
        else:
            print("Invalid action or not allowed at this time.")
            player.turn_event.clear()

        player.calculate_score()  # Recalculate score after each action

    def dealer_turn(self):
        self.dealer.calculate_score()
        print(f"Dealer's starting hand: {self.dealer.cards[0]}, score: {self.dealer.score}")  # Only reveal one card

        # Dealer hits until score is 17 or higher
        while self.dealer.score < 17:
            self.dealer.hit(self.deck)
            self.dealer.calculate_score()

        if self.dealer.is_busted():
            print("Dealer busts!")
        else:
            print(f"Dealer stands with score: {self.dealer.score}")

    def determine_winners(self):
        dealer_score = self.dealer.score
        dealer_busted = self.dealer.is_busted()
        dealer_has_blackjack = dealer_score == 21 and len(self.dealer.cards) == 2
        self.print_table_state()

        for player in self.players:
            player_score = player.score

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
            if player.id == split_player.origin_player_number:
                return player
        return None

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

    def get_table_state_array(self, hidden_card=False):
        # Initialize the table state with the dealer's hand
        if hidden_card:
            table_state = [900] + [self.dealer.cards[0], 888] + self.dealer.cards[2:]
        else:
            table_state = [900] + self.dealer.cards
        # Append each player's hand to the state, separated by 900 + player number
        for player in self.players:
            player_state = [900 + self.get_seat_number(player.id)] + player.cards
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
                    readable_state.append(f"{self.get_player_via_seat(seat_number=item % 9).name}'s hand:")
            elif isinstance(item, int):
                # Here, convert card codes to human-readable format, e.g., 102 -> 'Heart 2'
                readable_state.append(game.utils.convert_card_code(item))
            else:
                readable_state.append(item)  # Player names and dealer label
        print('\n'.join(readable_state))
