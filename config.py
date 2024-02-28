# config.py
import logging

from game.game_state_machine import GameStateMachine
from game.player_manager import PlayerManager
from game.event_handler import EventHandler
from game.game_manager import GameManager
from utils.event_bus import EventBus
import utils.log_setup

event_bus = EventBus()

logger = utils.log_setup.setup_logger(log_level=logging.DEBUG, name=__name__)

player_manager = PlayerManager(num_seats=4, event_bus=event_bus, logger=logger)

game_state_machine = GameStateMachine(event_bus=event_bus, logger=logger)

# Setup GameManager with all dependencies
game_manager = GameManager(num_decks=8,
                           player_manager=player_manager, event_bus=event_bus,
                           logger=logger)

event_handler = EventHandler(event_bus=event_bus, logger=logger, game_manager=game_manager)


async def get_game_manager() -> GameManager:
    return game_manager


async def get_event_bus() -> EventBus:
    return event_bus


async def get_state_machine() -> GameStateMachine:
    return game_state_machine


async def get_event_handler() -> EventHandler:
    return event_handler
