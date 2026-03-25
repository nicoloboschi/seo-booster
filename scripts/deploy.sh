#!/usr/bin/env bash
# Deploy built Hugo site to gh-pages branch.
# Usage: ./scripts/deploy.sh
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR"

echo "Building Hugo site..."
hugo --minify

DEPLOY_DIR=$(mktemp -d)
trap "rm -rf $DEPLOY_DIR" EXIT

REMOTE_URL=$(git remote get-url origin)

# Clone gh-pages into temp dir (or create orphan)
DEPLOY_REPO="$DEPLOY_DIR/repo"
if git ls-remote --heads origin gh-pages 2>/dev/null | grep -q gh-pages; then
    git clone --branch gh-pages --single-branch --depth 1 "$REMOTE_URL" "$DEPLOY_REPO"
    # Remove all tracked content (keep .git)
    cd "$DEPLOY_REPO"
    git rm -rf . > /dev/null 2>&1 || true
    cd "$REPO_DIR"
else
    mkdir -p "$DEPLOY_REPO"
    git -C "$DEPLOY_REPO" init
    git -C "$DEPLOY_REPO" checkout --orphan gh-pages
    git -C "$DEPLOY_REPO" remote add origin "$REMOTE_URL"
fi

# Copy built site into deploy repo
cp -r public/* "$DEPLOY_REPO/"
touch "$DEPLOY_REPO/.nojekyll"

# Commit and push
cd "$DEPLOY_REPO"
git add -A
if git diff --staged --quiet 2>/dev/null; then
    echo "No changes to deploy."
    exit 0
fi

TIMESTAMP=$(date "+%Y-%m-%d %H:%M")
git commit -m "Deploy $TIMESTAMP"
git push origin gh-pages --force

echo "Deployed successfully."
