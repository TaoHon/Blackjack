import re


def convert_card_code(card):
    if card == 888:
        return "📄"

    suit = '♠♥♣♦'[card // 100 - 1]
    value = card % 100
    if value == 1:
        face_value = 'A'
    elif value == 11:
        face_value = 'J'
    elif value == 12:
        face_value = 'Q'
    elif value == 13:
        face_value = 'K'
    else:
        face_value = str(value)

    return (f"{suit}{face_value}")


def convert_actions(actions):
    # Define a dictionary to map full actions to their codes
    action_codes = {
        "Hit (h)": "h",
        "Stand (s)": "s",
        "Double Down (d)": "d",
        "Split (p)": "p"
    }

    # Use list comprehension to convert each action in the list to its code
    converted_actions = [action_codes[action] for action in actions]

    return converted_actions
