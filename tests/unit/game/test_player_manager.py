import unittest
from unittest.mock import Mock
from game.player_manager import PlayerManager


class TestPlayerManager(unittest.TestCase):
    def setUp(self):
        self.logger = Mock()
        self.event_bus = Mock()
        self.manager = PlayerManager(self.logger, 2, self.event_bus)

    def test_add_player(self):
        player = Mock()
        player.id = "0"
        player.name = "Player0"
        self.manager.add_player(player)
        self.assertTrue(self.manager.player_exists(player.id))
        self.assertEqual(self.manager.get_player_by_id(player.id), player)

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

    def tearDown(self):
        pass


if __name__ == "__main__":
    unittest.main()
