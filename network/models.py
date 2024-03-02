from typing import Dict

from pydantic import BaseModel


class PlayerAction(BaseModel):
    player_name: str
    action: str


class RequestPlayerAction(BaseModel):
    player_name: str
    seat: int
    state: str
    table: list
    balance: float
    score: int
    available_actions: list

    # Add more fields as needed


class GameResult(BaseModel):
    balances: Dict[str, float]
    round: int
