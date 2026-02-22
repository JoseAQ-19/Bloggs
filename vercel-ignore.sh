#!/bin/bash
# vercel-ignore.sh — Vercel Ignored Build Step
# Only build when content/ (articles) or Hugo config/templates change.
# Scouts (data/trends_*.json) and workflow changes do NOT trigger builds.
#
# HOW TO CONFIGURE:
# In Vercel Dashboard > Project Settings > Git > Ignored Build Step:
# Set the command to: bash vercel-ignore.sh

echo "🔍 Vercel Ignore Script: Checking if build is needed..."

# Get the list of changed files in the latest commit
CHANGED_FILES=$(git diff HEAD~1 --name-only 2>/dev/null || echo "FIRST_DEPLOY")

# First deploy — always build
if echo "$CHANGED_FILES" | grep -q "FIRST_DEPLOY"; then
  echo "✅ First deploy detected. Building."
  exit 1
fi

# Check if any content, layout, config, or theme files changed
if echo "$CHANGED_FILES" | grep -qE "^(content/|layouts/|themes/|static/|config|hugo\.|assets/|archetypes/)"; then
  echo "✅ Content or template changes detected. Building."
  exit 1
fi

# Check if vercel.json or package files changed
if echo "$CHANGED_FILES" | grep -qE "^(vercel\.json|package\.json|package-lock\.json)"; then
  echo "✅ Config changes detected. Building."
  exit 1
fi

# If only data/, .github/, main.py, trend_scout.py, etc. changed — skip build
echo "🛑 Only non-content files changed (scouts, workflows, code). Skipping build."
exit 0
