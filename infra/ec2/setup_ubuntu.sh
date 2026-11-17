#!/usr/bin/env bash
# One-time setup on a fresh Ubuntu 24.04 EC2 instance:  bash infra/ec2/setup_ubuntu.sh
# Installs Docker Engine + Compose plugin from Docker's official apt repo, adds swap, enables Docker.
set -euo pipefail

echo ">> System update"
sudo apt-get update -y
sudo apt-get upgrade -y
sudo apt-get install -y ca-certificates curl git unzip

echo ">> Docker apt repository"
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update -y

echo ">> Docker Engine + Compose"
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"

echo ">> 2 GB swap (keeps the npm build from running out of memory)"
if [ ! -f /swapfile ]; then
  sudo fallocate -l 2G /swapfile
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
fi

echo ">> Done. Log out and back in (or run: newgrp docker) so 'docker' works without sudo."
docker --version || true
