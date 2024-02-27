import pytest
from unittest.mock import MagicMock
from game.game_state_machine import GameStateMachine


@pytest.fixture
def setup_game_state_machine():
    event_bus = MagicMock()
    logger = MagicMock()
    state_machine = GameStateMachine(event_bus, logger)
    return state_machine, event_bus, logger


def test_start_betting_transition(setup_game_state_machine):
    state_machine, _, _ = setup_game_state_machine
    assert state_machine.state == 'waiting_for_players'

    # Trigger transition
    state_machine.start_betting()
    assert state_machine.state == 'betting'


def test_all_betting_done_transition(setup_game_state_machine):
    state_machine, _, _ = setup_game_state_machine
    # Assuming initial state is 'betting' for this test
    state_machine.state = 'betting'

    state_machine.all_betting_done()
    assert state_machine.state == 'dealing_initial_cards'


def test_cards_dealing_done_transition(setup_game_state_machine):
    state_machine, _, _ = setup_game_state_machine
    # Setting state to 'dealing_initial_cards'
    state_machine.state = 'dealing_initial_cards'

    state_machine.cards_dealing_done()
    assert state_machine.state == 'player_turn'


def test_player_action_needed_transition(setup_game_state_machine):
    state_machine, _, _ = setup_game_state_machine
    # Setting state to 'player_turn'
    state_machine.state = 'player_turn'

    state_machine.player_action_need()
    # Expect state to remain 'player_turn' since it indicates another player action is required
    assert state_machine.state == 'player_turn'


def test_dealer_turn_done_transition(setup_game_state_machine):
    state_machine, _, _ = setup_game_state_machine
    # Setting state to 'dealer_turn'
    state_machine.state = 'dealer_turn'

    state_machine.dealer_turn_done()
    assert state_machine.state == 'determine_winners'


def test_cleanup_done_transition_resets_to_betting(setup_game_state_machine):
    state_machine, _, _ = setup_game_state_machine
    # Setting state to 'round_end'
    state_machine.state = 'round_end'

    state_machine.cleanup_done()
    assert state_machine.state == 'betting'
