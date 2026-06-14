#!/usr/bin/env bash
# Build and upload maze-kluster to PyPI.
# Run from the repo root: bash scripts/upload_library.sh
# Requires: pip install build twine
# Requires: PYPI_API_KEY env var set (or ~/.pypirc configured)
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    echo "Usage: ./scripts/upload_library.sh"
    echo ""
    echo "Builds the maze-kluster wheel and uploads it to PyPI."
    echo ""
    echo "Prerequisites:"
    echo "  pip install build twine"
    echo "  export PYPI_API_KEY=<your-token>  (or configure ~/.pypirc)"
    echo ""
    echo "Steps performed:"
    echo "  1. Copy model artifacts (rf.pkl, gbt.pkl, gp.pkl) into package data"
    echo "  2. Build wheel with 'python -m build --wheel'"
    echo "  3. Upload to PyPI via twine"
    echo "  4. Remove copied model artifacts"
    exit 0
fi

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "[1/4] Copying model artifacts into package data..."
cp "$ROOT/models/rf.pkl"  "$ROOT/src/maze_kluster/models/data/rf.pkl"
cp "$ROOT/models/gbt.pkl" "$ROOT/src/maze_kluster/models/data/gbt.pkl"
cp "$ROOT/models/gp.pkl"  "$ROOT/src/maze_kluster/models/data/gp.pkl"

echo "[2/4] Building wheel..."
cd "$ROOT"
rm -rf dist/
python -m build --wheel

echo "[3/4] Uploading to PyPI..."
TWINE_USERNAME=__token__ \
TWINE_PASSWORD="${PYPI_API_KEY}" \
  twine upload dist/*.whl

echo "[4/4] Cleaning up copied model artifacts..."
rm "$ROOT/src/maze_kluster/models/data/rf.pkl"
rm "$ROOT/src/maze_kluster/models/data/gbt.pkl"
rm "$ROOT/src/maze_kluster/models/data/gp.pkl"

echo "Done! Package published to PyPI."
