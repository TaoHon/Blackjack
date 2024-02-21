
class PlayerAgent:
    def place_bets(self, player, bets):
        print(f"Player {player.name}, available bets: {bets}")
        while True:
            bet = input("Enter your bet amount (or type 'quit' to leave the game): ")
            if bet.lower() == 'quit':
                return 'quit'
            try:
                bet_amount = int(bet)
                if bet_amount in bets:
                    return bet_amount
                else:
                    print("Invalid bet amount. Please choose from the available bets.")
            except ValueError:
                print("Please enter a valid number or 'quit'.")

    def request_action(self, status_array, available_actions, player):
        print(status_array)
        player_action = input(f"{player.name}, choose an action: {available_actions}: ").lower()
        return player_action

    def join_game(self, player):
        join_game = input(f"{player.name}, do you want to join the game? (yes/no): ")
        if join_game.lower() == 'yes':
            player_name = input("Enter your name: ")
        else:
            player_name = None
        return player_name

