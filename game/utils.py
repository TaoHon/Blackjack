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

