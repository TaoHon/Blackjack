import asyncio
import logging
import time
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from pydantic import ValidationError

from game.game_state_machine import GameStateMachine
from game.event_handler import EventHandler
from network.connection_manager import ConnectionManager
from game.player import Player
from game.game_manager import GameManager
from network.models import RequestPlayerAction, PlayerAction, GameResult
from game.state import GameState, PlayerState
import utils.log_setup
from config import get_game_manager, get_event_bus, get_state_machine, \
    get_event_handler
from utils.event_bus import EventBus

router = APIRouter()
logger = utils.log_setup.setup_logger(name=__name__, log_level=logging.DEBUG)


@router.websocket("/ws/result/publish_results")
async def websocket_broadcast_results(websocket: WebSocket,
                                      game_manager: GameManager = Depends(get_game_manager),
                                      game_state_machine: GameStateMachine = Depends(get_state_machine),
                                      event_handler: EventHandler = Depends(get_event_handler)):
    connection_manager = ConnectionManager()
    await connection_manager.connect(websocket)

    while True:
        await event_handler.wait_for_result.wait()
        balances = {}
        for player in game_manager.player_manager.players:
            balances[player.name] = player.balance

        # Assuming game_manager.round_counter exists and tracks the current round
        game_result = GameResult(balances=balances, round=game_manager.round_counter)

        await connection_manager.send_personal_message(game_result.model_dump_json(), websocket)
@router.websocket("/ws/{client_name}")
async def websocket_endpoint(websocket: WebSocket, client_name: str,
                             game_manager: GameManager = Depends(get_game_manager),
                             game_state_machine: GameStateMachine = Depends(get_state_machine),
                             event_handler: EventHandler = Depends(get_event_handler)):
    connection_manager = ConnectionManager()
    await connection_manager.connect(websocket)
    client_id = str(uuid.uuid4())

    # Create a new player and add to the game
    player = Player(name=client_name, id=client_id, websocket=websocket, balance=1000)
    game_manager.player_manager.add_player(player)

    while True:
        # logger.debug(f"Game state {game_state_machine.get_state()}")
        # logger.debug(f'Client {player.name} player.state has {player.state} state')

        if game_state_machine.get_state() == 'betting':
            await handle_betting_state(player, game_manager, connection_manager, event_handler, websocket,
                                       game_state_machine)

        elif game_state_machine.get_state() == 'player_turn':
            await handle_player_turn_state(player, game_manager, connection_manager, websocket, game_state_machine,
                                           client_id)

        elif game_state_machine.get_state() == 'publish_result':
            await handle_publish_result_state(player, game_manager, connection_manager, websocket,
                                              game_state_machine, event_handler)

        await event_handler.ready_to_start.wait()


async def handle_betting_state(player, game_manager, connection_manager, event_handler, websocket, game_state_machine):
    available_bets = game_manager.get_available_bets()

    logger.info(f'Client {player.name} player.state has {player.state} state')
    request_action = RequestPlayerAction(username=player.name, state=game_state_machine.get_state(),
                                         table=[], balance=player.balance,
                                         available_actions=available_bets)
    await connection_manager.send_personal_message(request_action.model_dump_json(), websocket)
    data = await websocket.receive_text()
    logger.info(f"Processing player action {data}")
    if game_state_machine.get_state() == 'betting':
        try:
            json_data = PlayerAction.model_validate_json(data)
            game_manager.place_bet(player.id, json_data.action)
        except ValidationError as e:
            await connection_manager.send_personal_message(f"Invalid data: {e}", websocket)
            logger.info(f"Current state is {game_state_machine.get_state()}")
        pass

    await event_handler.bet_finished.wait()


async def handle_player_turn_state(player, game_manager, connection_manager, websocket, game_state_machine, client_id):
    origin_player = player
    await game_manager.player_manager.player_events[player.id].wait()

    if player.state != PlayerState.MY_TURN:
        logger.debug(f'Getting split player for {client_id}: {player.name}')
        split_player = game_manager.player_manager.get_waiting_split_player(player)
        # create a copy of the origin player
        if split_player is None:
            logger.debug(f'No split player found')
            return
        else:
            player = split_player
            logger.debug(f'Split player found: {player.name}')

    logger.info(f'Handling turn for {client_id} ({player.name})')

    # Prepare and send the initial request action to the player
    table_state = game_manager.get_table_state_array(hidden_card=True)
    actions = player.available_actions if player.state == PlayerState.MY_TURN else []

    request_action = RequestPlayerAction(username=player.name, state=game_state_machine.get_state(), table=table_state,
                                         available_actions=actions, balance=player.balance)
    logger.debug(f'Requesting action: {request_action}')

    await connection_manager.send_personal_message(request_action.model_dump_json(), websocket)

    # Await player action
    data = await websocket.receive_text()
    logger.debug(f'Received action from {client_id}: {data}')

    try:
        json_data = PlayerAction.model_validate_json(data)
        if json_data.player_name == player.name:
            game_manager.handle_action(json_data.action, player)
            player = origin_player
        else:
            logger.error(f'Action from mismatched client name: {json_data.player_name} vs {player.name}')
    except ValidationError as e:
        logger.error(f'Invalid data from {client_id}: {e}')
        await connection_manager.send_personal_message(f"Invalid data: {e}", player.websocket)


async def handle_publish_result_state(player, game_manager, connection_manager, websocket, game_state_machine,
                                      event_handler):
    if player.state == PlayerState.RESULT_NOTIFIED:
        await event_handler.wait_for_new_round.wait()
        return

    logger.info(f'Publishing result for {player.name}')

    table_state = game_manager.get_table_state_array(hidden_card=False)
    request_action = RequestPlayerAction(username=player.name, state=game_state_machine.get_state(), table=table_state,
                                         balance=player.balance, available_actions=[])
    await connection_manager.send_personal_message(request_action.model_dump_json(), websocket)

    player.publish_result()
    game_manager.player_manager.check_all_results_are_published()
