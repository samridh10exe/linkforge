#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://localhost}"

curl -fsS "${BASE_URL}/health"
curl -fsS "${BASE_URL}/ready"
