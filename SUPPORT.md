# Support — SPARXSTAR Event Horizon

## Getting Help

### Documentation

Start with the project documentation before opening a support request:

- [README.md](README.md) — installation, configuration, and operation.
- [TECHNICAL-SPECIFICATION.md](TECHNICAL-SPECIFICATION.md) — architecture and design decisions.
- [docs/operator-example-server-block.conf](docs/operator-example-server-block.conf) — annotated production server block reference.

### Troubleshooting

The README contains a **Troubleshooting** section covering the most common
deployment issues:

- `map_hash_bucket_size directive is duplicate`
- Missing `high-risk-geo.map` at startup
- Missing `worker-secret.conf` at startup
- `X-SPARXSTAR-*` headers always empty
- Legitimate traffic being ghosted
- `/health` endpoint returning `444`

Read this section before opening an issue.

---

## Reporting Bugs

Use the **Bug Report** issue template on GitHub.

Provide:
- Nginx version and OS distribution.
- Exact error message or unexpected behaviour.
- Steps to reproduce.
- Relevant log output (redact IPs and secrets before posting).

---

## Security Vulnerabilities

**Do not post security vulnerabilities in public issues.**

See [SECURITY.md](SECURITY.md) for the responsible disclosure process.

---

## Commercial Support

For enterprise deployments, SLA-backed support, or custom integration
assistance, contact:

**Starisian Technologies**
Email: support@starisian.com
GitHub: [@Starisian-Technologies](https://github.com/Starisian-Technologies)

---

## Scope of Community Support

This repository does not provide support for:

- General Nginx configuration questions unrelated to Event Horizon.
- Third-party application layer issues (WordPress, Varnish, Node.js).
- Cloudflare Worker development.
- Operating system or firewall (ufw, iptables) configuration.
