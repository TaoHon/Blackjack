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


class TestHandlePlayerActionSplit(unittest.TestCase):
    def setUp(self):
        self.event_bus = EventBus()
        self.logger = setup_logger(log_level=logging.DEBUG, name=__name__)
        self.player_manager = PlayerManager(num_seats=1, event_bus=self.event_bus, logger=self.logger)
        self.game_state_machine = GameStateMachine(event_bus=self.event_bus, logger=self.logger)
        self.game_manager = GameManager(num_decks=8, player_manager=self.player_manager, event_bus=self.event_bus,
                                        logger=self.logger)
        self.event_handler = EventHandler(event_bus=self.event_bus, logger=self.logger, game_manager=self.game_manager)

    def test_determine_winners_player_split(self):
        # Preparing the deck with a specific card to ensure predictable outcomes
        self.game_manager.deck.cards = [110] * 50

        # Adding a test player to the game
        player = Player(name='TestUser', id=21, websocket=None, balance=1000)
        self.game_manager.add_player(player)

        # Placing a bet for the player and verifying the bet was recorded correctly
        self.game_manager.place_bet(player.id, 100)
        self.assertEqual(player.initial_bet, 100)
        self.assertEqual(player.bet, 100)

        # Verifying the dealer's balance increased due to the player's bet
        self.assertEqual(self.game_manager.dealer.balance, 100)

        # Simulating the player's turn and verifying available actions and card state
        self.game_manager.player_turn(player)
        self.assertEqual(player.available_actions, ['h', 's', 'd', 'p'])
        self.assertEqual(player.cards, [110, 110])

        # Verifying no split players exist before splitting
        self.assertEqual(self.player_manager.count_split_players(player), 0)

        # Handling player action to split and verifying the state post-split
        self.game_manager.handle_action(player=player, player_action='p')
        # Verifying a split player was added and associated attributes
        self.assertEqual(self.player_manager.count_split_players(player), 1)
        self.assertEqual(player.cards, [110, 110])
        self.assertEqual(player.bet, 100)
        self.assertEqual(player.initial_bet, 100)
        self.assertEqual(self.game_manager.dealer.balance, 200)
        self.assertEqual(player.balance, 800)

        self.assertEqual(len(self.player_manager.players), 2)

        # Verifying the origin of split players and continued game state
        self.assertEqual(self.player_manager.players[0].origin_player_id, None)
        self.assertEqual(self.player_manager.players[1].origin_player_id, player.id)

        # Repeating the process to split again and verify the game state updates
        self.game_manager.player_turn(player)
        self.game_manager.handle_action(player=player, player_action='p')
        # Assertions to verify the state after second split
        self.assertEqual(self.player_manager.count_split_players(player), 2)
        self.assertEqual(self.game_manager.dealer.balance, 300)
        self.assertEqual(player.balance, 700)
        self.assertEqual(len(self.player_manager.players), 3)

        self.game_manager.player_turn(player)
        self.assertEqual(player.available_actions, ['h', 's', 'd', 'p'])
        self.game_manager.handle_action(player=player, player_action='s')
        self.assertEqual(player.state, PlayerState.HAS_ACTED)  # Player has acted

        # Split hand 1's turn
        self.game_manager.player_turn(self.player_manager.players[1])
        self.assertEqual(self.player_manager.players[1].available_actions, ['h', 's', 'd', 'p'])
        # Split once more
        self.game_manager.handle_action(player=self.player_manager.players[1], player_action='p')
        # 3 split players now
        self.assertEqual(self.player_manager.count_split_players(player), 3)
        self.assertEqual(self.game_manager.dealer.balance, 400)
        self.assertEqual(len(self.player_manager.players), 4)

        # Checking that the game state remains consistent after actions
        self.assertEqual(self.game_state_machine.get_state(), 'player_turn')

        # Testing hitting after splitting and verifying the outcome
        self.game_manager.player_turn(self.player_manager.players[1])
        self.game_manager.handle_action(player=self.player_manager.players[1], player_action='h')
        self.assertEqual(self.player_manager.players[1].cards, [110, 110, 110])
        # busted
        self.assertEqual(self.player_manager.players[1].state, PlayerState.HAS_ACTED)  # Player has acted

        # Repeating hit action for another split player and verifying outcomes
        self.game_manager.player_turn(self.player_manager.players[2])
        # player_manager.players[2] doubled down
        self.game_manager.handle_action(player=self.player_manager.players[2], player_action='d')
        self.assertEqual(self.game_manager.dealer.balance, 500)
        self.assertEqual(self.player_manager.players[2].bet, 200)
        self.assertEqual(self.player_manager.players[2].initial_bet, 100)
        self.assertEqual(self.player_manager.players[2].balance, -100)
        self.assertEqual(self.player_manager.players[2].cards, [110, 110, 110])
        self.assertEqual(self.player_manager.players[2].state, PlayerState.HAS_ACTED)  # Player has acted

        # Repeating hit action for another split player and verifying outcomes
        self.game_manager.player_turn(self.player_manager.players[3])
        self.assertEqual(self.game_manager.dealer.balance, 500)

        self.assertEqual(self.player_manager.players[3].available_actions, ['h', 's', 'd'])

        self.assertEqual(self.player_manager.players[3].bet, 100)
        self.assertEqual(self.player_manager.players[3].initial_bet, 100)
        self.assertEqual(self.player_manager.players[3].balance, 000)
        self.assertEqual(self.player_manager.players[3].cards, [110, 110])
        self.game_manager.handle_action(player=self.player_manager.players[3], player_action='s')

        # determining winners
        self.assertEqual(player.balance, 700)
        self.assertEqual(self.game_manager.dealer.balance, 300)


if __name__ == '__main__':
    unittest.main()
