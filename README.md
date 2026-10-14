# Rock / Paper / Scissors

A small, polished desktop version of Rock-Paper-Scissors built with Python and Tkinter. The interface uses a dark graphite palette, muted lime accents, custom-drawn icons, and subtle animations.

## Features

- Play repeated rounds against a computer opponent.
- Computer moves are selected randomly.
- Scoreboard tracks player wins, computer wins, and draws.
- Round counter and one-click reset.
- Animated choice cards, computer reveal, result display, and score updates.
- Keyboard controls: `R` for Rock, `P` for Paper, `S` for Scissors. Keys `1`, `2`, and `3` work in the same order.
- `Ctrl + R` resets the game.
- Reduced-motion support via `RPS_REDUCE_MOTION=1` or the `--reduce-motion` command-line flag.
- Game logic is kept separate from the user interface.
- No third-party Python packages are required.

## Requirements

- Python 3.10 or newer is recommended.
- Tkinter must be available in your Python installation. It is included with most standard Windows Python installations.

## Run on Windows

1. Download or clone this repository.
2. Open Command Prompt in the project folder.
3. Check that Python is installed:

   ```bat
   python --version
   ```

4. Start the game:

   ```bat
   python main.py
   ```

If `python` is not recognized, try `py main.py`. If Tkinter is missing, rerun the Python installer and ensure the Tcl/Tk support option is installed.

## Project structure

```text
rock-paper-scissors/
├── main.py
├── game_logic.py
├── requirements.txt
├── README.md
├── .gitignore
└── screenshots/
    └── .gitkeep
```

## Testing the game logic

Run this command from the project folder:

```bat
python -m unittest
```

The game rules can also be checked quickly in a Python shell:

```python
from game_logic import Game

game = Game()
print(game.play("rock", "scissors"))  # Player wins
print(game.play("rock", "paper"))     # Computer wins
print(game.play("paper", "paper"))    # Draw
```

## Screenshots

After running the game, take a screenshot and save it in the `screenshots/` folder. You can then embed it here:

```markdown
![Rock-Paper-Scissors game](screenshots/game-window.png)
```

A screenshot is not included yet because the application needs to be launched on a desktop with a graphical display.

## Upload to GitHub

Create an empty repository on GitHub, then run these commands from this project folder. Replace `YOUR-USERNAME` and `YOUR-REPOSITORY` with your GitHub details.

```bat
git init
git add .
git commit -m "Build animated Rock Paper Scissors game"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
git push -u origin main
```

If Git says a remote named `origin` already exists, check it with `git remote -v` before changing it.

## Game rules

- Rock beats Scissors.
- Scissors beats Paper.
- Paper beats Rock.
- Matching moves result in a draw.

## License

You may use and modify this project for learning and portfolio purposes. Add a license file if you want to specify formal reuse terms.
