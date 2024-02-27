import unittest
from unittest.mock import MagicMock, patch, call
from game.game_manager import GameManager
from game.state import PlayerState
import game.utils


class TestGameManagerDealCards(unittest.TestCase):
    @patch('game.deck.Deck')
    @patch('game.player_manager.PlayerManager')
    @patch('game.player.Player')
    def setUp(self, MockPlayer, MockPlayerManager, MockDeck):
        self.game_manager = GameManager(num_decks=1, player_manager=MockPlayerManager(), event_bus=None, logger=None)
        self.player_1 = MagicMock(name='Player1')
        self.player_2 = MagicMock(name='Player2')
        self.player_3 = MagicMock(name='Player3')
        self.mocked_players = [self.player_1, self.player_2, self.player_3]
        # Assign mocked players to the player manager's players attribute
        self.game_manager.player_manager.players = self.mocked_players
        # Use the mock player class to simulate the dealer
        self.game_manager.dealer = MockPlayer()

    def test_deal_initial_cards_sequence(self):
        self.game_manager.deck = MagicMock()
        self.game_manager.reshuffle_deck = MagicMock()
        self.game_manager.deal_initial_cards()

        # Prepare the expected sequence of calls for the first and second card dealing
        expected_first_round_calls = [call.hit(self.game_manager.deck) for _ in range(1) for player in
                                      self.mocked_players + [self.game_manager.dealer]]
        expected_second_round_calls = [call.hit(self.game_manager.deck) for _ in range(1) for player in
                                       self.mocked_players + [self.game_manager.dealer]]

        # Check if the hit method was called in the correct sequence
        all_expected_calls = expected_first_round_calls + expected_second_round_calls

        # Verify the sequence for the mocked players and the dealer
        actual_calls = []
        for player in self.mocked_players:
            actual_calls.extend(player.method_calls)
        actual_calls.extend(self.game_manager.dealer.method_calls)

        self.assertEqual(actual_calls, all_expected_calls[:len(actual_calls)])

        # Check if reshuffle_deck was called
        self.game_manager.reshuffle_deck.assert_called_once()

    @patch('game.player.Player')
    def test_deal_initial_cards_with_skipped_round(self, MockPlayer):
        self.game_manager.deck = MagicMock()
        self.game_manager.reshuffle_deck = MagicMock()

        # Create mocked players with different states
        active_player_1 = MagicMock(name='ActivePlayer1', state=PlayerState.AWAITING_MY_TURN)
        active_player_2 = MagicMock(name='ActivePlayer2', state=PlayerState.AWAITING_MY_TURN)
        skipped_player = MagicMock(name='SkippedPlayer', state=PlayerState.SKIPPED_ROUND)

        self.game_manager.player_manager.players = [active_player_1, skipped_player, active_player_2]

        self.game_manager.deal_initial_cards()

        # Check that hit was called for active players and not for the skipped player
        active_player_1.hit.assert_called_with(self.game_manager.deck)
        active_player_2.hit.assert_called_with(self.game_manager.deck)
        skipped_player.hit.assert_not_called()

        # Since each active player gets two cards, verify the number of calls
        self.assertEqual(active_player_1.hit.call_count, 2)
        self.assertEqual(active_player_2.hit.call_count, 2)

        # Check if reshuffle_deck was called
        self.game_manager.reshuffle_deck.assert_called_once()


class TestGameManagerPlaceBet(unittest.TestCase):
    @patch('game.player_manager.PlayerManager')
    @patch('game.player.Player')
    @patch('game.deck.Deck')
    def setUp(self, MockDeck, MockPlayer, MockPlayerManager):
        self.logger = MagicMock()
        self.event_bus = MagicMock()
        self.game_manager = GameManager(num_decks=1, player_manager=MockPlayerManager(), event_bus=self.event_bus,
                                        logger=self.logger)
        self.mock_player = MockPlayer()
        self.game_manager.player_manager.get_player_via_id = MagicMock(return_value=self.mock_player)
        self.game_manager.player_manager.players = [self.mock_player]

    def test_place_bet_successfully(self):
        player_id = "player1"
        bet_amount = 100
        self.assertTrue(self.game_manager.place_bet(player_id, bet_amount))
        self.mock_player.place_initial_bet.assert_called_once_with(bet_amount)
        self.logger.info.assert_called()
        self.assertEqual(self.game_manager.dealer.balance, bet_amount)

    def test_place_bet_non_existing_player(self):
        self.game_manager.player_manager.get_player_via_id = MagicMock(return_value=None)
        player_id = "non_existing_player"
        bet_amount = 100
        self.assertFalse(self.game_manager.place_bet(player_id, bet_amount))
        self.logger.error.assert_called_once_with(f"Player with id {player_id} not found.")

    def test_all_players_have_placed_their_bets(self):
        player_id = "player1"
        bet_amount = 100
        self.mock_player.bet = bet_amount  # Pretend the player has already placed a bet
        self.game_manager.player_manager.players = [self.mock_player]
        self.mock_player.skip_round.return_value = False

        self.assertTrue(self.game_manager.place_bet(player_id, bet_amount))
        self.event_bus.publish.assert_called_with('all_betting_done')

    def test_all_players_skipping_the_round(self):
        self.game_manager.all_player_skipping_the_round = MagicMock(return_value=True)
        player_id = "player1"
        bet_amount = 100
        self.assertTrue(self.game_manager.place_bet(player_id, bet_amount))
        self.event_bus.publish.assert_called_with('all_players_skipped')


class TestGameManagerPlayerTurn(unittest.TestCase):
    @patch('game.player_manager.PlayerManager')
    @patch('game.player.Player')
    @patch('game.deck.Deck')
    def setUp(self, MockDeck, MockPlayer, MockPlayerManager):
        self.logger = MagicMock()
        self.event_bus = MagicMock()
        self.game_manager = GameManager(num_decks=1, player_manager=MockPlayerManager(), event_bus=self.event_bus,
                                        logger=self.logger)
        self.player = MockPlayer(name='player')
        self.game_manager.dealer = MockPlayer(name='dealer')

    def test_player_turn_stand_hit(self):
        # Mocking player properties for the test
        self.player.double_down_allowed.return_value = False
        self.player.split_allowed.return_value = False
        self.player.insurance_allowed.return_value = False
        self.player.has_double_down = False
        self.player.has_blackjack.return_value = False

        # Execute the method under test
        self.game_manager.player_turn(self.player)

        expected_actions = ["Hit (h)", "Stand (s)"]
        self.assertEqual(game.utils.convert_actions(expected_actions), self.player.available_actions)

    def test_player_turn_insurance(self):
        self.player.double_down_allowed.return_value = False
        self.player.split_allowed.return_value = False
        self.player.insurance_allowed.return_value = True
        self.player.has_double_down = False
        self.player.has_blackjack.return_value = False

        # Execute the method under test
        self.game_manager.player_turn(self.player)
        expected_actions = ["Hit (h)", "Stand (s)", "Insurance (i)"]
        self.assertEqual(game.utils.convert_actions(expected_actions), self.player.available_actions)

    def test_player_turn_can_split(self):
        self.player.double_down_allowed.return_value = False
        self.player.split_allowed.return_value = True
        self.player.insurance_allowed.return_value = False
        self.player.has_double_down = False
        self.player.has_blackjack.return_value = False

        # Execute the method under test
        self.game_manager.player_turn(self.player)
        expected_actions = ["Hit (h)", "Stand (s)", "Split (p)"]
        self.assertEqual(game.utils.convert_actions(expected_actions), self.player.available_actions)

    def test_player_turn_player_double_down(self):
        self.player.double_down_allowed.return_value = False
        self.player.split_allowed.return_value = False
        self.player.insurance_allowed.return_value = False
        self.player.has_double_down = True
        self.player.has_blackjack.return_value = False

        # Execute the method under test
        self.game_manager.player_turn(self.player)
        expected_actions = ["Stand (s)"]
        self.assertEqual(game.utils.convert_actions(expected_actions), self.player.available_actions)

    def test_player_turn_player_blackjack(self):
        self.player.double_down_allowed.return_value = False
        self.player.split_allowed.return_value = False
        self.player.insurance_allowed.return_value = False
        self.player.has_double_down = False
        self.player.score = 21

        # Execute the method under test
        self.game_manager.player_turn(self.player)
        expected_actions = ["Stand (s)"]
        self.assertEqual(game.utils.convert_actions(expected_actions), self.player.available_actions)


class TestGameManagerHandleAction(unittest.TestCase):
    @patch('game.player_manager.PlayerManager')
    @patch('game.player.Player')
    @patch('game.deck.Deck')
    def setUp(self, MockDeck, MockPlayer, MockPlayerManager):
        self.logger = MagicMock()
        self.event_bus = MagicMock()
        self.game_manager = GameManager(num_decks=1, player_manager=MockPlayerManager(), event_bus=self.event_bus,
                                        logger=self.logger)
        self.player = MockPlayer()
        # self.game_manager.dealer = MockPlayer()
        self.game_manager.dealer.cards = [101]  # Dealer's face-up card is an Ace for insurance tests
        self.game_manager.player_manager.insert_split_player = MagicMock()

    def test_handle_action_hit(self):
        self.player.is_busted = MagicMock(return_value=False)
        self.game_manager.handle_action('h', self.player)
        self.player.hit.assert_called_once_with(self.game_manager.deck)

    def test_handle_action_stand(self):
        self.game_manager.handle_action('s', self.player)
        self.player.stand.assert_called_once()

    def test_handle_action_double_down(self):
        self.game_manager.handle_action('d', self.player)
        self.player.double_down.assert_called_once_with(deck=self.game_manager.deck, dealer=self.game_manager.dealer)

    def test_handle_action_split(self):
        self.game_manager.handle_action('p', self.player)
        self.player.split.assert_called_once_with(self.game_manager.deck)
        self.game_manager.player_manager.insert_split_player.assert_called_once()

    def test_handle_action_insurance(self):
        self.game_manager.handle_action('i', self.player)
        self.player.take_insurance.assert_called_once()


class TestGameManagerAllPlayerSkipping(unittest.TestCase):
    @patch('game.player_manager.PlayerManager')
    @patch('game.player.Player')
    def setUp(self, MockPlayer, MockPlayerManager):
        self.player_manager = MockPlayerManager()
        self.game_manager = GameManager(num_decks=1, player_manager=self.player_manager, event_bus=None, logger=None)

    def test_all_players_skipping(self):
        # Mock players to simulate all skipping the round
        self.player_manager.players = [MagicMock(skip_round=MagicMock(return_value=True)) for _ in range(3)]

        result = self.game_manager.all_player_skipping_the_round()
        self.assertTrue(result, "Expected True when all players are skipping the round")

    def test_not_all_players_skipping(self):
        # Mock players where one is not skipping the round
        self.player_manager.players = [MagicMock(skip_round=MagicMock(return_value=True)) for _ in range(2)]
        self.player_manager.players.append(MagicMock(skip_round=MagicMock(return_value=False)))

        result = self.game_manager.all_player_skipping_the_round()
        self.assertFalse(result, "Expected False when at least one player is not skipping the round")


class TestGameManagerDealerTurn(unittest.TestCase):
    @patch('game.player_manager.PlayerManager')
    @patch('game.player.Player')
    @patch('game.deck.Deck')
    def setUp(self, MockDeck, MockPlayer, MockPlayerManager):
        self.logger = MagicMock()
        self.event_bus = MagicMock()
        self.game_manager = GameManager(num_decks=1, player_manager=MockPlayerManager(), event_bus=self.event_bus,
                                        logger=self.logger)
        self.game_manager.dealer = MockPlayer()
        self.game_manager.deck = MockDeck()

    def test_dealer_turn_hits_until_17_or_higher(self):
        scores = [10, 15, 17]  # Simulate dealer's score progression

        # Set up the dealer's calculate_score method to simulate score progression
        def side_effect_calculate_score():
            self.game_manager.dealer.score = scores.pop(0)

        self.game_manager.dealer.calculate_score = MagicMock(side_effect=side_effect_calculate_score)
        self.game_manager.dealer.score = scores[0]

        self.game_manager.dealer_turn()

        # Verify calculate_score was called enough times to reach a score of 17 or more
        self.assertEqual(self.game_manager.dealer.score, 17)
        self.assertTrue(self.game_manager.dealer.calculate_score.called)
        self.assertEqual(self.game_manager.dealer.calculate_score.call_count, 3)
        # Verify hit was called at least once
        self.assertTrue(self.game_manager.dealer.hit.called)
        self.assertEqual(self.game_manager.dealer.hit.call_count, 2)


class TestGameManagerDetermineWinners(unittest.TestCase):
    @patch('game.player_manager.PlayerManager')
    @patch('game.player.Player')
    @patch('game.player.Player')
    @patch('game.player.Player')
    def setUp(self, MockDealer, MockPlayer1, MockPlayer2, MockPlayerManager):
        self.logger = MagicMock()
        self.game_manager = GameManager(num_decks=1, player_manager=MockPlayerManager(), event_bus=None,
                                        logger=self.logger)
        self.game_manager.dealer = MockDealer(name='dealer')
        self.player1 = MockPlayer1(name='player1')
        self.player2 = MockPlayer2(name='player2')
        self.game_manager.player_manager.players = [self.player1, self.player2]

    def test_player_wins_by_higher_score(self):
        self.game_manager.dealer.score = 18
        self.game_manager.dealer.is_busted = MagicMock(return_value=False)
        self.game_manager.dealer.has_blackjack.return_value = False

        self.player1.score = 19
        self.player1.is_busted = MagicMock(return_value=False)
        self.player1.initial_bet = 100
        self.player1.bet = 200
        self.player1.balance = 1000
        self.player1.has_blackjack.return_value = False
        self.player1.origin_player_id = None
        self.game_manager.determine_winners()

        self.assertEqual(self.player1.balance, 1400)  # Player wins and gets bet * 2

    def test_player_loses_by_busting(self):
        self.game_manager.dealer.score = 18
        self.player1.score = 22  # Player busts
        self.player1.is_busted = MagicMock(return_value=True)
        self.player1.bet = 100
        self.player1.balance = 1000

        self.game_manager.determine_winners()

        # Ensure the player's balance remains unchanged (loss by busting doesn't win the bet back)
        self.assertEqual(self.player1.balance, 1000)  # Bet is lost, balance should not change

    def test_push_scenario(self):
        self.game_manager.dealer.score = 20
        self.game_manager.dealer.is_busted = MagicMock(return_value=False)
        self.game_manager.dealer.has_blackjack.return_value = False

        self.player1.score = 20
        self.player1.is_busted = MagicMock(return_value=False)
        self.player1.bet = 100
        self.player1.initial_balance = 10
        self.player1.balance = 1000
        self.player1.origin_player_id = None
        self.player1.has_blackjack.return_value = False

        self.game_manager.determine_winners()

        self.assertEqual(self.player1.balance, 1100)  # Player gets bet back in a push

    def test_dealer_wins(self):
        self.game_manager.dealer.score = 20
        self.game_manager.dealer.is_busted = MagicMock(return_value=False)
        self.game_manager.dealer.has_blackjack.return_value = False

        self.player1.score = 18
        self.player1.is_busted = MagicMock(return_value=False)
        self.player1.bet = 100
        self.player1.initial_balance = 10
        self.player1.balance = 1000
        self.player1.origin_player_id = None
        self.player1.has_blackjack.return_value = False

        self.game_manager.determine_winners()

        self.assertEqual(self.player1.balance, 1000)  # Player gets bet back in a push

    def test_player_wins_with_blackjack(self):
        self.game_manager.dealer.score = 20
        self.game_manager.dealer.is_busted = MagicMock(return_value=False)
        self.game_manager.dealer.has_blackjack.return_value = False

        self.player1.score = 21
        self.player1.is_busted = MagicMock(return_value=False)
        self.player1.bet = 100
        self.player1.initial_bet = 100
        self.player1.balance = 1000
        self.player1.origin_player_id = None
        self.player1.has_blackjack.return_value = True
        self.player1.insurance_taken = False

        self.game_manager.determine_winners()

        self.assertEqual(self.player1.balance, 1250)

    def test_dealer_and_player_both_blackjack(self):
        self.game_manager.dealer.score = 21
        self.game_manager.dealer.is_busted = MagicMock(return_value=False)
        self.game_manager.dealer.has_blackjack.return_value = True

        self.player1.score = 21
        self.player1.is_busted = MagicMock(return_value=False)
        self.player1.bet = 100
        self.player1.initial_bet = 100
        self.player1.balance = 1000
        self.player1.origin_player_id = None
        self.player1.has_blackjack.return_value = True
        self.player1.insurance_taken = False

        self.game_manager.determine_winners()

        self.assertEqual(self.player1.balance, 1100)

    def test_player_busted(self):
        self.game_manager.dealer.score = 20
        self.game_manager.dealer.is_busted = MagicMock(return_value=False)
        self.game_manager.dealer.has_blackjack.return_value = False

        self.player1.score = 22
        self.player1.is_busted = MagicMock(return_value=True)
        self.player1.bet = 100
        self.player1.initial_bet = 100
        self.player1.balance = 1000
        self.player1.origin_player_id = None
        self.player1.insurance_taken = False
        self.player1.has_blackjack.return_value = False

        self.game_manager.determine_winners()

        self.assertEqual(self.player1.balance, 1000)

    def test_dealer_busted(self):
        self.game_manager.dealer.score = 22
        self.game_manager.dealer.is_busted = MagicMock(return_value=True)
        self.game_manager.dealer.has_blackjack.return_value = False

        self.player1.score = 20
        self.player1.is_busted = MagicMock(return_value=False)
        self.player1.bet = 100
        self.player1.initial_bet = 100
        self.player1.balance = 1000
        self.player1.origin_player_id = None
        self.player1.has_blackjack.return_value = False
        self.player1.insurance_taken = False

        self.game_manager.determine_winners()

        self.assertEqual(self.player1.balance, 1200)

    def test_takes_insurance_dealer_blackjack(self):
        self.game_manager.dealer.score = 21
        self.game_manager.dealer.is_busted = MagicMock(return_value=False)
        self.game_manager.dealer.has_blackjack.return_value = True

        self.player1.score = 19
        self.player1.is_busted = MagicMock(return_value=False)
        self.player1.bet = 100
        self.player1.initial_bet = 100
        self.player1.balance = 1000
        self.player1.origin_player_id = None
        self.player1.has_blackjack.return_value = False
        self.player1.insurance_taken = True

        self.game_manager.determine_winners()

        self.assertEqual(self.player1.balance, 1150)

    def test_takes_insurance_dealer_wins_but_no_blackjack(self):
        self.game_manager.dealer.score = 20
        self.game_manager.dealer.is_busted = MagicMock(return_value=False)
        self.game_manager.dealer.has_blackjack.return_value = False

        self.player1.score = 19
        self.player1.is_busted = MagicMock(return_value=False)
        self.player1.bet = 100
        self.player1.initial_bet = 100
        self.player1.balance = 1000
        self.player1.origin_player_id = None
        self.player1.has_blackjack = False
        self.player1.insurance_taken = True

        self.game_manager.determine_winners()

        self.assertEqual(self.player1.balance, 1000)

    def test_takes_insurance_player_wins(self):
        self.game_manager.dealer.score = 19
        self.game_manager.dealer.is_busted = MagicMock(return_value=False)
        self.game_manager.dealer.has_blackjack.return_value = False

        self.player1.score = 20
        self.player1.is_busted = MagicMock(return_value=False)
        self.player1.bet = 200
        self.player1.initial_bet = 100
        self.player1.balance = 1000
        self.player1.origin_player_id = None
        self.player1.insurance_taken = True
        self.player1.has_blackjack.return_value = False

        self.game_manager.determine_winners()

        self.assertEqual(self.player1.balance, 1400)

    def test_takes_insurance_player_wins_with_blackjack(self):
        self.game_manager.dealer.score = 19
        self.game_manager.dealer.is_busted = MagicMock(return_value=False)
        self.game_manager.dealer.has_blackjack.return_value = False

        self.player1.score = 20
        self.player1.is_busted = MagicMock(return_value=False)
        self.player1.bet = 100
        self.player1.initial_bet = 100
        self.player1.balance = 1000
        self.player1.origin_player_id = None
        self.player1.insurance_taken = True
        self.player1.has_blackjack.return_value = True

        self.game_manager.determine_winners()

        self.assertEqual(self.player1.balance, 1250)

    def test_dealer_wins_with_blackjack_no_insurance(self):
        self.game_manager.dealer.score = 21
        self.game_manager.dealer.is_busted = MagicMock(return_value=False)
        self.game_manager.dealer.has_blackjack.return_value = True

        self.player1.score = 20
        self.player1.is_busted = MagicMock(return_value=False)
        self.player1.bet = 100
        self.player1.initial_bet = 100
        self.player1.balance = 1000
        self.player1.origin_player_id = None
        self.player1.insurance_taken = False
        self.player1.has_blackjack.return_value = False

        self.game_manager.determine_winners()

        self.assertEqual(self.player1.balance, 1000)


if __name__ == '__main__':
    unittest.main()
