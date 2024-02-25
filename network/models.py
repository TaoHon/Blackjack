from pydantic import BaseModel


class PlayerAction(BaseModel):
    player_name: str
    action: str
    # Add more fields as needed


class RequestPlayerAction(BaseModel):
    username: str
    state: str
    table: list
    # balance: int
    available_actions: list
    # Add more fields as needed
