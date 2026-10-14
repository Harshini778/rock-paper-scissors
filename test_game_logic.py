import unittest
from game_logic import DRAW, LOSE, WIN, Game

class GameLogicTests(unittest.TestCase):
    def setUp(self):
        self.game = Game()

    def test_player_win(self):
        result = self.game.play("rock", "scissors")
        self.assertEqual(result.outcome, WIN)
        self.assertEqual(self.game.player_score, 1)

    def test_computer_win(self):
        result = self.game.play("rock", "paper")
        self.assertEqual(result.outcome, LOSE)
        self.assertEqual(self.game.computer_score, 1)

    def test_draw(self):
        result = self.game.play("paper", "paper")
        self.assertEqual(result.outcome, DRAW)
        self.assertEqual(self.game.draws, 1)

    def test_round_counter_and_reset(self):
        self.game.play("rock", "scissors")
        self.game.play("paper", "paper")
        self.assertEqual(self.game.rounds, 2)
        self.game.reset()
        self.assertEqual((self.game.rounds, self.game.player_score,
                          self.game.computer_score, self.game.draws), (0, 0, 0, 0))

    def test_invalid_move(self):
        with self.assertRaises(ValueError):
            self.game.play("lizard", "rock")

if __name__ == "__main__":
    unittest.main()
