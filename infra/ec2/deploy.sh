#!/usr/bin/env bash
# Redeploy after pushing changes:  bash infra/ec2/deploy.sh
set -euo pipefail
cd "$(dirname "$0")/../.."

git pull --ff-only
docker compose up -d --build
docker image prune -f
docker compose ps
echo ">> Health:"
curl -fsS http://localhost/api/health && echo
