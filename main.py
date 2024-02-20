from game.table import Table

def main():
    print("Welcome to Blackjack!")

    # Initialize the deck and players
    num_players = int(input("Enter the number of players: "))
    table = Table(num_players)

    while True:
        # Start a new round
        table.play_round()
        table.cleanup_after_round()

        # Check if players want to continue or exit the game
        if input("Play another round? (y/n): ").lower() != 'y':
            print("Thanks for playing!")
            break


if __name__ == "__main__":
    main()
