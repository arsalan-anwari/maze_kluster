#!/usr/bin/env bash
# Upload Sphinx HTML docs to the remote web server.
# Run from the repo root: bash scripts/upload_docs.sh
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    echo "Usage: ./scripts/upload_docs.sh"
    echo ""
    echo "Syncs docs/sphinx/out/ to the remote docs host via rsync over SSH."
    echo ""
    echo "Prerequisites:"
    echo "  ssh alias 'vimexx' configured in ~/.ssh/config with a valid key"
    echo "  docs must already be built (run scripts/generate_docs.sh first)"
    exit 0
fi

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOCAL_DIR="$ROOT/docs/sphinx/out/"
REMOTE_HOST="vimexx"
REMOTE_DIR="/home/u214998p479997/domains/anwari.nl/public_html/docs/maze_kluster"

if [[ ! -d "$LOCAL_DIR" ]]; then
    echo "Error: $LOCAL_DIR does not exist. Run scripts/generate_docs.sh first."
    exit 1
fi

echo "Uploading docs to $REMOTE_HOST:$REMOTE_DIR ..."
rsync -avz --delete "$LOCAL_DIR" "$REMOTE_HOST:$REMOTE_DIR"

echo "Done! Docs published to https://anwari.nl/docs/maze_kluster"
