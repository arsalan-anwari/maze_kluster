# maze-kluster

A maze-solving bot library with a DFS baseline, three ML-driven smart bots, and a terminal UI. Built as part of the HTI maze-kluster assignment.

## Install

```bash
pip install maze-kluster
```

With the terminal UI:

```bash
pip install "maze-kluster[tui]"
```

### Local development (cloned repo)

Install the package in editable mode with the extras you need:

```bash
# everything (recommended for contributors)
pip install -e ".[dev]"

# just the terminal UI
pip install -e ".[tui]"

# just the docs toolchain
pip install -e ".[docs]"
```

Alternatively, use the pinned dev requirements file:

```bash
pip install -r requirements-dev.txt
pip install -e .
```

## Setup

Create a `connection.json` in the project root:

```json
{
  "base_url": "https://maze.example.com",
  "token": "your-token",
  "player": {
    "id": 0,
    "name": "your-name"
  }
}
```

Values can be pulled from environment variables using `${VAR_NAME}` syntax. Verify the connection with:

```bash
maze-kluster tui --list-mazes
```

## Generate training data and models

```bash
python data/generate.py      # runs baseline bot on training mazes
python models/generate.py    # trains RF, GBT, and GP scorers
```

Add `--reset` to the first command if you need to wipe session progress and start over.

## Run the TUI

```bash
maze-kluster tui
```

Pick a maze, pick a bot, and choose between a live run or a recorded replay. See [the docs](docs.anwari.nl/maze_kluster) for a full walkthrough and CLI reference.

## Docs

```bash
./scripts/generate_docs.sh
python -m http.server 8080 --directory docs/sphinx/out
```

## License

Apache 2.0. See [LICENSE](LICENSE).
