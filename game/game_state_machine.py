import asyncio

from transitions import Machine

from game.game_manager import GameManager


class GameStateMachine:
    states = ['waiting_for_players', 'betting', 'dealing_initial_cards', 'player_turn',
              'dealer_turn', 'determine_winners', 'publish_result', 'round_end']

    def __init__(self, event_bus, logger):
        self.machine = Machine(model=self, states=GameStateMachine.states, initial='waiting_for_players')
        self.event_bus = event_bus
        self.logger = logger

        # Define transitions
        self.machine.add_transition('start_betting', 'waiting_for_players', 'betting')
        self.machine.add_transition('all_betting_done', 'betting', 'dealing_initial_cards')
        self.machine.add_transition('cards_dealing_done', 'dealing_initial_cards', 'player_turn')
        self.machine.add_transition('player_action_need', 'player_turn', 'player_turn')
        self.machine.add_transition('all_players_acted', 'player_turn', 'dealer_turn')
        self.machine.add_transition('dealer_turn_done', 'dealer_turn', 'determine_winners')
        self.machine.add_transition('determine_winners_done', 'determine_winners', 'publish_result')
        self.machine.add_transition('publish_results_done', 'publish_result', 'round_end')
        self.machine.add_transition('cleanup_done', 'round_end', 'betting')
        self.machine.add_transition('all_players_skipped', 'betting', 'round_end')

        # Subscribe to events
        self.event_bus.subscribe('ready_to_bet', self.start_betting)
        self.event_bus.subscribe('all_betting_done', self.all_betting_done)
        self.event_bus.subscribe('cards_dealing_done', self.cards_dealing_done)
        self.event_bus.subscribe('player_action_done', self.player_action_need)
        self.event_bus.subscribe('all_players_acted', self.all_players_acted)
        self.event_bus.subscribe('dealer_turn_done', self.dealer_turn_done)
        self.event_bus.subscribe('determine_winners_done', self.determine_winners_done)
        self.event_bus.subscribe('publish_results_done', self.publish_results_done)
        self.event_bus.subscribe('cleanup_done', self.cleanup_done)
        self.event_bus.subscribe('all_players_skipped', self.all_players_skipped)

    def get_state(self):
        return self.state
