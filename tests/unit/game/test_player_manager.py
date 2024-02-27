import unittest
from unittest.mock import Mock, patch
from game.player_manager import PlayerManager
from game.state import PlayerState


class TestPlayerManager(unittest.TestCase):
    def setUp(self):
        self.logger = Mock()
        self.event_bus = Mock()
        self.manager = PlayerManager(self.logger, 2, self.event_bus)

    def test_remove_player(self):
        player = Mock()
        player.id = "0"
        player.name = "Player0"
        self.manager.add_player(player)
        removed = self.manager.remove_player(player.id)
        self.assertFalse(self.manager.player_exists(player.id))
        self.assertEqual(removed, True)

    def test_set_player_event(self):
        player = Mock()
        player.id = "0"
        player.name = "Player0"
        self.manager.add_player(player)
        self.manager.set_player_event(player.id)
        self.assertTrue(self.manager.player_events[player.id].is_set())

    def test_clear_player_event(self):
        player = Mock()
        player.id = "0"
        player.name = "Player0"
        self.manager.add_player(player)
        self.manager.set_player_event(player.id)
        self.manager.clear_player_event(player.id)
        self.assertFalse(self.manager.player_events[player.id].is_set())

    def test_player_exists(self):
        player = Mock()
        player.id = "player123"
        self.manager.add_player(player)
        self.assertTrue(self.manager.player_exists("player123"))
        self.assertFalse(self.manager.player_exists("nonexistentPlayer"))

    def test_get_available_seats(self):
        self.assertEqual(self.manager.get_available_seats(), 2)  # Assuming num_seats was set to 2 in setUp
        player1 = Mock()
        player1.id = "player1"
        self.manager.add_player(player1)
        self.assertEqual(self.manager.get_available_seats(), 1)
        player2 = Mock()
        player2.id = "player2"
        self.manager.add_player(player2)
        self.assertEqual(self.manager.get_available_seats(), 0)

    def test_get_player_via_id(self):
        player1 = Mock()
        player1.id = "25"
        self.manager.add_player(player1)
        self.assertIs(self.manager.get_player_via_id("25"), player1)
        self.assertIsNone(self.manager.get_player_via_id("nonexistentPlayer"))

    def test_get_player_via_seat(self):
        # Setup: Add two players and assign them to seats
        player1 = Mock()
        player1.id = "1"
        self.manager.add_player(player1)

        player2 = Mock()
        player2.id = "2"
        self.manager.add_player(player2)

        # Test: Verify that each player can be retrieved by their seat number
        self.assertIs(self.manager.get_player_via_seat(0), player1)  # Assuming player1 is in seat 0
        self.assertIs(self.manager.get_player_via_seat(1), player2)  # Assuming player2 is in seat 1
        self.assertIsNone(self.manager.get_player_via_seat(2))  # No player in this seat

    def test_get_current_turn_player(self):
        # Setup: Add a player and set their state to AWAITING_MY_TURN
        player1 = Mock()
        player1.id = "player1"
        player1.name = "Player1"
        player1.state = PlayerState.HAS_ACTED
        self.manager.add_player(player1)

        # Set another player to MY_TURN state
        player2 = Mock()
        player2.id = "player2"
        player2.name = "Player2"
        player2.state = PlayerState.MY_TURN
        self.manager.add_player(player2)

        # Test: The method should return player2
        current_turn_player = self.manager.get_current_turn_player()
        self.assertEqual(current_turn_player, player2)

        # Additional test: Ensure player2's state transitions to MY_TURN if not already set
        player2.transition_state.assert_called_with(PlayerState.MY_TURN)

    def test_get_current_turn_player_return_None(self):
        # Setup: Add a player and set their state to AWAITING_MY_TURN
        player1 = Mock()
        player1.id = "player1"
        player1.name = "Player1"
        player1.state = PlayerState.HAS_ACTED
        self.manager.add_player(player1)

        # Set another player to MY_TURN state
        player2 = Mock()
        player2.id = "player2"
        player2.name = "Player2"
        player2.state = PlayerState.HAS_ACTED
        self.manager.add_player(player2)

        # Test: The method should return player2
        current_turn_player = self.manager.get_current_turn_player()
        self.assertEqual(current_turn_player, None)

    def test_get_seat_number(self):
        # Setup: Add a player and expect a seat number
        player = Mock()
        player.id = "player1"
        self.manager.add_player(player)

        # Test: Verify that the correct seat number is returned for the player
        expected_seat_number = 0  # Assuming the first player gets the first seat
        actual_seat_number = self.manager.get_seat_number(player.id)
        self.assertEqual(expected_seat_number, actual_seat_number)

        # Test: Verify that None is returned for a non-existent player ID
        self.assertIsNone(self.manager.get_seat_number("nonexistent"))

    def test_check_all_results_are_published(self):
        # Setup: Add players and set their states
        player1 = Mock()
        player1.state = PlayerState.RESULT_NOTIFIED
        self.manager.add_player(player1)

        player2 = Mock()
        player2.state = PlayerState.RESULT_NOTIFIED
        self.manager.add_player(player2)

        # Test: Verify that the final event is published when all players are notified
        self.manager.check_all_results_are_published()
        self.event_bus.publish.assert_called_with('publish_results_done')

    def test_set_all_player_events(self):
        # Setup: Add a player
        player = Mock()
        player.id = "player1"
        self.manager.add_player(player)

        # Create a mock for event.set
        mock_event = Mock()
        self.manager.player_events[player.id] = mock_event  # replace original event with mock

        # Test: Set all player events
        self.manager.set_all_player_events()
        mock_event.set.assert_called()  # assert that mock_event.set has been called
        mock_event.reset_mock()  # reset the mock for reuse if needed

    def test_clear_all_player_events(self):
        # Setup is the same as for setting events

        # Test: Clear all player events
        self.manager.clear_all_player_events()
        for event in self.manager.player_events.values():
            event.clear.assert_called()

    def test_reset_all_players(self):
        # Setup: Add players to the game
        player1 = Mock()
        self.manager.add_player(player1)

        player2 = Mock()
        self.manager.add_player(player2)

        # Test: Reset all players and verify
        self.manager.reset_all_players()
        for player in self.manager.players:
            player.reset.assert_called()

    def test_insert_split_player(self):
        # Setup: Add an original player to the manager
        original_player = Mock()
        original_player.id = "original1"
        self.manager.add_player(original_player)

        # Create a split player mock
        split_player = Mock()
        split_player.id = "split1"

        # Test: Insert the split player and verify position
        self.manager.insert_split_player(original_player, split_player)

        # Verify that the split player is immediately after the original player
        expected_index = self.manager.players.index(original_player) + 1
        actual_index = self.manager.players.index(split_player)
        self.assertEqual(expected_index, actual_index, "Split player is not in the correct position.")

        # Additional Tests
        # Verify that inserting a player not in the list logs the appropriate message and does not modify the list
        not_in_list_player = Mock()
        not_in_list_player.id = "not_in_list"
        original_length = len(self.manager.players)
        self.manager.insert_split_player(not_in_list_player, split_player)
        self.assertEqual(len(self.manager.players), original_length,
                         "The players list should not change when trying to insert using a player not in the list.")

    def test_reset_players(self):
        # Setup: Add multiple players to the manager, including mocks to observe the reset call
        player1 = Mock()
        player2 = Mock()
        self.manager.players = [player1, player2]

        # Test: Reset players
        self.manager.reset_players()

        # Verify: Ensure reset was called on each player
        player1.reset.assert_called_once()
        player2.reset.assert_called_once()

    def test_remove_split_player(self):
        # Setup: Create a mix of original and split players
        original_player = Mock()
        original_player.origin_player_id = None  # Indicate an original player
        split_player = Mock()
        split_player.origin_player_id = "original1"  # Indicate a split player
        self.manager.players = [original_player, split_player]

        # Test: Remove split players
        self.manager.remove_split_player()

        # Verify: Only the original player should remain
        self.assertIn(original_player, self.manager.players, "Original player should remain in the list.")
        self.assertNotIn(split_player, self.manager.players, "Split player should be removed from the list.")
        self.assertEqual(len(self.manager.players), 1, "There should only be one player left in the list.")

    def tearDown(self):
        pass


class TestPlayerManagerAddPlayer(unittest.TestCase):
    # Existing setup...
    def setUp(self):
        self.logger = Mock()
        self.event_bus = Mock()
        self.manager = PlayerManager(self.logger, 2, self.event_bus)

    def test_add_player_to_empty_seat(self):
        player = Mock()
        player.id = "1"
        player.name = "Player1"
        # Mock available seats before adding player
        self.manager.available_seats = [1]
        result = self.manager.add_player(player)
        self.assertTrue(result)
        self.assertIn(player, self.manager.players)
        self.assertIn(player.id, self.manager.player_events)

    @patch('asyncio.Event', autospec=True)
    def test_event_creation_for_new_player(self, mock_event):
        player = Mock()
        player.id = "2"
        player.name = "Player2"
        self.manager.available_seats = [2]
        self.manager.add_player(player)
        mock_event.assert_called_once()

    def test_add_player_when_table_is_full(self):
        player = Mock()
        player.id = "3"
        player.name = "Player3"
        # No available seats
        self.manager.available_seats = []
        result = self.manager.add_player(player)
        self.assertFalse(result)
        self.logger.info.assert_called_with(f"{player.name} cannot join the game. Table is full.")

    def test_add_duplicate_player(self):
        player1 = Mock()
        player1.id = "4"
        player1.name = "Player4"
        self.manager.add_player(player1)
        # Attempt to add a player with the same name
        player2 = Mock()
        player2.id = "4"
        player2.name = "Player4"
        result = self.manager.add_player(player2)
        self.assertFalse(result)
        self.assertEqual(len(self.manager.players), 1)  # Still only one player added


if __name__ == "__main__":
    unittest.main()
