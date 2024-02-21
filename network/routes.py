import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, applications
from pydantic import ValidationError
from network.connection_manager import ConnectionManager
from game.player import Player
from game.table import Table
from models import PlayerAction, RequestPlayerAction
from game.game_state import GameState

router = APIRouter()
manager = ConnectionManager()

table = Table(num_seats=7)


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket):
    client_id = str(uuid.uuid4())  # Generate a unique client_id
    await manager.connect(websocket)
    try:
        while True:
            if table.get_state() == GameState.WAITING_FOR_PLAYERS:
                await manager.send_personal_message(f"Please enter your name", websocket)
                # Wait for the client's response
                data = await websocket.receive_text()
                try:
                    action = PlayerAction.model_validate_json(data)
                    player = Player(action.player_name, id=client_id)
                    table.add_player(player)
                except ValidationError as e:
                    await manager.send_personal_message(f"Invalid data: {e}", websocket)
            elif table.get_state() == GameState.BETTING:
                await manager.send_personal_message(f"Please place your bet", websocket)
                available_bets = ['bet'].append(table.get_available_bets(client_id))
                request_action = RequestPlayerAction(username=player.name, available_actions=['bet', available_bets])
                await manager.send_personal_message(request_action.model_dump_json(), websocket)
                # Wait for the client's response
                data = await websocket.receive_text()
                try:
                    action = PlayerAction.model_validate_json(data)
                    table.place_bet(client_id, action.action)
                except ValidationError as e:
                    await manager.send_personal_message(f"Invalid data: {e}", websocket)


    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left the game")
