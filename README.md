# maze-kluster

[![PyPI version](https://img.shields.io/pypi/v/maze-kluster?color=blue)](https://pypi.org/project/maze-kluster)
[![Python](https://img.shields.io/pypi/pyversions/maze-kluster)](https://pypi.org/project/maze-kluster)
[![License](https://img.shields.io/pypi/l/maze-kluster)](LICENSE)
[![Docs](https://img.shields.io/badge/docs-docs.anwari.nl-informational)](https://docs.anwari.nl/maze_kluster)
[![HTI](https://img.shields.io/badge/challenge-htiprojects.nl-orange)](https://htiprojects.nl)

A Python library for navigating mazes via REST API, shipping a DFS baseline bot and three ML-driven smart bots (Random Forest, Gradient-Boosted Trees, Gaussian Process), plus an optional terminal UI for live runs and replay.

## Installation

```bash
pip install maze-kluster          # core library
pip install "maze-kluster[tui]"   # + Textual terminal UI
```

## Quick start

### 1. Configure credentials

Create a `connection.json` in your working directory:

```json
{
  "base_url": "https://maze.kluster.htiprojects.nl",
  "api_key": "your-api-token"
}
```

Environment-variable substitution is supported — e.g. `"api_key": "${MY_API_KEY}"`.

### 2. Run a bot in Python

```python
from maze_kluster.api import MazeClient
from maze_kluster.bots import BaselineBot, SmartBotBase
from maze_kluster.models.rf import RFScorer

client = MazeClient.from_config("connection.json")

# DFS baseline
bot = BaselineBot(client)
result = bot.run("easy-01")
print(f"Score: {result.score_in_bag}  Moves: {result.total_moves}")

# ML-driven smart bot (pre-trained model bundled in the package)
smart_bot = SmartBotBase(client, scorer=RFScorer.load())
result = smart_bot.run("medium-03")
```

### 3. Use the BOTS registry

```python
from maze_kluster.bots import BOTS
from maze_kluster.api import MazeClient

client = MazeClient.from_config()
bot = BOTS["gbt"](client)   # "baseline" | "rf" | "gbt" | "gp"
result = bot.run("hard-02")
```

### 4. Evaluate results

```python
from maze_kluster.metrics import (
    score_efficiency,
    step_efficiency,
    collection_rate,
    exploration_completeness,
)

print(score_efficiency(result))         # fraction of potential reward collected
print(step_efficiency(result))          # reward per move
print(collection_rate(result))          # reward secured vs. lost in hand
print(exploration_completeness(result)) # fraction of tiles visited
```

## CLI

```bash
# Launch the TUI (requires maze-kluster[tui])
maze-kluster tui

# Live run with a specific bot and maze
maze-kluster tui --live --maze easy-01 --bot gbt

# Replay a saved run log
maze-kluster tui --replay run_logs/easy-01_baseline.jsonl

# List available mazes / themes
maze-kluster tui --list-mazes
maze-kluster tui --list-themes

# Custom connection file
maze-kluster tui --connection /path/to/connection.json
```

## Bots

| Name | Class | Strategy |
|---|---|---|
| `baseline` | `BaselineBot` | Depth-first search; explores fully before exiting |
| `rf` | `SmartBotBase` + `RFScorer` | Random Forest scores frontier tiles by desirability |
| `gbt` | `SmartBotBase` + `GBTScorer` | Gradient-Boosted Trees scorer |
| `gp` | `SmartBotBase` + `GPUCBScorer` | Gaussian Process with UCB acquisition |

Smart bots rank frontier nodes using a trained scorer and adjust by graph distance so nearby high-value tiles win over distant ones. Pre-trained model artifacts are bundled inside the package.

## Custom scorer

Implement `ScorerProtocol` to plug in your own model:

```python
import pandas as pd
from maze_kluster.models.protocol import ScorerProtocol
from maze_kluster.bots.smart import SmartBotBase
from maze_kluster.api import MazeClient

class MyScorer:
    def score(self, features: pd.DataFrame) -> list[float]:
        # Available columns: tile_type, actual_degree, is_dead_end,
        #                    neighbor_reward_mean, neighbor_reward_max,
        #                    unvisited_neighbors
        return [1.0] * len(features)

client = MazeClient.from_config()
bot = SmartBotBase(client, scorer=MyScorer())
bot.run("medium-01")
```

## Local development

```bash
git clone https://github.com/arsalan-anwari/maze-kluster
cd maze-kluster
pip install -e ".[dev]"
```

Or use the pinned dev requirements:

```bash
pip install -r requirements-dev.txt
pip install -e .
```

## Documentation

Full API reference, TUI walkthrough, data-generation guide, and bot evaluation analysis are at **[docs.anwari.nl/maze_kluster](https://docs.anwari.nl/maze_kluster)**.

## Requirements

- Python 3.11+
- `networkx`, `pandas`, `scikit-learn`, `pydantic`, `pyarrow`, `requests`
- `textual` (optional, for the TUI extra)

## License

Apache 2.0 — see [LICENSE](LICENSE).
