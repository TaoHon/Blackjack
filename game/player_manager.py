import asyncio
import utils.log_setup
import utils.event_bus
from game.state import PlayerState


class PlayerManager:
    def __init__(self, logger, num_seats, event_bus=None):
        self.players = []  # Stores player instances
        self.player_events = {}  # Maps player IDs to asyncio Events
        self.seats = {}  # Maps seat numbers to player IDs
        self.num_seats = num_seats
        self.available_seats = list(range(0, num_seats))  # create a list of available seats
        self.logger = logger
        self.event_bus = event_bus
        self.player_events = {}

    def add_player(self, player) -> bool:
        if not self.available_seats:
            self.logger.info(f"{player.name} cannot join the game. Table is full.")
            return False
        elif not self.player_exists(player.id):
            seat = self.available_seats.pop(0)
            self.seats[seat] = player.id  # assign seat to player
            self.logger.info(f"Adding {player.name} to seat {seat}, there are {len(self.available_seats)} seats left.")
            self.player_events[player.id] = asyncio.Event()
            self.players.append(player)
            if not self.available_seats:
                self.logger.info(f"No more seats left to join the game. Table is full.")
                self.logger.info(f"Game will start soon.")
                self.event_bus.publish('ready_to_bet')
            return True
        return False

    def remove_player(self, player_id) -> bool:
        """Remove a player from the game."""
        player = self.get_player_by_id(player_id)
        if not player:
            return False
        self.players.remove(player)
        del self.player_events[player.id]
        # Logic to free up the player's seat
        return True

    def get_player_by_id(self, player_id):
        """Retrieve a player instance by their ID."""
        return next((player for player in self.players if player.id == player_id), None)

    def set_player_event(self, player_id):
        """Set the event for a specific player."""
        if player_id in self.player_events:
            self.player_events[player_id].set()

    def clear_player_event(self, player_id):
        """Clear the event for a specific player."""
        if player_id in self.player_events:
            self.player_events[player_id].clear()

    def player_exists(self, player_id: str):
        for player in self.players:
            if player.id == player_id:
                return True
        return False

    def get_available_seats(self) -> int:
        available_seats = self.num_seats - len(self.players)
        return available_seats

    def get_player_via_id(self, player_id):
        for player in self.players:
            if player.id == player_id:
                return player
        return None

    def get_player_via_seat(self, seat_number):
        for seat, player_id in self.seats.items():
            if seat == seat_number:
                return self.get_player_via_id(player_id)
        return None

    def get_current_turn_player(self):
        self.logger.debug(f"getting the player for this turn")
        for player in self.players:
            if player.state == PlayerState.AWAITING_MY_TURN or player.state == PlayerState.MY_TURN:
                self.logger.debug(f"Now it is {player.name}'s turn")
                player.transition_state(PlayerState.MY_TURN)
                return player
        return None

    def player_exists(self, player_id: str):
        for player in self.players:
            if player.id == player_id:
                return True
        return False

    def get_seat_number(self, player_id):
        for seat, id in self.seats.items():
            if id == player_id:
                return seat
        return None

    def check_all_results_are_published(self):
        for player in self.players:
            if player.state != PlayerState.RESULT_NOTIFIED:
                return

        self.logger.info(f"All results are published")
        self.event_bus.publish('publish_results_done')

    def set_all_player_events(self):
        for id in self.player_events:
            self.player_events[id].set()

    def clear_all_player_events(self):
        for id in self.player_events:
            self.player_events[id].clear()

    def reset_all_players(self):
        for player in self.players:
            player.reset()

    def insert_split_player(self, original_player, split_player):
        try:
            original_player_position = self.players.index(original_player)
        except ValueError:
            self.logger.debug("Player not in list")
            return
        self.players.insert(original_player_position + 1, split_player)

    def reset_players(self):
        # reset each remaining player's state as needed for the next round.
        for player in self.players:
            player.reset()

    def remove_split_player(self):
        self.players = [player for player in self.players if
                        player.origin_player_id is None]
