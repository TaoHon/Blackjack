import unittest
from game.deck import Deck
from game.event_handler import EventHandler
from game.game_manager import GameManager
from game.game_state_machine import GameStateMachine
from game.player_manager import PlayerManager
from game.player import Player
from game.state import PlayerState
from utils.event_bus import EventBus
from utils.log_setup import setup_logger
import logging


class TestHandlePlayerActionInsurance(unittest.TestCase):
    def setUp(self):
        self.event_bus = EventBus()
        self.logger = setup_logger(log_level=logging.DEBUG, name=__name__)
        self.player_manager = PlayerManager(num_seats=1, event_bus=self.event_bus, logger=self.logger)
        self.game_state_machine = GameStateMachine(event_bus=self.event_bus, logger=self.logger)
        self.game_manager = GameManager(num_decks=8, player_manager=self.player_manager, event_bus=self.event_bus,
                                        logger=self.logger)
        self.event_handler = EventHandler(event_bus=self.event_bus, logger=self.logger, game_manager=self.game_manager)

    def test_handle_player_action_take_insurance_dealer_blackjack(self):
        # Preparing the deck with a specific card to ensure predictable outcomes

        # Adding a test player to the game
        player = Player(name='TestUser', id=21, websocket=None, balance=1000)
        self.game_manager.add_player(player)
        self.game_manager.deck.cards = [110, 102, 101, 103]
        # Placing a bet for the player and verifying the bet was recorded correctly
        self.game_manager.place_bet(player.id, 100)
        self.assertEqual(player.initial_bet, 100)
        self.assertEqual(player.bet, 100)
        self.assertEqual(player.balance, 900)

        # Verifying the dealer's balance increased due to the player's bet
        self.assertEqual(self.game_manager.dealer.balance, 100)

        # Simulating the player's turn and verifying available actions and card state
        self.game_manager.player_turn(player)
        self.assertEqual(player.cards, [103, 102])
        self.assertEqual(self.game_manager.dealer.cards, [101, 110])
        self.assertEqual(player.available_actions, ['h', 's', 'd', 'i'])

        # Handling player action to take insurance and verifying the state post-insurance
        self.game_manager.handle_action(player=player, player_action='i')
        self.assertEqual(player.insurance_taken, True)
        self.assertEqual(player.balance, 850)
        self.assertEqual(self.game_manager.dealer.balance, 150)

        self.assertEqual(player.state, PlayerState.MY_TURN)

        # Simulating the player's turn and verifying available actions and card state
        self.game_manager.player_turn(player)
        self.assertEqual(player.available_actions, ['h', 's', 'd'])
        self.assertEqual(player.cards, [103, 102])
        self.assertEqual(self.game_manager.dealer.cards, [101, 110])

        self.game_manager.handle_action(player=player, player_action='s')

        self.assertEqual(player.balance, 1000)
        self.assertEqual(self.game_manager.dealer.balance, 0)

    def test_handle_player_action_take_insurance_dealer_win(self):
        # Preparing the deck with a specific card to ensure predictable outcomes

        # Adding a test player to the game
        player = Player(name='TestUser', id=21, websocket=None, balance=1000)
        self.game_manager.add_player(player)
        self.game_manager.deck.cards = [109, 102, 101, 103]
        # Placing a bet for the player and verifying the bet was recorded correctly
        self.game_manager.place_bet(player.id, 100)
        self.assertEqual(player.initial_bet, 100)
        self.assertEqual(player.bet, 100)
        self.assertEqual(player.balance, 900)

        # Verifying the dealer's balance increased due to the player's bet
        self.assertEqual(self.game_manager.dealer.balance, 100)

        # Simulating the player's turn and verifying available actions and card state
        self.game_manager.player_turn(player)
        self.assertEqual(player.cards, [103, 102])
        self.assertEqual(self.game_manager.dealer.cards, [101, 109])
        self.assertEqual(player.available_actions, ['h', 's', 'd', 'i'])

        # Handling player action to take insurance and verifying the state post-insurance
        self.game_manager.handle_action(player=player, player_action='i')
        self.assertEqual(player.insurance_taken, True)
        self.assertEqual(player.balance, 850)
        self.assertEqual(self.game_manager.dealer.balance, 150)

        self.assertEqual(player.state, PlayerState.MY_TURN)

        # Simulating the player's turn and verifying available actions and card state
        self.game_manager.player_turn(player)
        self.assertEqual(player.available_actions, ['h', 's', 'd'])
        self.assertEqual(player.cards, [103, 102])
        self.assertEqual(self.game_manager.dealer.cards, [101, 109])

        self.game_manager.handle_action(player=player, player_action='s')

        self.assertEqual(player.balance, 850)
        self.assertEqual(self.game_manager.dealer.balance, 150)


if __name__ == '__main__':
    unittest.main()
