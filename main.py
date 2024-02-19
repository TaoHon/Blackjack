# lets make a blackjack game with the following rotation:
# cards are represented by a number, the first digit is the suit, the second digit is the value
# suits: 1 = spade, 2 = heart, 3 = club, 4 = diamond
# values: 1 = ace, 2-10 = 2-10, 11 = jack, 12 = queen, 13 = king
# spade[101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113]
# heart[201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213]
# club[301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313]
# diamond[401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413]

# tables are represented by a 2d array
# table[0] = dealer 
# table[1] = player1
# ...

# example:
# dealer  [101,102]
# player1 [0,0]
# player2 [0,0]
# player3 [201,202]
# player4 [301,302]
# player5 [0,0]
# player6 [301,302]
# player7 [0,0]

# players bet and amoutn of money can be represented by a number array
# [1, 100] (1 for the bet action, 100 for the number of chips)
# [2] (just the action number, since no additional information is needed)
# [3]
# [4]
# [5]
# [6]



'''

To represent the user actions in your blackjack game as a number array, you can assign each action a unique number and use those numbers to interpret the actions. Here’s a suggestion for mapping actions to numbers:

Bet: 1
Hit: 2
Stand: 3
Double Down: 4
Split: 5
Insurance: 6
Exit: 0
Number of bets: This can be represented by the actual number of chips or money the player wants to bet. It could be included as the second element of the array whenever the Bet action (1) is chosen.
For example, user actions could be represented in the array format as follows:

To bet 100 chips: [1, 100] (1 for the bet action, 100 for the number of chips)
To hit: [2] (just the action number, since no additional information is needed)
To stand: [3]
To double down: [4] (assuming the double down bet is automatically the same as the initial bet, no additional number is needed unless you want to specify another amount)
To split: [5] (this is applicable only when the player has two cards of the same value)
To take insurance: [6] (this is typically offered when the dealer's visible card is an Ace)
To exit the game: [0]
Keep in mind that for some actions like split and insurance, you might need to check for specific conditions in the game state before allowing these actions. For instance, a split is only possible if the player's two cards are of the same rank, and insurance is typically offered only when the dealer's upcard is an Ace.

This approach allows you to easily extend the game with more actions in the future by just adding more numbers to represent new actions. It also makes parsing the player's input straightforward since you're dealing with a simple numeric array.
'''
import random

# Define the plastic card
PLASTIC_CARD = 999
SHOULD_SHUFFLE = False
MONEY = 0

def generate_deck():
    # Define the deck of cards
    deck = [101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113,
            201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213,
            301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313,
            401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413] * 8  # 8 decks

    # Add the plastic card to the deck
    deck.append(PLASTIC_CARD)

    # Shuffle the deck
    random.shuffle(deck)

    return deck

def initialize_game():
    # Define the deck of cards
    deck = generate_deck()

    # Shuffle the deck
    random.shuffle(deck)

    # Initialize the table with no players
    table = [[0, 0] for _ in range(8)]  # 8 seats at the table

    return deck, table

def handle_plastic_card(deck):
    global SHOULD_SHUFFLE
    # The cut card is a solid-color plastic card. After a player cuts the cards, the dealer then inserts the cut card into the deck. When he reaches the cut card while dealing cards, he knows it’s time to shuffle after the hand is completed.
    # Shuffle the deck
    SHOULD_SHUFFLE = True
    card = draw_card(deck)
    return card

def draw_card(deck):
    if card is None:
        deck = generate_deck()  
    
    # Take the top card from the deck
    card = deck.pop(0)

    # Check if the card is the plastic card
    if card == PLASTIC_CARD:
        card = handle_plastic_card()
    return card

def deal_cards(deck, table):
    global SHOULD_SHUFFLE
    # Deal two cards to each seat at the table, including the dealer
    for _ in range(2):
        for player in table:
            card = draw_card(deck)
            player[0 if player[0] == 0 else 1] = card  # Assign card to the first or second slot
    return deck, table

def bet(amount):
    global MONEY
    MONEY -= amount  # Deduct the bet from the player's money

def hit(deck, player):
    card = draw_card(deck)
    # Add the card to the player's hand (assuming first two slots are for initial cards)
    if player[0] == 0:
         player[0] = card
    elif player[1] == 0:
        player[1] = card
    else:
        player.append(card)  # Add additional cards if the first two slots are filled
    # No need to handle the empty deck here since draw_card already does

def stand(player):
    # Standing does not require changes to the player's state, just ends their turn
    pass

def double_down(deck, player):
    player[3] -= player[2]  # Deduct the additional bet
    player[2] *= 2  # Double the bet
    hit(deck, player)  # Deal one additional card

def split(deck, player):
    # Placeholder for split logic; you'll need to check if the player's first two cards are of the same value
    pass

def insurance(player):
    # Placeholder for insurance logic; typically offered when the dealer's visible card is an Ace
    pass

def exit_game(player):
    # Placeholder for handling player exit; might involve cleaning up the player's state or saving the game
    pass

  



