import asyncio
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, applications
from pydantic import ValidationError
from network.connection_manager import ConnectionManager
from game.player import Player
from game.table import Table
from models import PlayerAction, RequestPlayerAction
from game.state import GameState, PlayerState

router = APIRouter()
manager = ConnectionManager()

table = Table(num_seats=2)

@router.websocket("/ws/{client_name}")
async def websocket_endpoint(websocket: WebSocket, client_name: str):
    await manager.connect(websocket)
    client_id = str(uuid.uuid4())
    table.initialize_events()  # Ensure we're in the async context
    if table.get_state() == GameState.WAITING_FOR_PLAYERS_TO_JOIN:
        try:
            player = Player(client_name, id=client_id, websocket=websocket)
            table.add_player(player)
            await table.waiting_players_to_join.wait()
        except ValidationError as e:
            await manager.send_personal_message(f"Invalid data: {e}", player.websocket)
    try:
        while True:
            if table.get_state() == GameState.BETTING:
                available_bets = table.get_available_bets()
                player = table.get_player_via_id(client_id)
                if player.state == PlayerState.WAITING_FOR_BET:
                    print(f"Waiting for {player.name} to bet")
                    request_action = RequestPlayerAction(username=player.name, state=table.get_state().name,
                                                         table=[],
                                                         available_actions=available_bets)
                    await manager.send_personal_message(request_action.model_dump_json(), player.websocket)
                    data = await player.websocket.receive_text()
                    try:
                        json_data = PlayerAction.model_validate_json(data)
                        table.place_bet(player.id, json_data.action)
                        await table.betting_event.wait()
                    except ValidationError as e:
                        await manager.send_personal_message(f"Invalid data: {e}", player.websocket)

            elif table.get_state() == GameState.AWAITING_PLAYER_ACTION:
                await table.player_events[player.id].wait()
                request_action = RequestPlayerAction(username=player.name, state=table.get_state().name,
                                                     table=table.get_table_state_array(hidden_card=True),
                                                     available_actions=player.available_actions)
                await manager.send_personal_message(request_action.model_dump_json(), websocket)
                data = await websocket.receive_text()
                try:
                    json_data = PlayerAction.model_validate_json(data)
                    table.handle_action(json_data.action, player)
                except ValidationError as e:
                    await manager.send_personal_message(f"Invalid data: {e}", player.websocket)

                # if player is not None:
                #     print(f"Waiting for {player.name} to bet")
                #     request_action = RequestPlayerAction(username=player.name, state=table.get_state().name,
                #                                          table=[],
                #                                          available_actions=available_bets)
                #     await manager.send_personal_message(request_action.model_dump_json(), player.websocket)
                #     data = await player.websocket.receive_text()
                #     print(f"{data}")
                #     try:
                #         action = PlayerAction.model_validate_json(data)
                #         table.place_bet(player.id, action.action)
                #     except ValidationError as e:
                #         await manager.send_personal_message(f"Invalid data: {e}", player.websocket)
            # await manager.broadcast(new_game_state)
    except WebSocketDisconnect:
        manager.disconnect(client_name)


# @router.websocket("/ws/{client_id}")
# async def websocket_endpoint(client_id: str, websocket: WebSocket):
#     await manager.connect(websocket)
#     try:
#         print(f"WebSocket {id(websocket)} connected.")
#         while True:
#             if table.get_state() == GameState.WAITING_FOR_PLAYERS_TO_JOIN:
#                 try:
#                     player = Player(client_id, id=client_id, websocket=websocket)
#                     table.add_player(player)
#                 except ValidationError as e:
#                     await manager.send_personal_message(f"Invalid data: {e}", player.websocket)
#
#             if table.get_state() == GameState.BETTING:
#                 available_bets = table.get_available_bets()
#                 player = table.get_player_with_no_bet()
#                 print(f"{player.name} ready to bet")
#             await asyncio.sleep(1)  # sleep for a while before next loop iteration to allow other connections

            # if player is not None:
            #     print(f"Waiting for {player.name} to bet")
            #     request_action = RequestPlayerAction(username=player.name, state=table.get_state().name,
            #                                          table=[],
            #                                          available_actions=available_bets)
            #     await manager.send_personal_message(request_action.model_dump_json(), player.websocket)
            #     data = await player.websocket.receive_text()
            #     print(f"{data}")
            #     try:
            #         action = PlayerAction.model_validate_json(data)
            #         table.place_bet(player.id, action.action)
            #     except ValidationError as e:
            #         await manager.send_personal_message(f"Invalid data: {e}", player.websocket)
            # elif table.get_state() == GameState.AWAITING_PLAYER_ACTION:
            #     if player and player.need_action:
            #         request_action = RequestPlayerAction(username=player.name, state=table.get_state().name,
            #                                              table=table.get_table_state_array(),
            #                                              available_actions=player.available_actions)
            #         await manager.send_personal_message(request_action.model_dump_json(), websocket)
            #         data = await websocket.receive_text()
            #         try:
            #             action = PlayerAction.model_validate_json(data)
            #             table.handle_action(action, player)
            #         except ValidationError as e:
            #             await manager.send_personal_message(f"Invalid data: {e}", websocket)
    # except WebSocketDisconnect:
    #     if player:
    #         table.remove_player(player)
    #     await manager.disconnect(client_id)
    #     await manager.broadcast(f"Client #{client_id} left the game")
