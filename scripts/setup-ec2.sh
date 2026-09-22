#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
#  Cloud Cost Intelligence — EC2 Bootstrap & Deployment Setup Script
#  Run this ONCE on a fresh Ubuntu 22.04 / 24.04 EC2 instance.
#  Usage: bash scripts/setup-ec2.sh
# ─────────────────────────────────────────────────────────────────────────────
set -e

REPO_URL="https://github.com/vishnu/cloud-cost-intelligence.git"
APP_DIR="/home/ubuntu/cloud-cost-intelligence"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ⚡ Cloud Cost Intelligence — EC2 Server Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── 1. System Packages Update ────────────────────────────────────────────────
echo "📦 Updating system packages..."
sudo apt-get update -y && sudo apt-get upgrade -y
sudo apt-get install -y git curl wget unzip nginx certbot python3-certbot-nginx

# ── 2. Install Docker ────────────────────────────────────────────────────────
echo "🐳 Installing Docker Engine..."
if ! command -v docker &> /dev/null; then
  curl -fsSL https://get.docker.com | sh
  sudo usermod -aG docker ubuntu
  sudo systemctl enable docker
  sudo systemctl start docker
else
  echo "   Docker is already installed."
fi

# ── 3. Install Docker Compose Plugin ──────────────────────────────────────────
echo "📦 Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
  COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep '"tag_name"' | sed -E 's/.*"([^"]+)".*/\1/')
  sudo curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
  sudo chmod +x /usr/local/bin/docker-compose
fi
docker-compose --version

# ── 4. Set up Application Directory ───────────────────────────────────────────
echo "📥 Checking application repository..."
if [ -d "$APP_DIR" ]; then
  echo "   Application directory exists at $APP_DIR. Pulling latest main branch..."
  cd $APP_DIR && git pull origin main || true
else
  echo "   Cloning repository to $APP_DIR..."
  git clone $REPO_URL $APP_DIR || mkdir -p $APP_DIR
fi
cd $APP_DIR

# ── 5. Generate Production .env ───────────────────────────────────────────────
if [ ! -f "$APP_DIR/.env" ]; then
  echo "⚙️  Generating production .env configuration..."
  SECRET_KEY=$(openssl rand -hex 32 2>/dev/null || echo "prod-secret-key-$(date +%s)")
  POSTGRES_PASS=$(openssl rand -hex 16 2>/dev/null || echo "finops_pass_$(date +%s)")
  PUBLIC_IP=$(curl -s http://checkip.amazonaws.com || echo "localhost")

  cat <<EOF > $APP_DIR/.env
ENVIRONMENT=production
DEBUG=false
DEMO_MODE=true
APP_NAME="AWS Cost Intelligence"
PRODUCT_NAME="cloud-cost-intelligence"
SECRET_KEY=${SECRET_KEY}
DATABASE_URL=postgresql://finops:${POSTGRES_PASS}@postgres:5432/cloud_cost_db
POSTGRES_USER=finops
POSTGRES_PASSWORD=${POSTGRES_PASS}
POSTGRES_DB=cloud_cost_db
CORS_ORIGINS=http://${PUBLIC_IP},http://localhost:5173,http://localhost:80
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://${PUBLIC_IP}/auth/callback
VITE_API_BASE_URL=http://${PUBLIC_IP}/api/v1
EOF
  echo "   .env created successfully."
fi

# ── 6. Configure Nginx Reverse Proxy ──────────────────────────────────────────
echo "🌐 Configuring Nginx reverse proxy..."
PUBLIC_IP=$(curl -s http://checkip.amazonaws.com || echo "localhost")

sudo tee /etc/nginx/conf.d/cloud-cost-intelligence.conf > /dev/null << NGINX
server {
    listen 80;
    server_name ${PUBLIC_IP} _;

    client_max_body_size 50M;

    # Frontend Single Page App
    location / {
        proxy_pass http://localhost:5173;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_cache_bypass \$http_upgrade;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_read_timeout 120s;
    }

    # API Health Endpoint
    location /health {
        proxy_pass http://localhost:8000/health;
    }
}
NGINX

sudo rm -f /etc/nginx/conf.d/default.conf
sudo nginx -t && sudo systemctl reload nginx

# ── 7. Configure Systemd Auto-restart Service ─────────────────────────────────
echo "⚙️  Creating systemd service..."
sudo tee /etc/systemd/system/cloud-cost-intelligence.service > /dev/null << SERVICE
[Unit]
Description=Cloud Cost Intelligence Platform
Requires=docker.service
After=docker.service network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=${APP_DIR}
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
SERVICE

sudo systemctl daemon-reload
sudo systemctl enable cloud-cost-intelligence.service

# ── 8. Launch Containers ──────────────────────────────────────────────────────
echo "🚀 Building and starting Docker containers..."
docker-compose up -d --build

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ Setup Completed Successfully!"
echo "  URL: http://${PUBLIC_IP}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
