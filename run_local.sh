#!/bin/zsh
# 맥에서 한 번 수집 + 화면 열기
cd "$(dirname "$0")"
[ -f .env ] && set -a && source .env && set +a
.venv/bin/python collector/run.py "$@"
echo "→ 화면: http://localhost:8810/web/  (서버가 안 떠 있으면: python3 -m http.server 8810)"
