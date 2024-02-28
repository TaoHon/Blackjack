import unittest
from unittest.mock import MagicMock, Mock

# Import the Player class from game package
from game.player import Player
from game.state import PlayerState


class TestPlayer(unittest.TestCase):

    def setUp(self):
        self.mock_logger = MagicMock()
        self.mock_websocket = MagicMock()
        self.mock_deck = MagicMock()
        self.mock_dealer = MagicMock()
        self.mock_card = MagicMock()
        self.mock_insurance_bet = MagicMock()
        self.player = Player(logger=self.mock_logger, websocket=self.mock_websocket)
        self.dealer = Player(logger=self.mock_logger, websocket=self.mock_websocket)

    def test_transition_state(self):
        self.player.transition_state(PlayerState.AWAITING_MY_TURN)
        self.assertEqual(self.player.state, PlayerState.AWAITING_MY_TURN)

    def test_reset(self):
        self.player.reset()
        self.assertEqual(self.player.cards, [])
        self.assertEqual(self.player.score, 0)
        self.assertEqual(self.player.insurance_taken, False)
        self.assertEqual(self.player.available_actions, [])
        self.assertEqual(self.player.bet, 0)
        self.assertEqual(self.player.state, PlayerState.WAIT_FOR_BET)
        self.assertEqual(self.player.has_double_down, False)

    def test_hit(self):
        self.mock_deck.deal_card.return_value = 102
        self.player.hit(self.mock_deck)
        self.assertEqual(self.player.cards, [102])

    def test_calculate_score(self):
        # Test lower limit with one card (Ace considered as 11)
        self.player.cards = [101]
        self.player.calculate_score()
        self.assertEqual(self.player.score, 11)

        # Test lower limit with one card (2)
        self.player.cards = [102]
        self.player.calculate_score()
        self.assertEqual(self.player.score, 2)

        # Test condition when have Ace and some card making sum more than 21
        self.player.cards = [101, 113, 113]
        self.player.calculate_score()
        self.assertEqual(self.player.score, 21)

        # Test for 21 score with Ace considered as 11
        self.player.cards = [101, 110, 110]
        self.player.calculate_score()
        self.assertEqual(self.player.score, 21)

        # Test upper limit with multiple cards (Ace considered as 1)
        self.player.cards = [101, 113, 113]
        self.player.calculate_score()
        self.assertEqual(self.player.score, 21)

        # Test with multiple cards (Ace considered as 1)
        self.player.cards = [101, 109, 113, 113]
        self.player.calculate_score()
        self.assertEqual(self.player.score, 30)

        # Test upper limit with number cards only
        self.player.cards = [110, 110, 110, 110]
        self.player.calculate_score()
        self.assertEqual(self.player.score, 40)

        # Test hand with multiple Aces
        self.player.cards = [101, 101, 102]
        self.player.calculate_score()
        self.assertEqual(self.player.score, 14)

        # Test hand with multiple Aces and high-value card
        self.player.cards = [101, 101, 113, 113]
        self.player.calculate_score()
        self.assertEqual(self.player.score, 22)

    def test_display_hand(self):
        self.player.cards = [201]
        self.assertEqual(self.player.display_hand(), f"{self.player.name}'s hand: ♥A")

    def test_is_busted(self):
        self.player.cards = [101, 101, 113, 113]
        self.assertEqual(self.player.is_busted(), True)

        self.player.cards = [101, 101]
        self.assertEqual(self.player.is_busted(), False)

    def test_place_bet(self):
        self.player.place_initial_bet(10)
        self.assertEqual(self.player.bet, 10)
        self.assertEqual(self.player.balance, -10)

    def test_double_down(self):
        self.mock_deck.deal_card.return_value = 105
        self.player.cards = [101, 102]
        self.player.initial_bet = 10
        self.player.bet = 10
        self.player.balance = 20
        self.player.double_down(self.mock_deck, self.mock_dealer)
        self.assertEqual(
            self.player.cards, [101, 102, 105])
        self.assertEqual(self.player.bet, 20)
        self.assertEqual(self.player.balance, 10)

    def test_split(self):
        self.mock_deck.deal_card.side_effect = [103, 104, 105]
        self.player.cards = [102, 102]
        self.player.balance = 100
        self.player.initial_bet = 20
        self.player.bet = 20
        split_player = self.player.split(self.mock_deck)
        self.assertIsNotNone(split_player)

        self.assertEqual(self.player.cards, [102, 103])
        self.assertEqual(split_player.cards, [102, 104])

        self.assertEqual(self.player.balance, 80)
        self.assertEqual(self.player.bet, 20)
        self.assertEqual(split_player.bet, 20)

    def test_stand(self):
        self.player.stand()
        self.assertEqual(self.player.state, PlayerState.HAS_ACTED)

    def test_busted(self):
        self.player.busted()
        self.assertEqual(self.player.state, PlayerState.HAS_ACTED)

    def test_skip_round(self):
        self.player.bet = 0
        self.assertEqual(self.player.skip_round(), True)

    def test_publish_result(self):
        self.player.publish_result()
        self.assertEqual(self.player.state, PlayerState.RESULT_NOTIFIED)

    def test_split_allowed(self):
        self.player.cards = [202, 102]
        self.assertEqual(self.player.split_allowed(split_counter=0), True)

        self.player.cards = [202, 102]
        self.assertEqual(self.player.split_allowed(split_counter=3), False)

        self.player.cards = [301, 401]
        self.assertEqual(self.player.split_allowed(split_counter=0), True)

        self.player.cards = [301, 401]
        self.assertEqual(self.player.split_allowed(split_counter=1), False)

        self.player.cards = [301, 402]
        self.assertEqual(self.player.split_allowed(split_counter=0), False)

        self.player.cards = [301, 401, 402]
        self.assertEqual(self.player.split_allowed(split_counter=0), False)

        self.player.cards = [301]
        self.assertEqual(self.player.split_allowed(split_counter=0), False)

    def test_double_down_allowed(self):
        self.player.cards = [301]
        self.assertEqual(self.player.double_down_allowed(), False)

        self.player.cards = [301, 401]
        self.assertEqual(self.player.double_down_allowed(), True)

        self.player.cards = [301, 401, 302]
        self.assertEqual(self.player.double_down_allowed(), False)

    def test_insurance_allowed(self):
        self.dealer.name = 'dealer'
        self.dealer.cards = ['401', '302']
        self.player.insurance_taken = False
        self.assertEqual(self.player.insurance_allowed(self.dealer), True)

        self.dealer.name = 'dealer'
        self.dealer.cards = ['402', '302']
        self.player.insurance_taken = False
        self.assertEqual(self.player.insurance_allowed(self.dealer), False)

        self.dealer.name = 'dealer'
        self.dealer.cards = ['401', '302', '201']
        self.player.insurance_taken = False
        self.assertEqual(self.player.insurance_allowed(self.dealer), False)

        self.dealer.name = 'dealer'
        self.dealer.cards = ['401', '302']
        self.player.insurance_taken = True
        self.assertEqual(self.player.insurance_allowed(self.dealer), False)

    def test_take_insurance(self):
        self.dealer.balance = 0
        self.player.initial_bet = 100

        self.player.insurance_taken = False
        self.player.take_insurance(self.dealer)
        self.assertEqual(self.dealer.balance, self.player.initial_bet / 2)
        self.assertEqual(self.player.insurance_taken, True)


if __name__ == '__main__':
    unittest.main()
