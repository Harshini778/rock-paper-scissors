"""Game rules and score tracking for Rock / Paper / Scissors."""
from dataclasses import dataclass
import random

CHOICES = ("rock", "paper", "scissors")
WIN = "win"
LOSE = "lose"
DRAW = "draw"

BEATS = {
    "rock": "scissors",
    "paper": "rock",
    "scissors": "paper",
}

@dataclass(frozen=True)
class RoundResult:
    number: int
    player: str
    computer: str
    outcome: str
    explanation: str

class Game:
    """Stores scores and resolves rounds independently of the interface."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.rounds = 0
        self.player_score = 0
        self.computer_score = 0
        self.draws = 0

    def play(self, player, computer):
        if player not in CHOICES:
            raise ValueError(f"Invalid player choice: {player!r}")
        if computer not in CHOICES:
            raise ValueError(f"Invalid computer choice: {computer!r}")

        self.rounds += 1
        if player == computer:
            outcome = DRAW
            explanation = "Both players chose the same move."
            self.draws += 1
        elif BEATS[player] == computer:
            outcome = WIN
            explanation = f"{player.title()} beats {computer}."
            self.player_score += 1
        else:
            outcome = LOSE
            explanation = f"{computer.title()} beats {player}."
            self.computer_score += 1

        return RoundResult(
            number=self.rounds,
            player=player,
            computer=computer,
            outcome=outcome,
            explanation=explanation,
        )

def computer_choice():
    """Return a random computer move."""
    return random.choice(CHOICES)
