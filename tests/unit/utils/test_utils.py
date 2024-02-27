import unittest
from game import utils


class TestCardCode(unittest.TestCase):

    def test_convert_card_code_paper(self):
        card = 888
        result = utils.convert_card_code(card)
        self.assertEqual(result, "📄")

    def test_convert_card_code_spade_ace(self):
        card = 101
        result = utils.convert_card_code(card)
        self.assertEqual(result, "♠A")

    def test_convert_card_code_heart_jack(self):
        card = 211
        result = utils.convert_card_code(card)
        self.assertEqual(result, "♥J")

    def test_convert_card_code_club_queen(self):
        card = 312
        result = utils.convert_card_code(card)
        self.assertEqual(result, "♣Q")

    def test_convert_card_code_diamond_king(self):
        card = 413
        result = utils.convert_card_code(card)
        self.assertEqual(result, "♦K")

    def test_convert_card_code_diamond_five(self):
        card = 405
        result = utils.convert_card_code(card)
        self.assertEqual(result, "♦5")


class TestConvertActions(unittest.TestCase):
    def setUp(self):
        self.actions = [
            "Hit (h)",
            "Stand (s)",
            "Double Down (d)",
            "Split (p)",
            "Insurance (i)"
        ]

    def test_convert_actions(self):
        result = utils.convert_actions(self.actions)
        expected_result = ["h", "s", "d", "p", "i"]
        self.assertEqual(result, expected_result, "Converted actions are incorrect")


if __name__ == "__main__":
    unittest.main()
