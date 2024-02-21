import logging
import argparse

from game.table import Table

logger = logging.getLogger(__name__)

# Set the level of logger to DEBUG. This means we want to catch all log messages
logger.setLevel(logging.DEBUG)

def main():
    parser = argparse.ArgumentParser(description="Define the number of players.")
    parser.add_argument('-p', '--num_players', type=int, required=True, help="The number of players")
    parser.add_argument('-d', '--num_decks', type=int, required=True, help="The number of decks")

    args = parser.parse_args()

    num_players = args.num_players
    num_decks = args.num_decks
    print(f"Number of players: {num_players}")

    table = Table(num_players, num_decks)

    while True:
        # Start a new round
        table.wait_for_players()
        table.play_round()
        table.cleanup_after_round()

if __name__ == "__main__":
    main()
