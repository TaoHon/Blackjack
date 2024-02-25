import logging
from asyncio import Event
import game.game_manager
from game.state import PlayerState


# from game.game_state_machine import GameStateMachine


class EventHandler:
    def __init__(self, game_manager, event_bus, logger=logging.getLogger()):
        self.game_manager = game_manager
        self.event_bus = event_bus
        self.logger = logger
        self.current_player = None
        # Initialize other components (PlayerManager, etc.)
        self.event_bus.subscribe('ready_to_bet', self.start_betting)
        self.event_bus.subscribe('all_betting_done', self.start_dealing_cards)
        self.event_bus.subscribe('cards_dealing_done', self.start_player_turn)
        self.event_bus.subscribe('player_acted', self.update_player_event)
        self.event_bus.subscribe('all_players_acted', self.start_dealer_turn)
        self.event_bus.subscribe('dealer_turn_done', self.determine_winners)
        self.event_bus.subscribe('determine_winners_done', self.publish_results)
        self.event_bus.subscribe('publish_results_done', self.cleanup_after_round)
        self.event_bus.subscribe("all_players_skipped", self.handle_all_players_skipped)

        self.bet_finished = Event()
        self.ready_to_start = Event()
        self.wait_for_dealer = Event()

        self.wait_for_new_round = Event()

    def start_betting(self):
        self.ready_to_start.set()
        self.logger.info("Starting betting")

    def start_dealing_cards(self):
        self.bet_finished.set()
        self.game_manager.deal_initial_cards()
        self.event_bus.publish('cards_dealing_done')

    def start_player_turn(self):
        self.current_player = self.game_manager.player_manager.get_current_turn_player()
        if self.current_player is not None:
            self.logger.info("game_manager.player_manager.player_events[current_player.id].set()")
            self.game_manager.player_manager.player_events[self.current_player.id].set()
            self.game_manager.player_turn(self.current_player)
        else:
            self.logger.info("All players acted")
            self.event_bus.publish('all_players_acted')

    def update_player_event(self):
        if self.current_player is not None:
            self.logger.info("game_manager.player_manager.player_events[current_player.id].clear()")
            self.game_manager.player_manager.player_events[self.current_player.id].clear()
        # get the next player
        self.start_player_turn()

    def start_dealer_turn(self):
        self.game_manager.player_manager.set_all_player_events()
        self.game_manager.dealer_turn()
        self.wait_for_dealer.set()
        self.event_bus.publish('dealer_turn_done')

    def determine_winners(self):
        self.game_manager.determine_winners()
        self.event_bus.publish('determine_winners_done')

    def publish_results(self):
        pass

    def cleanup_after_round(self):
        self.logger.debug("cleanup_after_round")
        self.bet_finished.clear()
        self.game_manager.player_manager.clear_all_player_events()
        self.game_manager.player_manager.reset_all_players()

        self.wait_for_new_round.set()
        self.game_manager.cleanup_after_round()
        self.event_bus.publish('cleanup_done')
        self.wait_for_new_round.clear()

    def handle_all_players_skipped(self):
        self.bet_finished.set()
        self.cleanup_after_round()
