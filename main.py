import player
import table as blackjacktable
def main():
    print("Welcome to Blackjack!")

    # Initialize the deck and players
    num_players = int(input("Enter the number of players: "))
    table = blackjacktable.Table(num_players)

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
