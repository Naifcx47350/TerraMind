# TerraMind — Hosting Guide

How to put TerraMind on the internet at **https://terramind-llm.com**, what to buy, what it costs, and how to run it afterwards.

> **Prices checked 13 Oct 2026.** Hosting prices changed several times in 2026 (Hetzner raised prices in April *and* June). Re-check the provider's own pricing page before you pay. Sources are listed at the end.

---

## 0. The short version

| Decision | Recommendation | Cost |
|---|---|---|
| Server | **Hetzner Cloud CX23** (x86, 2 vCPU, 4 GB RAM, 40 GB disk), Germany or Finland, Ubuntu 24.04 | **€5.49/mo** + ~€0.50/mo IPv4 |
| Domain | **terramind-llm.com** at Cloudflare Registrar (at-cost, no renewal markup) | ~$10.44/yr (~$11.17/yr from 1 Nov 2026) |
| HTTPS | Caddy (already in the stack), free Let's Encrypt certificate | €0 |
| OpenAI | **Visitors bring their own key**, so you pay nothing per question | €0/mo |
| One-time OpenAI cost | Building the search indexes, or **€0** if you copy them from your PC (Step 9, Option A) | < $1 once |
| **Total** | | **≈ €7 per month** |

First deploy takes about 1–2 hours, most of it waiting for DNS and the first Docker build.

---

## 1. What you are deploying

```
Visitor's browser ──HTTPS 443──► caddy ──► frontend (nginx) ──/api/*──► gateway :8000 ──► model-api :8001 ──► OpenAI
        │                                   │                                                    ▲
        └── OpenAI key stays in this tab ───┴── sent with each question as X-OpenAI-Key ─────────┘
```

| Service | Job | Public? | Measured RAM (idle, after warm-up) |
|---|---|---|---|
| caddy | HTTPS certificate, ports 80/443 | **Yes**, the only public service | ~11 MB |
| frontend | Serves the React app, rate-limits `/api/*` (20 req/min per visitor) | No (127.0.0.1:3000) | ~15 MB |
| gateway | Web API, demo answers, checks keys | No (Docker network only) | ~42 MB |
| model-api | RAG pipelines, CrossEncoder reranker (PyTorch CPU), Chroma | No (Docker network only) | ~480 MB |

Measured locally with `docker stats` on 13 Oct 2026. The whole stack uses about **0.55 GB at idle**. Answering questions adds some on top, but 4 GB leaves plenty of room. The model-api image is about **3.2 GB** on disk.

### How API keys work (bring your own key)

- There is **no OpenAI key on the server**. Each visitor pastes their own key in the welcome screen (or later via **profile menu → OpenAI access → Enter API key**).
- The key lives only in that browser tab (`sessionStorage`) and is sent with each question as an `X-OpenAI-Key` header. The model API attaches it to that one request and never writes it to disk or to the environment, so one visitor's key can never answer for another.
- Visitors without a key can click **Try the demo instead**. A badge in the top bar shows demo mode, and answers are canned samples, so nobody mistakes them for real AI.
- Usage is billed to each visitor's own OpenAI account. Your running cost is the server and the domain only.

---

## 2. Hosting options compared

| Option | Specs | Price / month | Verdict |
|---|---|---|---|
| **Hetzner CX23** | 2 vCPU x86, 4 GB, 40 GB | **€5.49** + IPv4 | ✅ **Recommended.** Enough RAM for the measured usage, same CPU architecture the image is tested on, can be resized later. |
| Hetzner CX33 | 4 vCPU x86, 8 GB, 80 GB | €8.49 + IPv4 | Upgrade path if many people use it at once. Hetzner can resize (rescale) a server in place. |
| Contabo Cloud VPS 10 | ~3–4 vCPU, 8 GB, 75 GB NVMe | ~€4.50–5.50 | Most RAM per euro, but listed prices and specs disagree between sources. Verify on contabo.com before choosing. |
| DigitalOcean Basic | 2 vCPU, 4 GB, 80 GB | ~$24 | Friendliest dashboard and docs, about 4× the price. |
| AWS Lightsail | 2 vCPU, 4 GB, 80 GB | ~$24 (with IPv4) | Choose this only if you want to stay inside AWS. |
| Oracle Cloud Always Free | 2 OCPU ARM, 12 GB | €0 | ❌ Not for something you want reliably online. Oracle cut the free limits in half on 15 Jun 2026 without notice, capacity isn't guaranteed, and it's ARM (see below). |
| Hetzner CAX (ARM) | e.g. CAX11: 2 vCPU ARM, 4 GB | €5.99 + IPv4 | ❌ Not until the image is tested on ARM. The Dockerfile installs PyTorch from the CPU wheel index, and I couldn't confirm a Python 3.11 ARM64 wheel there. |

**Why Hetzner CX23:** the stack measured ~0.55 GB at idle, so 4 GB is comfortable. x86 matches the image we built and tested. At ~€6/month it costs about a quarter of DigitalOcean or Lightsail. The trade-off is location: Hetzner's cheap plans are only in Germany and Finland, which adds a little network delay for users in the Gulf. That is small next to the several seconds the AI takes to write an answer.

Pick **Falkenstein / Nuremberg (Germany)** or **Helsinki (Finland)**. It doesn't matter much which.

---

## 3. Costs

| Item | When | Cost |
|---|---|---|
| Hetzner CX23 + primary IPv4 | Monthly | ~€6.00 |
| Hetzner automatic backups (optional) | Monthly | ~20% of the server price (~€1.10) |
| Domain terramind-llm.com (Cloudflare) | Yearly | ~$10.44 (~$11.17 after 1 Nov 2026) |
| TLS certificate (Let's Encrypt via Caddy) | — | €0 |
| OpenAI usage | Per visitor | Paid by each visitor with their own key |
| Building indexes (text-embedding-3-small at ~$0.02 per 1M tokens) | Once | < $1, or €0 with Option A |

For reference, a visitor's own cost per question with `gpt-4o-mini` ($0.15 per 1M input tokens, $0.60 per 1M output tokens) is usually a fraction of a cent.

---

## 4. Tools you need

| Where | Tool | Notes |
|---|---|---|
| Your PC | **SSH** | Built into Windows 11 (`ssh`, `ssh-keygen`, `scp` in PowerShell) |
| Your PC | Git, Docker Desktop | Already installed |
| Accounts | **Hetzner Cloud** (hetzner.com/cloud), **Cloudflare** (domain + DNS), GitHub | The repo is public, so the server can clone it without credentials |
| Server | **Ubuntu 24.04 LTS** | Chosen when creating the server |
| Server | **Docker Engine + Compose plugin** | Installed in Step 6 |
| Server | `ufw`, `unattended-upgrades` | Firewall and automatic security updates |
| Optional | A free uptime monitor (e.g. UptimeRobot) | Pings `/api/health` and emails you if the site goes down |

---

## 5. Step-by-step deployment

### Step 1 — Buy the domain
1. Create a Cloudflare account → **Domain Registration → Register Domains** → search `terramind-llm.com` → buy.
2. Cloudflare becomes your DNS provider automatically.

### Step 2 — Create an SSH key on your PC (PowerShell)
```powershell
ssh-keygen -t ed25519 -C "terramind-server"
# Press Enter for the default path; set a passphrase.
Get-Content $env:USERPROFILE\.ssh\id_ed25519.pub   # copy this line for Step 3
```

### Step 3 — Create the server (Hetzner Cloud Console)
1. **New project** → **Add Server**.
2. Location: **Falkenstein**, **Nuremberg** or **Helsinki**.
3. Image: **Ubuntu 24.04**.
4. Type: **Shared vCPU → x86 → CX23**.
5. Networking: **Public IPv4** ✅ and **IPv6** ✅.
6. SSH keys: **Add SSH key** → paste the line from Step 2.
7. Firewalls: **Create firewall** with inbound rules **TCP 22**, **TCP 80**, **TCP 443** and **UDP 443** (HTTP/3).
8. Backups: optional (+~20%).
9. Create, then copy the server's **IPv4 address**.

### Step 4 — Point the domain at the server (Cloudflare → DNS)
| Type | Name | Content | Proxy |
|---|---|---|---|
| A | `@` | your server IPv4 | **DNS only (grey cloud)** |
| AAAA | `@` | your server IPv6 (optional) | DNS only |

Keep the proxy **off** (grey cloud), so Caddy can get its certificate directly from Let's Encrypt. Check from your PC:
```powershell
Resolve-DnsName terramind-llm.com   # should show your server IP (can take a few minutes)
```

### Step 5 — First login and basic hardening
```bash
ssh root@YOUR_SERVER_IP

apt update && apt upgrade -y
adduser deploy                      # pick a strong password
usermod -aG sudo deploy
rsync --archive --chown=deploy:deploy ~/.ssh /home/deploy

# Key-only logins, no root over SSH
sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin no/; s/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart ssh

# Firewall + automatic security updates
apt install -y ufw unattended-upgrades
ufw allow OpenSSH && ufw allow 80/tcp && ufw allow 443/tcp && ufw allow 443/udp
ufw --force enable
exit
```
Open a **new** terminal and confirm `ssh deploy@YOUR_SERVER_IP` works **before** closing the root session.

> Docker publishes ports past `ufw`. That's fine here: the only published ports are 80/443 (meant to be public) and `127.0.0.1:3000` (localhost only). The Hetzner firewall from Step 3 is the outer guard.

### Step 6 — Install Docker
```bash
ssh deploy@YOUR_SERVER_IP
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker deploy
exit                                 # log out and back in so the group applies
ssh deploy@YOUR_SERVER_IP
docker compose version               # should print v2.x
```

### Step 7 — Get the code
```bash
git clone https://github.com/Naifcx47350/TerraMind.git
cd TerraMind
```
The corpus (PDFs and product catalog) is in the repo, so nothing else needs uploading.

### Step 8 — Check the Caddyfile
`docker/caddy/Caddyfile` already starts with `terramind-llm.com {`. Change it only if you use a different domain. **No `.env` file is needed**: there is no server API key.

### Step 9 — Load the search indexes (pick one)

**Option A — copy them from your PC (recommended: no key on the server, €0).**
On your PC (PowerShell, in the TerraMind folder):
```powershell
docker run --rm -v terramind-vectorstore:/v -v "${PWD}:/backup" alpine tar czf /backup/vectorstore.tgz -C /v .
scp vectorstore.tgz deploy@YOUR_SERVER_IP:~/TerraMind/
```
On the server:
```bash
cd ~/TerraMind
docker volume create terramind-vectorstore
docker run --rm -v terramind-vectorstore:/v -v "$PWD:/backup" alpine tar xzf /backup/vectorstore.tgz -C /v
rm vectorstore.tgz
```

**Option B — build them on the server (needs your key once, < $1).**
```bash
cd ~/TerraMind
docker compose build model-api
read -rs OPENAI_API_KEY && export OPENAI_API_KEY   # paste your key; it is not echoed or saved to history
docker compose --profile init run --rm init-indexes
unset OPENAI_API_KEY
```

### Step 10 — Start TerraMind
```bash
docker compose up -d --build        # first build: ~10–20 min (PyTorch is a ~200 MB download)
docker compose ps                   # wait until gateway and model-api show "healthy"
```

### Step 11 — Check it works
```bash
curl -sI https://terramind-llm.com | head -1          # HTTP/2 200
curl -s https://terramind-llm.com/api/config           # {"model_api_ready":true,...,"demo_available":true}
curl -s https://terramind-llm.com/api/ask -H 'Content-Type: application/json' \
     -d '{"question":"test"}'                           # {"detail":"Add your OpenAI API key ..."}  (401 = correct)
```
Then in a browser:
- [ ] The welcome screen asks for a key and offers **Try the demo instead**
- [ ] Demo: the **Demo · sample answers** badge shows, and the three starter prompts get sample answers
- [ ] Profile menu → **OpenAI access** shows the mode; **Enter API key** opens the key screen
- [ ] A real key: one Auto question, one photo question, one Compare question all answer
- [ ] A wrong key shows "OpenAI did not accept this key"
- [ ] The padlock shows a valid certificate for terramind-llm.com

---

## 6. Running it day to day

| Task | Command (on the server, in `~/TerraMind`) |
|---|---|
| Deploy an update | `git pull && docker compose up -d --build` |
| Status | `docker compose ps` |
| Logs | `docker compose logs -f --tail=100 model-api` (or `gateway`, `caddy`) |
| Restart everything | `docker compose restart` |
| RAM/CPU per service | `docker stats --no-stream` |
| Free disk after updates | `docker image prune -f` |
| Rebuild indexes after data changes | Step 9 Option B, then `docker compose restart model-api` |

**Backups:** the only state on the server is the index volume, which can be rebuilt from the repo. Chat history lives in each visitor's browser. Hetzner backups or a snapshot before big updates are enough.

**Monitoring:** point a free uptime monitor at `https://terramind-llm.com/api/health`.

---

## 7. Privacy and limits to know about

1. **`/api/history` (recent questions log) is off by default.** Nothing is recorded and the route returns 404. To use it for debugging, set `HISTORY_ADMIN_TOKEN=<long random string>` in the server's `.env`, restart, and send the token as a header: `curl -H "X-Admin-Token: <token>" https://terramind-llm.com/api/history`. It keeps only the last 200 entries, in memory.
2. **Visitor keys pass through your server** in memory, for one request, and are not logged (nginx doesn't log request headers). The welcome screen says this. Keep it that way: never add header logging.
3. **Rate limit** is 20 requests/min per visitor (burst 10) on `/api/*`. Raise it in `docker/frontend/nginx.conf` if real users hit it.

### Security measures already in place

| Area | Protection |
|---|---|
| Browser | Content-Security-Policy (only this site's scripts, images and API calls, which blocks key theft by injected content), `X-Frame-Options: DENY`, `nosniff`, `Referrer-Policy: no-referrer`, HSTS (Caddy) |
| Cross-site calls | CORS is off: other websites can't call the API from a visitor's browser. Opt in with `CORS_ORIGINS` only if needed. |
| Request size | Caddy and nginx refuse bodies over 10 MB (413). The API also limits history (40 messages × 20k chars), image size (~6 MB) and image type (JPEG/PNG/WebP/GIF). The browser shrinks photos to ≤1600 px before upload. |
| Errors | Unexpected errors show a generic message. Details stay in the server log. `/api/health` reports status only. |
| Containers | Only Caddy is public. The gateway runs as a non-root user. |
| Answers | Rendered as Markdown without raw HTML; `javascript:` links stripped. |

**Known and accepted:** `chromadb 1.5.9` has published advisories (PYSEC-2026-311, -3813, -3814, -3815), all in Chroma's **HTTP server** mode. TerraMind runs Chroma embedded inside the model API and never starts that server, so they don't apply. Upgrade once a fixed release is out. The model-api container still runs as root: switching needs a full image rebuild and a change to the index volume's file ownership, so do it as a tested follow-up.

---

## 8. Pre-deploy test results (13 Oct 2026, local)

| Check | Result |
|---|---|
| Backend tests (`pytest tests/`) | ✅ 78 passed (key isolation, request limits, vision off the event loop) |
| Gateway tests (`cd web && pytest tests/`) | ✅ 33 passed (history lockdown, size/role/MIME limits, CORS, error and health redaction) |
| Dependency audit (`npm audit`, `pip-audit`) | ✅ npm 0; gateway Python 0; chromadb advisories don't apply (server mode only, see Section 7) |
| Security headers, CORS, non-root gateway, 413 on 12 MB upload, streaming not buffered | ✅ checked through Caddy (first token 7 ms) |
| Frontend production build (`vite build`) | ✅ built |
| `caddy validate` (domain Caddyfile) | ✅ valid |
| `nginx -t` + real visitor IP reaches the rate limiter | ✅ |
| Full stack through Caddy (`http://localhost`), new gateway + frontend images, new `core/` code | ✅ details below |
| ↳ Homepage / `/api/config` | ✅ 200, `model_api_ready: true`, `demo_available: true` |
| ↳ Question with no key / placeholder key | ✅ 401 / 400 with a clear message |
| ↳ Demo session: stream, compare, Arabic prompt | ✅ sample answers, `system: mock`, Arabic answer for the Arabic prompt |
| ↳ Visitor key reaches OpenAI (test with a fake key) | ✅ OpenAI answers "Incorrect API key provided", so the visitor's key is used, not a server key |
| ↳ model-api container has **no** `OPENAI_API_KEY` in its environment | ✅ |
| ↳ Old "save key on server" endpoint | ✅ removed (404) |
| ↳ Ports 8000/8001 reachable from outside | ✅ not reachable |
| ↳ Rate limit: 35 rapid requests | ✅ 11 × 200, then 24 × 429 |
| Real answer with a working OpenAI key | ⏳ not yet run: the key in the local `.env` is rejected by OpenAI. Do it in Step 11 with a fresh key. |
| Full `model-api` image rebuild | ⏳ PyTorch download kept failing on the home connection. The local test reused the existing image with the new code mounted. The server builds it in Step 10. |

---

## 9. Troubleshooting

| Symptom | Likely cause → fix |
|---|---|
| Browser shows a certificate error | DNS not pointing at the server yet, Cloudflare proxy is orange, or port 80 is blocked. Check Step 4 and the firewall, then `docker compose logs caddy`. |
| Site loads but stays on "Starting TerraMind…" | model-api still loading or unhealthy → `docker compose logs model-api`. Missing indexes → Step 9. |
| "OpenAI did not accept this key" | The key was copied incompletely or revoked. Create a new one at platform.openai.com/api-keys. |
| Answers fail with a quota/billing message | The visitor's OpenAI account has no credit. They need to add billing in their OpenAI account. |
| HTTP 429 errors | The rate limit (Section 7.3). |
| Server runs out of memory | `docker stats` → resize to CX33 in the Hetzner console (Rescale). |

---

## Sources

- Hetzner price adjustment (15 Jun 2026), official: https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/
- Hetzner IPv4/backup notes: https://costgoat.com/pricing/hetzner · https://kuberns.com/blogs/hetzner-cloud-pricing/ · https://www.bitdoze.com/hetzner-cloud-cost-optimized-plans/
- Hetzner 2026 increases overview: https://northflank.com/blog/hetzner-cloud-server-price-increases
- DigitalOcean Droplet pricing 2026: https://costbench.com/software/cloud-infrastructure/digitalocean/ · https://fluence.ai/blog/digitalocean-droplets-vs-fluence/
- AWS Lightsail pricing 2026: https://cloudburn.io/blog/amazon-lightsail-pricing · https://whichdevtool.com/tools/aws-lightsail/
- Contabo pricing 2026: https://learnwithhasan.com/self-hosting-hub/vps-providers/contabo-vps/ · https://hostingcompass.com/en/providers/contabo/vps
- Oracle Always Free cut (Jun 2026): https://www.infoq.com/news/2026/07/oracle-cloud-free-tier-limits/ · https://linuxiac.com/oracle-quietly-cuts-free-tier-ampere-a1-resources-in-half/
- Cloudflare Registrar .com pricing: https://tld-list.com/registrars/cloudflare · https://startupowl.com/reviews/cloudflare-registrar
- OpenAI model pricing (gpt-4o-mini, text-embedding-3-small): https://pricepertoken.com/pricing-page/model/openai-gpt-4o-mini · https://www.layer3labs.io/guides/openai-embedding-models-pricing
- PyTorch on aarch64 (why ARM is untested): https://pytorch.org/?p=83473
