# Security Policy — SPARXSTAR Event Horizon

## Supported Versions

| Version | Supported |
|---------|-----------|
| 2.1.x   | ✅ Yes     |
| < 2.1   | ❌ No      |

Only the current major release receives security fixes.

---

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Publicly disclosing a vulnerability before a fix is available puts all
deployments at risk.

### Preferred Channel

Email: **security@starisian.com**

Include in your report:

- A description of the vulnerability and its potential impact.
- The affected component (logic maps, scripts, CI, documentation).
- Steps to reproduce or a proof-of-concept (can be withheld until a fix
  is confirmed).
- Your preferred disclosure timeline, if any.

### What to Expect

| Stage | Timeline |
|---|---|
| Acknowledgement | Within 2 business days |
| Triage and severity assessment | Within 5 business days |
| Fix development | Determined by severity (Critical: 7 days, High: 14 days) |
| Coordinated disclosure | Agreed with reporter |

We do not currently operate a paid bug bounty programme, but we acknowledge
valid reporters in release notes with their consent.

---

## Scope

### In Scope

- Nginx map rules that can be bypassed to allow malicious traffic through.
- Logic errors in threat aggregation (`$spx_final_decision`, `$spx_base_threat`).
- Script vulnerabilities in `update_bots.py` or `update_cloudflare.py` (e.g.
  unsafe write paths, HTTPS bypass, regex injection).
- CI/CD pipeline issues that could allow secret exposure or unsafe deployments.
- Documentation errors that would cause operators to misconfigure security controls.

### Out of Scope

- Rate limiting bypass (rate limits are defined by the operator, not Event Horizon).
- Cloudflare-layer vulnerabilities (report directly to Cloudflare).
- Vulnerabilities in upstream application code (WordPress, Helios, Sirus).
- Denial-of-service via Nginx regex CPU exhaustion on static assets (static assets
  bypass the firewall by design).

---

## Security Design Notes

- The Ghosting Protocol (`return 444`) drops TCP connections with no HTTP response.
  This is intentional and not a vulnerability.
- `$spx_firewall_active` bypass is **IP-based only**. Header-based bypass was
  intentionally removed. Any claim that a header can bypass the firewall should
  be reported as a vulnerability.
- `X-SPARXSTAR-*` headers are forwarded **only** when the Cloudflare Worker
  presents the correct shared secret. Client-supplied values are always stripped.
- The worker secret lives in `/etc/nginx/secrets/worker-secret.conf`, which is
  listed in `.gitignore` and must never be committed.
