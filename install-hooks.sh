#!/usr/bin/env bash
# One-time setup: tell this repo to use the shared hooks in .githooks/
# so the manifest auto-regenerates on every commit.
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

chmod +x .githooks/pre-commit
git config core.hooksPath .githooks

echo "✓ Hooks installed."
echo "  core.hooksPath → .githooks"
echo "  regenerate.py will run automatically before every commit"
echo "  that touches a .html file (other than index.html)."
