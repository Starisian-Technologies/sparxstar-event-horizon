
<img width="1280" height="640" alt="sparxstar-event-horizon" src="https://github.com/user-attachments/assets/16f804e4-2bc9-4b0a-a3fc-eeb675529e1d" />

# SPARXSTAR Event Horizon v2.0

> **"Nothing malicious escapes."**

**Event Horizon** is a high-performance, carrier-grade Nginx firewall designed for zero-latency threat mitigation. It drops malicious connections immediately (Ghosting Protocol) before they consume application resources, protecting your upstream against DDoS, bots, SQLi, XSS, and brute-force attacks.

## 🚀 Key Features

- **Ghosting Protocol:** Returns `444 No Response` to attackers, instantly closing the connection and saving CPU/bandwidth.
- **Zero Latency:** Logic executes *before* complex regex location matching. Static assets bypass the firewall entirely.
- **Real-IP Enforcement:** securely decodes `CF-Connecting-IP` (Cloudflare) or other headers, preventing spoofing.
- **The 8G Logic Core:** 8 layers of threat intelligence maps (Bad Bots, SQLi, XSS, RCE, Spam, etc.).
- **Dynamic Rate Limiting:** specialized zones for connection and request flooding.
- **Bot Trap (Honeypot):** invisible `/spx-trap` endpoint that instantly bans curious bots.
- **Automated Intelligence:** Python scripts to auto-update bot signatures and Cloudflare IP ranges.

## 📂 Project Structure

```text
/etc/nginx/
├── conf.d/
│   ├── spx-horizon-logic.conf      # The Brain (Maps, Zones, Logic — loaded ONCE)
│   └── spx-cloudflare-trust.conf   # Auto-generated RealIP trust list
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
sudo cp conf.d/spx-horizon-logic.conf /etc/nginx/conf.d/
sudo cp snippets/spx-horizon-rules.conf /etc/nginx/snippets/
sudo mkdir -p /etc/nginx/scripts
sudo cp scripts/*.py /etc/nginx/scripts/
```

### 2. Initial Setup Scripts
Run the update scripts to generate the initial bot signatures and IP trust lists.

```bash
# Install Python 3 if missing
sudo apt update && sudo apt install python3

# Generate Cloudflare Trust List
sudo python3 /etc/nginx/scripts/update_cloudflare.py --output /etc/nginx/conf.d/spx-cloudflare-trust.conf

# Generate Bad Bot Map
sudo python3 /etc/nginx/scripts/update_bots.py --output /etc/nginx/conf.d/spx-horizon-logic.conf
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

Open `/etc/nginx/conf.d/spx-horizon-logic.conf` and find the **Emergency Bypass** section:

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

### 5. Validate and Reload

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## ⚙️ Maintenance & Updates

### Automated Updates (Cron)
Keep your threat intelligence fresh by adding these to crontab (`crontab -e`):

```cron
# Update Bot List (Weekly)
0 3 * * 1 /usr/bin/python3 /etc/nginx/scripts/update_bots.py --output /etc/nginx/conf.d/spx-horizon-logic.conf && /usr/sbin/nginx -t && /usr/bin/systemctl reload nginx

# Update Cloudflare IPs (Monthly)
0 4 1 * * /usr/bin/python3 /etc/nginx/scripts/update_cloudflare.py --output /etc/nginx/conf.d/spx-cloudflare-trust.conf && /usr/sbin/nginx -t && /usr/bin/systemctl reload nginx
```

### Customizing Rules
- **Add/Remove Blocked IPs:** Edit specific maps in `conf.d/spx-horizon-logic.conf`.
- **Change Rate Limits:** Adjust `limit_req_zone` in Logic Core configuration file.
- **Allow Specific Bots:** Add specific IP/UA exclusions in the Logic file maps.

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
