#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$ROOT/backups"
if [[ -f "$ROOT/data/bot.db" ]]; then
  sqlite3 "$ROOT/data/bot.db" ".backup '$ROOT/backups/bot-$STAMP.db'"
  gzip -f "$ROOT/backups/bot-$STAMP.db"
  echo "Backup created: backups/bot-$STAMP.db.gz"
else
  echo "Database not found: $ROOT/data/bot.db" >&2
  exit 1
fi
