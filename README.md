
<img width="1280" height="640" alt="sparxstar-event-horizon" src="https://github.com/user-attachments/assets/16f804e4-2bc9-4b0a-a3fc-eeb675529e1d" />

# SPARXSTAR Event Horizon v2.0

> **"Nothing malicious escapes."**

**Event Horizon** is a high-performance, carrier-grade Nginx firewall designed for zero-latency threat mitigation. It drops malicious connections immediately (Ghosting Protocol) before they consume application resources, protecting your upstream against DDoS, bots, SQLi, XSS, and brute-force attacks.

## 🏗️ Architecture

Event Horizon sits between Cloudflare's edge and your application layer. Understanding this placement is critical — placing the firewall *behind* the application server defeats the Ghosting Protocol.

```text
Internet
   ↓
Cloudflare Edge  (absorbs volumetric DDoS, terminates TLS)
   ↓
SPARXSTAR Event Horizon  (Nginx firewall — threat evaluation & ghosting)
   ↓
Application Layer
   • WordPress
   • APIs
   • Services
```

All threat evaluation runs *before* Nginx's regex location matching, so every request is scored and either ghosted or passed to the app with zero per-request overhead from the firewall logic.

## 🚀 Key Features

- **Ghosting Protocol:** Returns `444 No Response` to attackers, instantly closing the TCP connection and saving CPU/bandwidth. Clients receive no HTTP response — connection resets are expected behavior for blocked requests.
- **Zero Latency:** Logic executes *before* complex regex location matching. Static assets bypass the firewall entirely (intentional performance optimization — dynamic endpoints remain fully protected).
- **Real-IP Enforcement:** Securely decodes `CF-Connecting-IP` *only* for connections arriving from trusted Cloudflare IP ranges, preventing header spoofing. No other proxies are trusted unless explicitly added.
- **The 8G Logic Core:** 8 layers of threat intelligence maps (Bad Bots, SQLi, XSS, RCE, Spam, etc.).
- **Dynamic Rate Limiting:** Specialized zones for connection and request flooding.
- **Bot Trap (Honeypot):** The `/spx-trap` endpoint is never referenced by legitimate site code. Any request to this path is assumed to be automated scanning or bot activity, immediately ghosted.
- **Configurable Geo Amplifier:** High-risk country codes live in a separate map file operators can edit without touching the core config.
- **Automated Intelligence:** Python scripts to auto-update bot signatures and Cloudflare IP ranges.

## 📂 Project Structure

```text
/etc/nginx/
├── conf.d/
│   ├── 000-spx-horizon-logic.conf  # The Brain (Maps, Zones, Logic — loaded ONCE, must be first)
│   └── spx-cloudflare-trust.conf   # Auto-generated RealIP trust list
├── maps/
│   └── high-risk-geo.map           # Configurable high-risk country code list
├── snippets/
│   └── spx-horizon-rules.conf      # The Brawn (Server Block Rules)
└── scripts/
    ├── update_bots.py              # Updates User-Agent signatures
    └── update_cloudflare.py        # Updates Cloudflare IP ranges
```

## 🛠️ Installation

### 1. Deploy Configuration Files
Copy the configuration files to your Nginx directory (usually `/etc/nginx/`).

> **⚠️ Important:** Only the *contents* of each folder are copied into Nginx — **do not** clone or symlink the repository into `/etc/nginx/` itself, and **never** add an `include` directive in `nginx.conf` that points to the cloned repository directory. Every `conf.d/` file must exist in exactly **one** location (`/etc/nginx/conf.d/`). Loading a file from both the repo clone and `/etc/nginx/conf.d/` will cause nginx to fail with a *"duplicate directive"* error.

```bash
# Clone the repository (anywhere outside /etc/nginx)
git clone https://github.com/Starisian-Technologies/sparxstar-event-horizon.git
cd sparxstar-event-horizon

# Copy configuration (adjust paths if your distro differs)
sudo cp conf.d/000-spx-horizon-logic.conf /etc/nginx/conf.d/
sudo cp snippets/spx-horizon-rules.conf /etc/nginx/snippets/
sudo mkdir -p /etc/nginx/maps
sudo cp maps/high-risk-geo.map /etc/nginx/maps/
sudo mkdir -p /etc/nginx/scripts
sudo cp scripts/*.py /etc/nginx/scripts/
sudo chmod +x /etc/nginx/scripts/*.py
```

### 2. Initial Setup Scripts
Run the update scripts to generate the initial bot signatures and IP trust lists.

```bash
# Install Python 3 if missing
sudo apt update && sudo apt install python3

# Generate Cloudflare Trust List
sudo python3 /etc/nginx/scripts/update_cloudflare.py --output /etc/nginx/conf.d/spx-cloudflare-trust.conf

# Generate Bad Bot Map
sudo python3 /etc/nginx/scripts/update_bots.py --output /etc/nginx/conf.d/000-spx-horizon-logic.conf
```

### 3. Configure Your Nginx
Edit your `nginx.conf` or specific site configuration file.

#### A. Global Logic (nginx.conf)
Ensure `/etc/nginx/conf.d/*.conf` is included in the `http {}` block of `/etc/nginx/nginx.conf`. This loads the Logic Core and RealIP settings.
*Most default Nginx installs already have this line — **do not add a second include pointing to the repository clone**.*

#### B. Server Protection (sites-enabled/yoursite)
Include the rules snippet inside your `server {}` block.

```nginx
server {
    listen 443 ssl http2;
    server_name example.com;
    
    # [!] INCLUDE EVENT HORIZON RULES HERE
    include /etc/nginx/snippets/spx-horizon-rules.conf;

    # ... SSL settings ...
    # ... Other location blocks ...
}
```

### 4. Important: Whitelist Your IP
**⚠️ Before reloading, whitelist your IP to avoid locking yourself out.**

Open `/etc/nginx/conf.d/000-spx-horizon-logic.conf` and find the **Emergency Bypass** section:

```nginx
# 4. EMERGENCY BYPASS
map $spx_real_ip $spx_firewall_active {
    default 1;
    127.0.0.1 0;
    ::1 0;
    # Add your IP here (0 = Bypass Firewall)
    203.0.113.45 0; 
}
```

> **⚠️ Use your admin/operator *egress* IP** (e.g. your home or VPN exit node), not the server's own public IP. Adding the server's own IP here would bypass the firewall for traffic that appears to originate locally, which is rarely the intended behavior.

### 5. Configure Worker Secret
Create the worker secret file and restrict its permissions:

```bash
sudo mkdir -p /etc/nginx/secrets
echo '"your-shared-secret-value" 1;' | sudo tee /etc/nginx/secrets/worker-secret.conf
sudo chown root:root /etc/nginx/secrets/worker-secret.conf
sudo chmod 600 /etc/nginx/secrets/worker-secret.conf
```

> **⚠️ Never commit the secret value.** The file is excluded from this repository intentionally.

### 6. Validate and Reload

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## 🔒 Origin Lockdown (Recommended)

Because Event Horizon sits behind Cloudflare, attackers who discover your origin IP can bypass both Cloudflare and the firewall entirely by connecting directly. The most robust lockdown is at the network/OS layer:

```bash
# Allow only Cloudflare IP ranges (https://www.cloudflare.com/ips/) and your own
# infrastructure IPs on ports 80/443. Block all other inbound connections.
# Example using ufw:
sudo ufw allow from 173.245.48.0/20 to any port 80,443
sudo ufw allow from 103.21.244.0/22 to any port 80,443
# ... (add all Cloudflare ranges, then deny the rest)
sudo ufw deny 80
sudo ufw deny 443
```

Alternatively, use your cloud provider's firewall rules (AWS Security Groups, DigitalOcean Cloud Firewall, etc.) to restrict inbound traffic to only Cloudflare IP ranges and your own infrastructure.

## ⚙️ Maintenance & Updates

### Automated Updates (Cron)
Keep your threat intelligence fresh by adding these to crontab (`crontab -e`):

```cron
# Update Bot List (Weekly)
0 3 * * 1 /usr/bin/python3 /etc/nginx/scripts/update_bots.py --output /etc/nginx/conf.d/000-spx-horizon-logic.conf && /usr/sbin/nginx -t && /usr/bin/systemctl reload nginx

# Update Cloudflare IPs (Monthly)
0 4 1 * * /usr/bin/python3 /etc/nginx/scripts/update_cloudflare.py --output /etc/nginx/conf.d/spx-cloudflare-trust.conf && /usr/sbin/nginx -t && /usr/bin/systemctl reload nginx
```

> **The `nginx -t &&` guard is intentional.** If the updated config has a syntax error, the `&&` prevents `systemctl reload nginx` from running and avoids deploying a broken configuration.

> **⚠️ Cloudflare IP Sync:** `update_cloudflare.py` regenerates `spx-cloudflare-trust.conf` (the RealIP trust list). The `$spx_from_cloudflare` geo block in `000-spx-horizon-logic.conf` contains a **duplicate** of those ranges and must be updated manually to match. See the `SYNC WARNING` comment in that file.

### Customizing the High-Risk Geo List
Edit `/etc/nginx/maps/high-risk-geo.map` to add or remove country codes (ISO 3166-1 alpha-2):

```
# Example: add Russia and China
RU      1;
CN      1;
```

Then reload: `sudo nginx -t && sudo systemctl reload nginx`

### Customizing Rules
- **Add/Remove Blocked IPs:** Edit specific maps in `conf.d/000-spx-horizon-logic.conf`.
- **Change Rate Limits:** Adjust `limit_req_zone` in Logic Core configuration file.
- **Allow Specific Bots:** Add specific IP/UA exclusions in the Logic file maps.

## 📊 Recommended Log Monitoring

Track these metrics to detect and respond to attacks early:

| Metric | Log source | Alert threshold |
|---|---|---|
| `444` response rate spike | `/var/log/nginx/spx-blocked.log` | Sudden increase vs baseline |
| Rate-limit triggers (`429`) | access log | High frequency from single IP |
| Honeypot hits (`/spx-trap`) | `/var/log/nginx/spx-blocked.log` | Any hit = automated scanner |
| Unusual geo traffic | access log + CF-IPCountry | New country codes at scale |

```bash
# Quick check: count recent ghosted connections
# (assumes default Nginx combined log format; field 9 = status code)
sudo awk '$9 == 444' /var/log/nginx/spx-blocked.log | wc -l

# Top blocked IPs in the last 1000 log lines
sudo tail -1000 /var/log/nginx/spx-blocked.log | awk '{print $1}' | sort | uniq -c | sort -rn | head -20
```

## 🛡️ Testing & Verification
Event Horizon includes a full test suite.

```bash
# Install test dependencies
pip3 install pytest requests

# Run the attack simulation
pytest tests/test_firewall.py
```

## 📝 License
Proprietary / Closed Source.
© 2026 Starisian Technologies. All Rights Reserved.
