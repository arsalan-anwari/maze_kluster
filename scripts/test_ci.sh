#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Run each CI job individually using act (mirrors GitHub Actions order).

Options:
  -h, --help    Show this help message and exit

Environment:
  ACT_BIN       Path to the act binary (default: act)

Jobs run in order:
  lint           ruff check + format check
  typecheck      mypy src/
  test (3.11)    pytest on Python 3.11
  test (3.12)    pytest on Python 3.12
  build          build wheel artifact

Tip: run 'act push -j lint' first to pull the runner image (~500 MB one-time download).
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
    exit 0
fi

ACT_BIN="${ACT_BIN:-act}"

run_job() {
    local label="$1"
    shift
    echo ""
    echo "=========================================="
    echo " $label"
    echo "=========================================="
    "$ACT_BIN" push "$@"
}

run_job "Lint"                          -j lint
run_job "Type check"                    -j typecheck
run_job "Test / Python 3.11"            -j test --matrix python-version:3.11
run_job "Test / Python 3.12"            -j test --matrix python-version:3.12
run_job "Build wheel"                   -j build

echo ""
echo "All CI jobs passed."
