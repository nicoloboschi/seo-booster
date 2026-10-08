#!/usr/bin/env bash
# Tell Bing/Yandex/Seznam (IndexNow) that URLs changed or were deleted.
# Usage: bash .claude/skills/publish/indexnow.sh /articles/a/ /articles/b/ ...   (paths or full URLs)
set -euo pipefail
ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
KEY=$(basename "$(ls "$ROOT"/static/*.txt | grep -E '/[0-9a-f]{32}\.txt$' | head -1)" .txt)
HOST=aiagentmemory.org
URLS=$(for u in "$@"; do case $u in http*) echo "\"$u\"";; *) echo "\"https://$HOST$u\"";; esac; done | paste -sd, -)
curl -s -o /dev/null -w "IndexNow HTTP %{http_code} (200/202 = accepted)\n" -X POST https://api.indexnow.org/indexnow \
  -H 'Content-Type: application/json; charset=utf-8' \
  -d "{\"host\":\"$HOST\",\"key\":\"$KEY\",\"keyLocation\":\"https://$HOST/$KEY.txt\",\"urlList\":[$URLS]}"
