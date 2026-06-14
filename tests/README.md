# Tests

Run all tests from the project root:

```bash
pytest
```

## What is covered

**graph_and_bot**: unit tests for `MazeGraph` (node insertion, frontier tracking, shortest path, backtracking) and `BaselineBot` navigation logic against a mock client.

**smart_bot_and_scorers**: tests for `SmartBotBase` move selection and all three scorer implementations (RF, GBT, GP) using a shared fixture set.

**feature_engineering**: tests for `prepare_features()` and the feature column contract that scorers depend on.

**evaluation_metrics**: tests for the metric calculations used in analysis (score efficiency, step efficiency, collection rate, exploration completeness).

**data_collection**: tests for `TileLogger` (parquet write/append, flush behavior) and `RunLog` (JSONL step recording).

**tui**: tests for bot registry lookup, JSONL replay parsing, and tile rendering helpers.

## Fixtures

Shared fixtures live in `smart_bot_and_scorers/conftest.py` and provide a small pre-built graph and a mock scorer for reuse across the smart bot and scorer tests.
