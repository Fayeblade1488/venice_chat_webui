#!/usr/bin/env bash
set -euo pipefail

BASE=${1:-http://localhost}

echo "[*] Checking LiteLLM..."
curl -sS ${BASE}:4000/v1/models -H "Authorization: Bearer ${LITELLM_MASTER_KEY:-sk-local}" | head -c 200 && echo

echo "[*] Checking Open WebUI..."
curl -sS ${BASE}:3001/ | head -c 200 && echo

echo "[*] Checking Perplexica..."
curl -sS ${BASE}:3000/ | head -c 200 && echo

echo "[*] Checking SearXNG..."
curl -sS ${BASE}:8085/ | head -c 200 && echo
