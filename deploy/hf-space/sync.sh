#!/usr/bin/env bash
# Copies the backend source needed to build the HF Space into this folder.
# Run from the repo root:  bash deploy/hf-space/sync.sh
# The copied files are gitignored in the main repo (see .gitignore), so they
# only exist locally and are pushed to the Hugging Face Space, never to GitHub.
set -euo pipefail

cd "$(dirname "$0")"
SRC=../..

echo "Syncing backend source into deploy/hf-space/ ..."
cp "$SRC/backend/pyproject.toml" ./pyproject.toml
cp "$SRC/backend/alembic.ini"    ./alembic.ini
rm -rf ./app ./scripts ./migrations
cp -r "$SRC/backend/app"        ./app
cp -r "$SRC/backend/scripts"    ./scripts
cp -r "$SRC/backend/migrations" ./migrations

echo "Done. Push this folder to your Space:"
echo "  cd deploy/hf-space"
echo "  git init && git add -A && git commit -m 'deploy'"
echo "  git remote add origin https://huggingface.co/spaces/<your-user>/<space-name>"
echo "  git push -f origin main"
