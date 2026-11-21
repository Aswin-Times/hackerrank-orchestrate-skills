#!/usr/bin/env sh
# Install the hr-orchestrate skills for Claude Code.
#   ./scripts/install.sh            -> ~/.claude/skills (all projects)
#   ./scripts/install.sh --project DIR -> DIR/.claude/skills (one challenge repo)
set -eu
here=$(cd "$(dirname "$0")/.." && pwd)
dest="$HOME/.claude/skills"
if [ "${1:-}" = "--project" ]; then
  [ -n "${2:-}" ] || { echo "usage: $0 [--project DIR]"; exit 2; }
  dest="$2/.claude/skills"
fi
mkdir -p "$dest"
for d in "$here"/skills/hr-orchestrate*; do
  name=$(basename "$d")
  rm -rf "$dest/$name"
  cp -R "$d" "$dest/$name"
  echo "installed $name -> $dest/$name"
done
echo "Done. Start a Claude Code session in the challenge repo and say: use hr-orchestrate"
