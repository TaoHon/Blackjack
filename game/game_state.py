# game_state.py

from enum import Enum, auto  # Notice how the import statement has been modified


class GameState(Enum):  # Error gone, we now subclass Enum
    WAITING_FOR_PLAYERS = auto()
    BETTING = auto()
    DEALING_INITIAL_CARDS = auto()
    PLAYER_TURNS = auto()
    DEALER_TURN = auto()
    DETERMINE_WINNERS = auto()
    RESHUFFLE = auto()
    ROUND_END = auto()
