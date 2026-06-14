#!/usr/bin/env bash
# Build Sphinx docs.
#
# Prerequisites (run once after cloning):
#   pip install -e ".[docs]"
#   # or, if using the pinned dev requirements:
#   pip install -r requirements-dev.txt && pip install -e .
#
# Usage:
#   ./scripts/generate_docs.sh
#
# Place images in docs/sphinx/res/ before building:
#   docs/sphinx/res/analysis/explore/   -- exploration plots
#   docs/sphinx/res/analysis/evaluate/  -- evaluation plots
#   docs/sphinx/res/tui/                -- TUI screenshots

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    echo "Usage: ./scripts/generate_docs.sh"
    echo ""
    echo "Builds the Sphinx HTML docs into docs/sphinx/out/."
    echo ""
    echo "Prerequisites (run once after cloning):"
    echo "  pip install -e \".[docs]\""
    echo ""
    echo "Place analysis/TUI images in docs/sphinx/res/ before building:"
    echo "  docs/sphinx/res/analysis/explore/   -- exploration plots"
    echo "  docs/sphinx/res/analysis/evaluate/  -- evaluation plots"
    echo "  docs/sphinx/res/tui/                -- TUI screenshots"
    exit 0
fi

set -e

SPHINX_SRC="docs/sphinx/source"
SPHINX_OUT="docs/sphinx/out"

echo "Building docs..."
sphinx-build -b html "$SPHINX_SRC" "$SPHINX_OUT"
echo "Docs built -> $SPHINX_OUT/index.html"
echo ""
echo "To view locally: python -m http.server 8080 --directory $SPHINX_OUT"
echo "Then open http://localhost:8080 in your browser."
