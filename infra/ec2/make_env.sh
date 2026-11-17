#!/usr/bin/env bash
# Create backend/.env for production on the EC2 instance, with generated secrets.
#
#   bash infra/ec2/make_env.sh                                  # SageMaker, http://<this instance's public IP>
#   bash infra/ec2/make_env.sh bedrock us-west-2                # Bedrock fallback in another region
#   bash infra/ec2/make_env.sh sagemaker us-east-1 https://clinical.example.com   # with a domain
#
# Prints the demo password once. Save it; it is also in backend/.env (readable only by you).
set -euo pipefail
cd "$(dirname "$0")/../.."

PROVIDER="${1:-sagemaker}"
REGION="${2:-us-east-1}"
PUBLIC_URL="${3:-}"
TEMPLATE=backend/.env.production.example
ENV_FILE=backend/.env

case "$PROVIDER" in sagemaker|bedrock) ;; *) echo "Provider must be sagemaker or bedrock"; exit 1 ;; esac
if [ -f "$ENV_FILE" ]; then
  echo "$ENV_FILE already exists. Remove it first if you want to regenerate (this logs everyone out)."
  exit 1
fi

if [ -z "$PUBLIC_URL" ]; then
  # Ask the EC2 metadata service (IMDSv2) for this instance's public IP.
  TOKEN=$(curl -sf --max-time 2 -X PUT "http://169.254.169.254/latest/api/token" \
          -H "X-aws-ec2-metadata-token-ttl-seconds: 60" || true)
  IP=$(curl -sf --max-time 2 -H "X-aws-ec2-metadata-token: $TOKEN" \
          http://169.254.169.254/latest/meta-data/public-ipv4 || true)
  PUBLIC_URL="http://${IP:-localhost}"
fi

JWT_SECRET=$(openssl rand -hex 32)
# Letters and digits only, so the value needs no quoting in the env file.
DEMO_PASSWORD=$(openssl rand -base64 48 | tr -dc 'A-Za-z0-9' | head -c 16)

umask 077
sed -e "s|REPLACE_PUBLIC_URL|${PUBLIC_URL}|" \
    -e "s|REPLACE_JWT_SECRET|${JWT_SECRET}|" \
    -e "s|REPLACE_DEMO_PASSWORD|${DEMO_PASSWORD}|" \
    -e "s|REPLACE_LLM_PROVIDER|${PROVIDER}|" \
    -e "s|REPLACE_AWS_REGION|${REGION}|" \
    "$TEMPLATE" > "$ENV_FILE"

echo "Wrote $ENV_FILE"
echo "  site URL : $PUBLIC_URL"
echo "  provider : $PROVIDER ($REGION)"
echo "  login    : demo / $DEMO_PASSWORD     <-- save this password"
echo "Next: docker compose up -d --build"
