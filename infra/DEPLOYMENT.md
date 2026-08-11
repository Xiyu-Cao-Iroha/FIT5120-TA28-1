# Deploying CalmPath to ying-iroha.online/calmpath

Target: Alibaba Cloud ECS, Ubuntu 22.04, 2 vCPU / 2 GiB, IP `47.95.227.164`.
Everything below is run **on the server**, over SSH, as root (or a sudo user).

Tested locally end-to-end before writing this (Docker build, both containers
talking to each other, a real `/routes/compare` call) — the steps here match
what was actually verified working, not just what should theoretically work.

## 0. Point the domain at the server

In Alibaba Cloud's DNS console for `ying-iroha.online` (阿里云 DNS 解析), add:

| 记录类型 | 主机记录 | 记录值 |
|---|---|---|
| A | @ | 47.95.227.164 |

DNS can take a few minutes to a few hours to propagate. You can start the
steps below while waiting — you only need DNS resolved by the time you run
`certbot` in step 6.

Also check the ECS instance's **security group** (安全组) allows inbound
TCP on ports 22, 80, and 443 — Alibaba Cloud blocks everything else by
default.

## 1. Install Docker, Docker Compose, nginx, certbot

```bash
apt update && apt upgrade -y
apt install -y ca-certificates curl gnupg nginx certbot python3-certbot-nginx git

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Node.js (for the frontend build step)
curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
apt install -y nodejs
```

## 2. Clone the repo

```bash
mkdir -p /opt/calmpath && cd /opt/calmpath
git clone https://github.com/Xiyu-Cao-Iroha/FIT5120-TA28-1.git .
git checkout main
```

If the repo is private, you'll be prompted for GitHub credentials — use a
personal access token as the password, not your account password.

## 3. Backend environment file

```bash
cd /opt/calmpath/services/api
cp .env.example .env
nano .env
```

Set it to (adjust the Google Maps key — see the note below):

```
DATABASE_URL=postgresql+psycopg://calmpath:CHANGE_THIS_PASSWORD@db:5432/calmpath
CORS_ORIGINS=https://ying-iroha.online
CBD_MIN_LAT=-37.8230
CBD_MAX_LAT=-37.8050
CBD_MIN_LON=144.9400
CBD_MAX_LON=144.9700
RATE_LIMIT_PER_MINUTE=10
GOOGLE_MAPS_API_KEY=your-key-here
USE_LIVE_MELBOURNE_OPEN_DATA=true
```

**Before going live, restrict the Google Maps key** (Google Cloud Console →
Credentials): add an HTTP referrer restriction for `https://ying-iroha.online/*`.
The key currently used for local dev is unrestricted and shouldn't be reused
as-is on a public server.

Note the password you pick — you need the same one in the next step.

## 4. Start the database and API containers

```bash
cd /opt/calmpath/infra
POSTGRES_PASSWORD=CHANGE_THIS_PASSWORD docker compose -f docker-compose.prod.yml up -d --build
```

Both containers only bind to `127.0.0.1` (not exposed to the internet
directly) — nginx in front of them handles all public traffic. Check it's
actually up:

```bash
curl http://127.0.0.1:8010/api/v1/health
```

Should return `{"status":"degraded"...}` at this point — that's expected,
it just means there's no pedestrian data seeded yet (next step).

## 5. Run migrations and seed data

```bash
cd /opt/calmpath/infra
docker compose -f docker-compose.prod.yml exec api python -m alembic upgrade head
docker compose -f docker-compose.prod.yml exec api python -m app.seed
```

## 6. Build the frontend and set up nginx

```bash
cd /opt/calmpath/apps/mobile
cp .env.example .env
nano .env
```

Set:

```
EXPO_PUBLIC_API_BASE_URL=https://ying-iroha.online/calmpath/api/v1
EXPO_PUBLIC_GOOGLE_MAPS_API_KEY=your-key-here
```

`EXPO_PUBLIC_GOOGLE_MAPS_API_KEY` needs **Maps JavaScript API** enabled on
it specifically (separate from Directions/Places) and should also be
referrer-restricted to `https://ying-iroha.online/*`.

```bash
npm install
npm run build:web
mkdir -p /var/www/calmpath
cp -r dist /var/www/calmpath/
```

Set up the nginx site:

```bash
cp /opt/calmpath/infra/nginx-calmpath.conf /etc/nginx/sites-available/calmpath
ln -s /etc/nginx/sites-available/calmpath /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

At this point `http://ying-iroha.online/calmpath/` should load over plain
HTTP. Confirm that before moving to HTTPS.

## 7. HTTPS

```bash
certbot --nginx -d ying-iroha.online
```

Certbot edits the nginx config in place to add the HTTPS server block and
redirect HTTP → HTTPS. Follow its prompts (enter an email, agree to terms).
It auto-renews via a systemd timer it installs — nothing further to do.

## 8. Verify

- `https://ying-iroha.online/calmpath/` — app loads
- `https://ying-iroha.online/calmpath/destination` — direct URL to a
  sub-route also loads (confirms the SPA fallback in the nginx config
  works, not just the root page)
- Try one of the demo scenarios end to end

## Redeploying after a code change

```bash
cd /opt/calmpath && git pull

cd services/api
docker compose -f ../infra/docker-compose.prod.yml up -d --build api

cd ../apps/mobile
npm run build:web
rm -rf /var/www/calmpath/dist
cp -r dist /var/www/calmpath/
```

No nginx or certbot changes needed for a routine redeploy.
