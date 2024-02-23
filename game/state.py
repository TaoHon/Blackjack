# state.py

from enum import Enum, auto  # Notice how the import statement has been modified


class GameState(Enum):  # Error gone, we now subclass Enum
    WAITING_FOR_PLAYERS_TO_JOIN = auto()
    BETTING = auto()
    DEALING_INITIAL_CARDS = auto()
    PLAYER_TURNS = auto()
    AWAITING_PLAYER_ACTION = auto()
    DEALER_TURN = auto()
    DETERMINE_WINNERS = auto()
    RESHUFFLE = auto()
    ROUND_END = auto()


class PlayerState(Enum):
    WAITING_FOR_BET = auto()
    HAS_BET = auto()
    AWAITING_MY_TURN = auto()
    MY_TURN = auto()
    HAS_ACTED = auto()
    TOOK_INSURANCE = auto()
    BUSTED = auto()
