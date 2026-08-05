
<img width="1280" height="640" alt="sparxstar-event-horizon" src="https://github.com/user-attachments/assets/16f804e4-2bc9-4b0a-a3fc-eeb675529e1d" />

# SPARXSTAR Event Horizon v2.1

> **"Nothing malicious escapes."**

**Event Horizon** is a high-performance, carrier-grade Nginx firewall designed for zero-latency threat mitigation. It drops malicious connections immediately (Ghosting Protocol) before they consume application resources, protecting your upstream against DDoS, bots, SQLi, XSS, and brute-force attacks.

Event Horizon is a **detection intelligence core** — it deliberately does not enforce runtime performance tuning (buffers, timeouts, keepalive). Keep those in your platform adapter or base Nginx profile.

---

## 🏗️ Architecture

Event Horizon sits between Cloudflare's edge and your application layer. Placing the firewall *behind* the application server defeats the Ghosting Protocol.

```text
Internet
   ↓
Cloudflare Edge        (absorbs volumetric DDoS, terminates TLS)
   ↓
SPARXSTAR Event Horizon (Nginx — threat evaluation & ghosting)
   ↓
Application Layer      (WordPress, APIs, Services)
```

All threat evaluation runs *before* Nginx's regex location matching. Every request is scored and either ghosted or passed to the application with the full `X-SPX-*` threat intelligence header set attached — zero per-request overhead from the firewall logic on static assets.

---

## 🚀 Key Features

- **Ghosting Protocol:** Returns `444 No Response`, instantly closing the TCP connection. Clients receive no HTTP response — connection resets are the expected behavior for blocked requests.
- **Zero Latency:** Logic executes *before* complex regex location matching. Static assets bypass the firewall entirely; dynamic endpoints remain fully protected.
- **Real-IP Enforcement:** Decodes `CF-Connecting-IP` *only* for connections arriving from verified Cloudflare IP ranges. Direct-to-origin traffic cannot spoof the header.
- **8G Logic Core:** 8 layers of threat intelligence maps — Bad Bots, SQLi, XSS, RCE, path traversal, spam referrers, behavioral checks, and more.
- **Threat Signal Propagation:** Every dynamic request carries `X-SPX-*` headers that downstream PHP services (Helios / Sirus) can consume to make risk-aware decisions.
- **Cloudflare Worker Trust Chain:** `X-SPARXSTAR-*` identity headers (user, session, roles) are forwarded only when the Worker presents the correct shared secret — all other values are stripped.
- **Dynamic Rate Limiting:** Per-route zones for login, GraphQL, submissions, and general traffic.
- **Bot Trap (Honeypot):** `/spx-trap` is never referenced by legitimate site code. Any hit is immediately ghosted and logged.
- **Configurable Geo Amplifier:** High-risk country codes live in a separate map file. Geo alone never triggers a block — it amplifies other threat signals.
- **Automated Intelligence:** Python scripts to refresh bot signatures and Cloudflare IP ranges with atomic write and syntax-guard before apply.

---

## 📂 Repository & Deployed Structure

### Repository layout (what you clone)

```text
sparxstar-event-horizon/
├── nginx/
│   ├── conf.d/
│   │   ├── 000-spx-horizon-logic.conf  # Logic Core — maps and aggregation
│   │   └── spx-cloudflare-trust.conf   # RealIP trust list (refresh with update_cloudflare.py)
│   ├── maps/
│   │   └── high-risk-geo.map           # Editable high-risk country code list
│   └── snippets/
│       └── spx-dynamic-proxy-headers.conf # X-SPX-* and X-SPARXSTAR-* proxy headers (per proxied location)
├── docs/
│   └── operator-example-server-block.conf # Operator reference (CI also uses this file)
├── scripts/
│   ├── update_cloudflare.py            # Refreshes Cloudflare IP trust list
│   └── update_bots.py                  # Refreshes bad-bot User-Agent map
└── tests/
    └── test_firewall.py                # Attack simulation test suite
```

### Deployed layout (where files live under `/etc/nginx/`)

```text
/etc/nginx/
├── conf.d/
│   ├── 000-spx-horizon-logic.conf      # Must load FIRST — the "000-" prefix ensures this
│   └── spx-cloudflare-trust.conf       # Auto-generated; include inside http{} or conf.d
├── maps/
│   └── high-risk-geo.map
├── snippets/
│   ├── spx-dynamic-proxy-headers.conf  # include per proxied location (X-SPX-* threat headers)
├── scripts/
│   ├── update_cloudflare.py
│   └── update_bots.py
└── secrets/
    └── worker-secret.conf              # Created manually — never committed (see Step 5)
```

---

## 🛠️ Installation

### Pre-flight checklist

Before running `nginx -t`:

- [ ] All file-copy commands in Step 1 completed (including `spx-dynamic-proxy-headers.conf` and `spx-cloudflare-trust.conf`)
- [ ] `/etc/nginx/secrets/worker-secret.conf` exists (Step 5) — Nginx **will not start** without it
- [ ] `/etc/nginx/maps/high-risk-geo.map` exists (copied in Step 1) — Nginx **will not start** without it
- [ ] Your admin/egress IP is in the Emergency Bypass map (Step 4)
- [ ] `varnish_backend` and `tus_node_backend` upstreams are defined in your server block (Step 3)

---

### Step 1 — Deploy Configuration Files

> **⚠️ Copy files, do not symlink the repo into `/etc/nginx/`.** Every `conf.d/` file must exist in exactly one location. If the same file is loaded twice (once from the repo clone and once from `/etc/nginx/conf.d/`), Nginx will fail with a `duplicate directive` error.

```bash
# Clone the repository anywhere outside /etc/nginx
git clone https://github.com/Starisian-Technologies/sparxstar-event-horizon.git
cd sparxstar-event-horizon

# Logic Core (http context — must load first)
sudo cp nginx/conf.d/000-spx-horizon-logic.conf /etc/nginx/conf.d/

# Cloudflare RealIP trust list (http context)
sudo cp nginx/conf.d/spx-cloudflare-trust.conf /etc/nginx/conf.d/

# Shipped snippet file
sudo mkdir -p /etc/nginx/snippets
sudo cp nginx/snippets/spx-dynamic-proxy-headers.conf /etc/nginx/snippets/

# High-risk geo map (required at startup — Nginx exits if this file is missing)
sudo mkdir -p /etc/nginx/maps
sudo cp nginx/maps/spx-high-risk-geo.map /etc/nginx/maps/high-risk-geo.map

# Update scripts
sudo mkdir -p /etc/nginx/scripts
sudo cp scripts/*.py /etc/nginx/scripts/
sudo chmod +x /etc/nginx/scripts/*.py
```

---

### Step 2 — Refresh Threat Intelligence

The repository ships a working `spx-cloudflare-trust.conf` and bot map, but you should refresh them immediately so they reflect current data.

```bash
# Install Python 3 if missing
sudo apt update && sudo apt install python3

# 1. Refresh Cloudflare IP trust list (run this FIRST)
sudo python3 /etc/nginx/scripts/update_cloudflare.py \
    --output /etc/nginx/conf.d/spx-cloudflare-trust.conf

# 2. Refresh bad-bot User-Agent map
sudo python3 /etc/nginx/scripts/update_bots.py \
    --output /etc/nginx/conf.d/000-spx-horizon-logic.conf
```

> **⚠️ Cloudflare IP Sync — manual step required after every refresh.**
> `update_cloudflare.py` regenerates `spx-cloudflare-trust.conf` (the `set_real_ip_from` list).
> The `$spx_from_cloudflare` geo block inside `000-spx-horizon-logic.conf` is a **separate copy** of the same ranges — both must be kept in sync. If they diverge, Cloudflare Worker identity headers (`X-SPARXSTAR-*`) silently become empty strings and your PHP services see no user context.
>
> After running `update_cloudflare.py`, open `000-spx-horizon-logic.conf`, find the `geo $realip_remote_addr $spx_from_cloudflare` block (Section 5a), and mirror the same CIDR ranges.

---

### Step 3 — Configure Your Nginx

#### A. Global Logic Core

Ensure `/etc/nginx/conf.d/*.conf` is included in the `http {}` block of `/etc/nginx/nginx.conf`. Most default Nginx installs already have this line — **do not add a second include pointing to the repository clone directory**.

#### B. Upstream Definitions and Runtime Configuration

Event Horizon no longer ships runtime server-block rules. Define runtime locations in your own server block (or start from `docs/operator-example-server-block.conf`), and put this line at the top of each proxied location:

```nginx
if ($spx_final_decision) { return 444; }
```

Define your upstreams **before** your `server {}` block:

| Upstream name | Purpose | Example target |
|---|---|---|
| `varnish_backend` | Main application proxy (HTML, WP, APIs) | `127.0.0.1:6081` |
| `tus_node_backend` | TUS resumable-upload backend | `127.0.0.1:1080` |

> **Not running Varnish?** Point `varnish_backend` directly at your application server (Apache on `8080`, Node on `3000`, etc.). The name is historical — it accepts any HTTP upstream. For PHP-FPM over FastCGI, add a separate `location` block with `fastcgi_pass`.

> **Not running TUS uploads?** Define the upstream anyway — Nginx requires all referenced upstreams to exist at startup, even if the path is never hit.

```nginx
# In nginx.conf http{} or a conf.d include — BEFORE your server block
upstream varnish_backend {
    server 127.0.0.1:6081;  # Replace with your application backend
    keepalive 32;
}

upstream tus_node_backend {
    server 127.0.0.1:1080;  # Replace with your TUS upload service
    keepalive 8;
}

server {
    listen 443 ssl http2;
    server_name example.com;

    # Standard proxy headers — inherited by all locations that do not
    # define their own proxy_set_header directives.
    proxy_set_header Host              $host;
    proxy_set_header X-Real-IP         $remote_addr;
    proxy_set_header X-Forwarded-For   $remote_addr;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Port  $server_port;
    proxy_set_header X-Request-ID      $request_id;
    proxy_set_header Connection        "";
    proxy_http_version 1.1;

    # Firewall enforcement is inlined in each proxied location:
    #     if ($spx_final_decision) { return 444; }

    # ── Operator runtime locations ───────────────────────────────────
    # Each location runs the inlined firewall gate first, then adds
    # rate limits, dynamic proxy headers, and proxy_pass.

    # ACME challenge and well-known pass-through.
    location ^~ /.well-known/ {
        proxy_pass http://varnish_backend;
    }

    # WordPress login.
    location = /wp-login.php {
        if ($spx_final_decision) { return 444; }
        limit_req zone=spx_wp_login burst=3 nodelay;
        include /etc/nginx/snippets/spx-dynamic-proxy-headers.conf;
        proxy_pass http://varnish_backend;
    }

    # WordPress admin.
    location /wp-admin/ {
        if ($spx_final_decision) { return 444; }
        limit_req zone=spx_general burst=20 nodelay;
        include /etc/nginx/snippets/spx-dynamic-proxy-headers.conf;
        proxy_pass http://varnish_backend;
    }

    # GraphQL — POST and OPTIONS only (GET exposes params in logs).
    location /graphql {
        if ($spx_final_decision) { return 444; }
        if ($request_method !~ ^(POST|OPTIONS)$) { return 444; }
        limit_req zone=spx_graphql burst=10 nodelay;
        include /etc/nginx/snippets/spx-dynamic-proxy-headers.conf;
        proxy_pass http://varnish_backend;
    }

    # TUS resumable uploads. Add TUS client egress IPs to the
    # $spx_empty_ua_is_bad allowlist — TUS clients often send no UA.
    location /files/ {
        if ($spx_final_decision) { return 444; }
        proxy_set_header Tus-Resumable   $http_tus_resumable;
        proxy_set_header Upload-Offset   $http_upload_offset;
        proxy_set_header Upload-Length   $http_upload_length;
        proxy_set_header Upload-Metadata $http_upload_metadata;
        proxy_pass http://tus_node_backend;
    }

    # Main catch-all. Enforce method guard, then firewall gate, then proxy.
    location / {
        if ($spx_final_decision) { return 444; }
        if ($request_method !~ ^(GET|POST|HEAD|PUT|PATCH|DELETE|OPTIONS)$) { return 444; }
        if ($request_method = OPTIONS) { return 204; }
        limit_conn spx_conn 50;
        limit_req  zone=spx_req burst=40 nodelay;
        include /etc/nginx/snippets/spx-dynamic-proxy-headers.conf;
        proxy_pass http://varnish_backend;
    }

    # Your SSL certificate, HSTS preload, etc.
}
```

> **Security header ownership:** Event Horizon does not ship response security headers. Keep your baseline `add_header` policy in platform config, and remember Nginx header inheritance rules when adding per-location headers.

> **For the full annotated operator reference** — including the CI test harness — see [`docs/operator-example-server-block.conf`](docs/operator-example-server-block.conf).

#### C. robots.txt — Honeypot registration

Add the following to your site's `robots.txt` so the honeypot endpoint is invisible to legitimate crawlers. Any request that hits it despite this entry is immediately ghosted and logged as automated scanning.

```
User-agent: *
Disallow: /spx-trap
```

---

### Step 4 — Whitelist Your Admin IP

**Do this before reloading Nginx.** The firewall blocks all unrecognised traffic by default. If your IP is not in the bypass list, you will lock yourself out.

Open `/etc/nginx/conf.d/000-spx-horizon-logic.conf` and find the **Emergency Bypass** section (Section 4):

```nginx
map $spx_real_ip $spx_firewall_active {
    default 1;
    127.0.0.1 0;  # loopback
    ::1 0;        # loopback IPv6
    # Add your admin/operator egress IP below (0 = bypass firewall)
    # 203.0.113.45 0;
}
```

Replace `203.0.113.45` with your actual admin egress IP (your home IP, VPN exit node, etc.) and uncomment the line.

> **Use your egress IP, not the server's own public IP.** The bypass is keyed on `$spx_real_ip` — the validated client IP after Cloudflare's `CF-Connecting-IP` has been decoded. It cannot be activated by a forged header.

> **Monitoring and health-check tools with no User-Agent** also need their IPs allowlisted. Find the `$spx_empty_ua_is_bad` map in the same file (Section 6) and add their egress IPs there too, otherwise they will be ghosted:
>
> ```nginx
> map $spx_real_ip $spx_empty_ua_is_bad {
>     default   1;
>     127.0.0.1 0;
>     ::1       0;
>     10.0.0.5  0;  # your monitoring tool's IP
> }
> ```

---

### Step 5 — Create the Worker Secret File

This file is the trust anchor for the entire `X-SPARXSTAR-*` identity header chain. **Nginx will refuse to start if this file does not exist.**

#### What kind of secret?

The secret is a **shared secret** — an opaque, high-entropy random string known only to your Cloudflare Worker and this origin. It is not a key with a required format, length, or algorithm; it is compared as a literal string. Treat it like a password:

- **High entropy:** at least 32 bytes of randomness (≈ 256 bits). Longer is fine.
- **URL/header-safe characters:** it travels in the `X-Worker-Origin-Secret` HTTP header, so stick to characters valid in a header value. Hex or base64url output is safest — avoid spaces, `"`, and `;` (the last two collide with Nginx map syntax).
- **Unique per environment:** use a different secret for staging and production. Rotate it if it is ever exposed.

#### Generating one

Pick any of these (all produce a header-safe string):

```bash
openssl rand -hex 32          # 64 hex chars  — most portable
openssl rand -base64 48 | tr '+/' '-_' | tr -d '='   # base64url, no padding
head -c 32 /dev/urandom | xxd -p -c 32                # hex via /dev/urandom
uuidgen | tr -d '-'           # lower-entropy fallback if openssl is unavailable
```

#### Writing the file

```bash
sudo mkdir -p /etc/nginx/secrets

# Generate the secret and write it in Nginx map syntax in one step.
# The surrounding quotes and the trailing " 1;" are REQUIRED Nginx map
# syntax — they are not part of the secret value itself.
# No openssl? Substitute any generator from the list above, e.g.
#   SECRET="$(uuidgen | tr -d '-')"
SECRET="$(openssl rand -hex 32)"
echo "\"$SECRET\" 1;" | sudo tee /etc/nginx/secrets/worker-secret.conf

sudo chown root:root /etc/nginx/secrets/worker-secret.conf
sudo chmod 600 /etc/nginx/secrets/worker-secret.conf

# Print the bare value to paste into your Cloudflare Worker's secret store:
echo "$SECRET"
```

The secret value (the part inside the quotes) must match the `X-Worker-Origin-Secret` header that your Cloudflare Worker sends — store it in the Worker as an encrypted secret/environment variable, not in code. If no Worker is deployed yet, this file still needs to exist — create it with a placeholder value. Identity headers will evaluate to empty strings until a matching Worker is in place.

> **Never commit the secret value.** The file is listed in `.gitignore` intentionally.

---

### Step 6 — Validate and Reload

```bash
sudo nginx -t && sudo systemctl reload nginx
```

The `nginx -t` guard must pass before reload. If it fails, see the [Troubleshooting](#-troubleshooting) section below.

---

## 📡 Threat Signal Headers

Every request that passes through a dynamic location (`/`, `/wp-admin/`, `/graphql`, etc.) arrives at your application carrying these Nginx-computed headers. Because `proxy_set_header` overwrites the header on the proxied request, **client-supplied values are always discarded** — spoofing `X-SPX-Threat` from outside Nginx is not possible.

| Header | Values | Meaning |
|---|---|---|
| `X-SPX-Threat` | `0` or `1` | Binary: is this request flagged as a threat? |
| `X-SPX-Risk` | `0`–`100` | Numeric triage score (96 = SQLi + PHP exploit header, 48 = bot, etc.) |
| `X-SPX-Geo-Risk` | `0` or `1` | High-risk country flag (amplifier — never a standalone block signal) |
| `X-SPX-Bot` | `0` or `1` | Bad bot User-Agent detected |
| `X-SPX-Reason` | pipe-delimited string | Active signal tokens — see table below |

**X-SPX-Reason tokens:**

| Token | Signal source |
|---|---|
| `sqli` | SQLi / XSS / RCE in query string |
| `bad_uri` | Dangerous URI pattern (traversal, shells, sensitive files) |
| `bot` | Bad bot User-Agent |
| `bad_ref` | Spam referrer |
| `bad_post` | POST with invalid or missing Content-Type |
| `content_disp` | Content-Disposition header carrying a `.php` filename |
| `missing_host` | No Host header (scanner / smuggling probe) |
| `geo_risk` | High-risk country code (Cloudflare `CF-IPCountry`) |

**PHP consumer example (Helios / Sirus):**

```php
$is_threat = (int)($_SERVER['HTTP_X_SPX_THREAT']   ?? 0);
$risk      = (int)($_SERVER['HTTP_X_SPX_RISK']     ?? 0);
$geo       = (int)($_SERVER['HTTP_X_SPX_GEO_RISK'] ?? 0);
$bot       = (int)($_SERVER['HTTP_X_SPX_BOT']      ?? 0);
$reason    = rtrim($_SERVER['HTTP_X_SPX_REASON']   ?? '', '|');

if ($is_threat) {
    do_action('helios_high_risk_request', $risk, $reason);
}
```

> **Trust verification:** PHP consumers must also confirm the request arrived via the trusted edge before acting on these values. At a minimum, check that `CF-RAY` is present. Trusting `X-SPX-Threat: 1` from a request with no `CF-RAY` would be a bypass vector if your origin IP is ever hit directly — lock that down at the network layer (see [Origin Lockdown](#-origin-lockdown-recommended)).

---

## 🔑 Cloudflare Worker Trust Chain

The `X-SPARXSTAR-*` headers carry identity claims set by a Cloudflare Worker sitting in front of your origin. Event Horizon forwards them downstream **only** when two conditions are both true:

1. The TCP connection arrives from a verified Cloudflare IP range (`$spx_from_cloudflare = 1`)
2. The request carries `X-Worker-Origin-Secret` matching the value in `/etc/nginx/secrets/worker-secret.conf`

If either condition fails, all `X-SPARXSTAR-*` values are replaced with empty strings before the request reaches PHP. This means a client cannot spoof identity headers by crafting them directly.

| Header forwarded | PHP `$_SERVER` key | Content |
|---|---|---|
| `X-SPARXSTAR-User` | `HTTP_X_SPARXSTAR_USER` | Authenticated user identifier |
| `X-SPARXSTAR-Session` | `HTTP_X_SPARXSTAR_SESSION` | Session token |
| `X-SPARXSTAR-Roles` | `HTTP_X_SPARXSTAR_ROLES` | Role claims |
| `X-SPARXSTAR-AuthLevel` | `HTTP_X_SPARXSTAR_AUTHLEVEL` | Authentication level |
| `X-SPARXSTAR-Issued` | `HTTP_X_SPARXSTAR_ISSUED` | Token issue timestamp |
| `X-SPARXSTAR-Expires` | `HTTP_X_SPARXSTAR_EXPIRES` | Token expiry timestamp |
| `X-SPARXSTAR-Site` | `HTTP_X_SPARXSTAR_SITE` | Multisite site identifier |

---

## 🔒 Origin Lockdown (Recommended)

Event Horizon sits behind Cloudflare. An attacker who discovers your origin IP can bypass Cloudflare and hit your server directly. Lock down inbound ports 80 and 443 at the network layer to Cloudflare IP ranges only:

```bash
# Example using ufw — add all Cloudflare ranges from https://www.cloudflare.com/ips/
sudo ufw allow from 173.245.48.0/20 to any port 80,443
sudo ufw allow from 103.21.244.0/22 to any port 80,443
# ... repeat for all Cloudflare ranges ...
sudo ufw deny 80
sudo ufw deny 443
```

Alternatively, use your cloud provider's firewall rules (AWS Security Groups, DigitalOcean Cloud Firewall, GCP VPC firewall) to restrict inbound traffic to Cloudflare ranges and your own infrastructure IPs.

---

## ⚙️ Maintenance & Updates

### Rate Limiting Zones

Event Horizon runtime locations use the zones below. Define the corresponding `limit_req_zone` / `limit_conn_zone` directives in your platform-owned `http{}` config (for example, `nginx.conf` or an http-included `conf.d` file), then adjust rates and burst values to match your traffic profile:

| Zone | Applies to | Default rate | Burst |
|---|---|---|---|
| `spx_req` | All dynamic requests | 20 req/s | 40 |
| `spx_conn` | Concurrent connections per IP | 50 concurrent | — |
| `spx_wp_login` | `/wp-login.php` | 5 req/min | 3 |
| `spx_graphql` | `/graphql` | 30 req/min | 10 |
| `spx_submission` | `/submission` | 20 req/min | 10 |
| `spx_general` | `/wp-admin/` | 300 req/min | 20 |

### Automated Updates (Cron)

The two refresh scripts should run on a schedule. The jobs below run as **root** (they write into `/etc/nginx/` and reload Nginx), so they must be installed in root's crontab or under `/etc/cron.d/` — not a normal user's crontab.

> **⚠️ The two installation methods use different syntax.** `crontab -e` entries have **no user field**; `/etc/cron.d/` entries require a **user field** (`root`) between the schedule and the command. Pasting a `/etc/cron.d/`-style line into `crontab -e` (or vice versa) will silently fail or error. Pick one method below and use its exact format.

> **⚠️ Match the deployed filename.** The `--output` paths below name `000-spx-horizon-logic.conf` and `spx-cloudflare-trust.conf`. If you deployed these files under different names, edit the cron lines to match — a mismatched output path will overwrite the wrong file or create a stray one.

**Method A — root crontab (`sudo crontab -e`)** — no user field:

```cron
# Update bot signatures weekly (Monday 03:00)
0 3 * * 1 /usr/bin/python3 /etc/nginx/scripts/update_bots.py --output /etc/nginx/conf.d/000-spx-horizon-logic.conf && /usr/sbin/nginx -t && /usr/bin/systemctl reload nginx

# Update Cloudflare IP ranges monthly (1st of month 04:00)
0 4 1 * * /usr/bin/python3 /etc/nginx/scripts/update_cloudflare.py --output /etc/nginx/conf.d/spx-cloudflare-trust.conf && /usr/sbin/nginx -t && /usr/bin/systemctl reload nginx
```

Run `sudo crontab -e`, paste the two lines, save and exit. Verify with `sudo crontab -l`.

**Method B — drop-in file (`/etc/cron.d/spx-horizon`)** — note the added `root` user field:

```cron
# /etc/cron.d/spx-horizon  — owned by root, mode 0644, MUST end with a newline
# ┌ min ┌ hr ┌ dom ┌ mon ┌ dow ┌ USER ── command ───────────────────────────
# Update bot signatures weekly (Monday 03:00)
0 3 * * 1 root /usr/bin/python3 /etc/nginx/scripts/update_bots.py --output /etc/nginx/conf.d/000-spx-horizon-logic.conf && /usr/sbin/nginx -t && /usr/bin/systemctl reload nginx

# Update Cloudflare IP ranges monthly (1st of month 04:00)
0 4 1 * * root /usr/bin/python3 /etc/nginx/scripts/update_cloudflare.py --output /etc/nginx/conf.d/spx-cloudflare-trust.conf && /usr/sbin/nginx -t && /usr/bin/systemctl reload nginx
```

Install it with correct ownership and permissions:

```bash
sudo tee /etc/cron.d/spx-horizon > /dev/null <<'EOF'
0 3 * * 1 root /usr/bin/python3 /etc/nginx/scripts/update_bots.py --output /etc/nginx/conf.d/000-spx-horizon-logic.conf && /usr/sbin/nginx -t && /usr/bin/systemctl reload nginx
0 4 1 * * root /usr/bin/python3 /etc/nginx/scripts/update_cloudflare.py --output /etc/nginx/conf.d/spx-cloudflare-trust.conf && /usr/sbin/nginx -t && /usr/bin/systemctl reload nginx
EOF
sudo chown root:root /etc/cron.d/spx-horizon
sudo chmod 0644 /etc/cron.d/spx-horizon
```

> Files in `/etc/cron.d/` must be owned by root, **not** be group/world-writable, and end with a trailing newline — cron silently ignores a file that violates any of these.

The `nginx -t &&` guard prevents a broken update from being applied. If the generated config has a syntax error, the old configuration stays active.

> **After running `update_cloudflare.py`**, you must also manually update the `geo $realip_remote_addr $spx_from_cloudflare` block in `000-spx-horizon-logic.conf` (Section 5a) to match. See the Cloudflare sync note in [Step 2](#step-2--refresh-threat-intelligence).

### Customising the High-Risk Geo List

Edit `/etc/nginx/maps/high-risk-geo.map`. Each entry is an ISO 3166-1 alpha-2 country code followed by ` 1;`:

```
RU      1;  # Russia
CN      1;  # China
```

> Geo alone **never** blocks a request. It acts as a risk amplifier — a request is blocked only when both the geo signal and another threat signal (SQLi, bad bot, etc.) fire at the same time.

After editing: `sudo nginx -t && sudo systemctl reload nginx`

### Customising Rules

- **Allow a specific IP through the firewall:** Add it to the `$spx_firewall_active` map (Section 4) with value `0`.
- **Allow a monitoring tool with no User-Agent:** Add its IP to the `$spx_empty_ua_is_bad` map (Section 6) with value `0`.
- **Add or remove blocked bots:** Edit the `$spx_bad_bot` map (Section 6), or run `update_bots.py` to replace the full list.
- **Change rate limits:** Edit the platform-owned `limit_req_zone` / `limit_conn_zone` directives in your `http{}` runtime config, and the `limit_req` burst values in your operator server block locations.

---

## 🌐 Built-in Endpoints

| Endpoint | Behaviour | Notes |
|---|---|---|
| `/health` | Returns `200 OK` | Only accessible from IPs in the `$spx_firewall_active` bypass list. Load balancers must connect from a bypass-listed IP or this returns `444`. |
| `/spx-trap` | Immediately ghosted (`444`) | Honeypot. Add `Disallow: /spx-trap` to `robots.txt`. Any hit = automated scanner. |
| `/files/` | Operator-defined | TUS resumable upload endpoint. Define in your server block with `if ($spx_final_decision) { return 444; }` and `proxy_pass http://tus_node_backend;`. TUS client IPs must be in the `$spx_empty_ua_is_bad` allowlist (no UA by spec). |
| `/.well-known/` | Operator-defined | ACME challenge pass-through. Define in your server block with `location ^~ /.well-known/ { proxy_pass ...; }` — the `^~` prefix wins over extension-based lockdown regex. |

---

## 📊 Log Monitoring

All ghosted connections are written to `/var/log/nginx/spx-blocked.log`. Normal (non-blocked) traffic is not logged by Event Horizon.

```bash
# Count ghosted connections since last log rotation
sudo awk '$9 == 444' /var/log/nginx/spx-blocked.log | wc -l

# Top blocked IPs in the last 1000 log entries
sudo tail -1000 /var/log/nginx/spx-blocked.log | awk '{print $1}' | sort | uniq -c | sort -rn | head -20

# Show only honeypot hits
sudo grep '/spx-trap' /var/log/nginx/spx-blocked.log
```

| Alert signal | What it means |
|---|---|
| Sudden spike in `444` count | Active attack or scan sweep in progress |
| High rate of `444` from a single IP | Brute-force or crawler — add to blocklist |
| Any hit on `/spx-trap` | Automated scanner confirmed |
| Unexpected new country codes | Possible geo-targeted campaign |

---

## 🛡️ Testing & Verification

Event Horizon ships an attack simulation test suite. Tests connect to a live local Nginx instance — a `ConnectionError` is a **PASS** (the firewall ghosted the connection). A `200` or `404` on a blocked path is a **FAIL**.

> **⚠️ The test suite only validates a bare, local install.** It assumes Nginx is reachable directly at `http://localhost` with no edge in front of it. **It cannot validate a production deployment that sits behind Cloudflare (and/or Varnish).** On a Cloudflare-fronted origin the suite produces false failures that look like firewall faults but are not — see [Validating a Cloudflare-fronted deployment](#validating-a-cloudflare-fronted-deployment) below for why, and for the log-based method you should use instead.

### Installing the test runner

The suite needs Python 3, `pytest`, and `requests`. **Lead with your distribution's packages** — a stock Ubuntu/Debian server has no `pip` and the package path avoids the `--break-system-packages` friction entirely:

```bash
# Debian / Ubuntu (recommended — no pip required)
sudo apt update && sudo apt install -y python3-pytest python3-requests
```

```bash
# RHEL / Rocky / AlmaLinux
sudo dnf install -y python3-pytest python3-requests
```

When installed from distro packages the runner is **`pytest-3`** (Debian/Ubuntu) or **`python3 -m pytest`**, *not* a bare `pytest` — the unversioned `pytest` command often does not exist:

```bash
pytest-3 tests/test_firewall.py -v
# or, portable across distros:
python3 -m pytest tests/test_firewall.py -v
```

**pip fallback (only if your distro has no `python3-pytest` package):**

```bash
# pip itself is frequently not installed — add it first
sudo apt install -y python3-pip          # Debian/Ubuntu
# or: sudo dnf install -y python3-pip    # RHEL/Rocky/AlmaLinux
# then install the libraries. On PEP 668 "externally managed" systems
# (Ubuntu 23.04+, Debian 12+) pip refuses to touch system packages, so
# use a virtualenv (preferred) ...
python3 -m venv ~/.spx-venv && ~/.spx-venv/bin/pip install pytest requests
~/.spx-venv/bin/pytest tests/test_firewall.py -v

# ... or override the guard if you accept writing to system site-packages:
pip3 install --break-system-packages pytest requests
```

### Validating a Cloudflare-fronted deployment

The shipped tests request `http://localhost` from the box itself. On a real deployment behind Cloudflare this is **not** how legitimate traffic arrives, so the tests misreport two non-faults as firewall failures:

- **TLS verification failure (`CERTIFICATE_VERIFY_FAILED`)** — if you point the tests at `https://<origin>`, the origin certificate is issued for your public domain, not `localhost`, so `requests` rejects it (the suite intentionally does not pass `verify=False`).
- **Blocks "DID NOT RAISE"** — the shipped logic core lists `127.0.0.1`/`::1` in the Emergency Bypass, so loopback traffic evaluates to `$spx_firewall_active = 0` and therefore `$spx_final_decision = 0` — a request originating from the box itself is **never** ghosted, no matter what attack payload it carries. (CI strips those bypass entries — the `# spx-admin-bypass` lines — precisely so the attack tests can see a block; a production origin keeps the bypass in place.) Compounding this, because the request does not arrive from a Cloudflare IP, `$spx_from_cloudflare = 0`, so `CF-Connecting-IP` is never decoded (`$spx_real_ip` stays `127.0.0.1`) and the `X-SPARXSTAR-*` worker-identity path can't be exercised either. Block-tests that expect a ghosted connection instead get a normal response.

These are artifacts of bypassing the edge, not firewall faults. **On a production origin, do not rely on the test suite — validate from the logs instead.** Every ghosted connection is written to `/var/log/nginx/spx-blocked.log` (see [Log Monitoring](#-log-monitoring)). Send known-bad requests *through Cloudflare* (i.e. to your public hostname) and confirm each one is ghosted and logged:

```bash
# From an external host, hit your PUBLIC hostname so the request traverses
# Cloudflare and arrives with a real CF-Connecting-IP. A ghosted request
# returns no HTTP response (connection reset) — curl exits non-zero.
curl -sS --max-time 5 "https://example.com/spx-trap"                       # honeypot → ghosted
curl -sS --max-time 5 "https://example.com/?id=1'+UNION+SELECT+user"       # SQLi → ghosted
curl -sS --max-time 5 "https://example.com/wp-config.php"                   # sensitive file → ghosted

# Then confirm each attempt was ghosted and logged on the origin:
sudo tail -f /var/log/nginx/spx-blocked.log
```

A `444`/connection-reset on the client plus a matching line in `spx-blocked.log` is the production equivalent of a test PASS.

> **⚠️ Cloudflare's own WAF may block the test patterns before they reach your origin.** Generic attack signatures like `UNION SELECT` or `wp-config.php` can be intercepted at Cloudflare's edge, in which case `curl` receives a standard Cloudflare response (e.g. HTTP `403`) rather than an origin `444`/connection reset — and nothing appears in `spx-blocked.log` because the request never reached Event Horizon. **Use `/spx-trap` as the most reliable origin-ghosting check:** it is unique to Event Horizon, is never referenced by legitimate traffic, and is not matched by Cloudflare's default managed rules, so a request to it always reaches the origin to be ghosted and logged.

---

## 🔧 Troubleshooting

### `nginx -t` fails: `"map_hash_bucket_size" directive is duplicate`

**Cause:** The config file is being loaded twice — once from its deployed location (`/etc/nginx/conf.d/`) and once from a second `include` path (e.g. pointing at the repository clone directory).

**Fix:** Check `nginx.conf` and all `conf.d/` includes for a second reference to `000-spx-horizon-logic.conf`. Remove it. Each file must be included exactly once.

---

### `nginx -t` fails: `open() "/etc/nginx/maps/high-risk-geo.map" failed (2: No such file or directory)`

**Cause:** The geo map file was not copied to the deployment path.

**Fix:**
```bash
sudo mkdir -p /etc/nginx/maps
sudo cp /path/to/sparxstar-event-horizon/maps/high-risk-geo.map /etc/nginx/maps/
```

---

### `nginx -t` fails: `open() "/etc/nginx/secrets/worker-secret.conf" failed (2: No such file or directory)`

**Cause:** The worker secret file does not exist. Nginx requires the file to be present at startup even if you are not using the Worker trust chain yet.

**Fix:** Create the file (see [Step 5](#step-5--create-the-worker-secret-file)). If you have no Worker secret yet, use a placeholder — identity headers will simply evaluate to empty strings:
```bash
sudo mkdir -p /etc/nginx/secrets
echo '"placeholder-replace-me" 1;' | sudo tee /etc/nginx/secrets/worker-secret.conf
sudo chmod 600 /etc/nginx/secrets/worker-secret.conf
```

---

### Nginx starts but `X-SPARXSTAR-*` headers are always empty

**Cause:** Either (a) the Cloudflare Worker is not sending `X-Worker-Origin-Secret`, (b) the secret value does not match `worker-secret.conf`, or (c) the `$spx_from_cloudflare` geo block and `spx-cloudflare-trust.conf` are out of sync.

**Fix:**
1. Confirm your Worker sends `X-Worker-Origin-Secret` with the correct value.
2. Verify `worker-secret.conf` contains exactly `"your-secret" 1;` with the value in quotes.
3. Check that the CIDR ranges in the `geo $realip_remote_addr $spx_from_cloudflare` block (Section 5a of `000-spx-horizon-logic.conf`) match those in `spx-cloudflare-trust.conf`. Run `update_cloudflare.py` and then update the geo block manually.

---

### Legitimate traffic is being ghosted

**Cause:** Most common causes — your admin IP is not in the bypass list, a monitoring tool sends no User-Agent, or a bot signature regex is over-broad.

**Fix:**
1. Add your IP to the `$spx_firewall_active` map (Section 4).
2. If a monitoring or health-check tool sends requests with no User-Agent, add its IP to the `$spx_empty_ua_is_bad` map (Section 6).
3. Check `/var/log/nginx/spx-blocked.log` for the blocked IP and the request path to identify which map triggered the block.

---

### The `/health` endpoint returns `444`

**Cause:** `$spx_firewall_active` is `1` for the requesting IP. The health check location only returns `200` for IPs in the bypass list.

**Fix:** Add the load balancer or health-check service IP to the `$spx_firewall_active` map bypass list (Section 4 of `000-spx-horizon-logic.conf`).

---

## 📝 License

© 2026 Starisian Technologies. All Rights Reserved. See [LICENSE](LICENSE.md) for full terms.
