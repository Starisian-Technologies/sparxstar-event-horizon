# Changelog — SPARXSTAR Event Horizon

All notable changes to this project are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versions follow [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

### Documentation

- **Testing:** Documented that the attack-simulation suite validates only a
  bare, local install and cannot validate a Cloudflare-fronted origin (TLS
  cert mismatch and missing `CF-Connecting-IP` produce false failures). Added
  a log-based validation procedure (`/var/log/nginx/spx-blocked.log`) for
  production deployments.
- **Testing:** Reworked the test-runner install instructions to lead with the
  distro-package path (`apt install python3-pytest python3-requests`) and the
  correct runner invocation (`pytest-3` / `python3 -m pytest`), with `pip`
  (including virtualenv and `--break-system-packages`) given only as a fallback.
- **Cron:** Added explicit installation instructions for the automated-update
  jobs covering both `crontab -e` and `/etc/cron.d/`, the user-field syntax
  difference between them, and a note that the `--output` filename must match
  the deployed config filename.
- **Worker secret:** Documented what the worker secret is (a high-entropy
  shared secret), how to generate one (`openssl rand`), and the header-safe
  character constraints.

---

## [2.1.0] — 2026-04-01

### Changed

- **Architecture:** Restored full 8G Firewall v1.5 pattern coverage. All
  17 `[QUERY STRING]`, 23 `[REQUEST URI]`, 12 `[USER AGENT]`, and associated
  rule groups are now represented as http-context `map` directives.
- **Threat aggregation:** `$spx_bad_method` (CONNECT, DEBUG, MOVE, TRACE,
  TRACK) and `$spx_bad_cookie` (encoded injection chars) integrated into
  `$spx_base_threat`.
- **Risk scoring:** `$spx_risk_score` map updated with new severity tiers.
- **Worker trust chain:** `$spx_pass_sparxstar_*` maps introduced for
  conditional `X-SPARXSTAR-*` header forwarding.
- **Geo amplifier:** `$spx_high_risk_geo` now reads from an external map
  file (`/etc/nginx/maps/high-risk-geo.map`) so operators can customise
  the country list without editing the logic core.
- **Snippet:** `spx-dynamic-proxy-headers.conf` now includes `X-SPX-Bot`,
  `X-SPX-Reason`, and the `X-SPARXSTAR-*` set.
- **Repository structure:** Shipped assets moved to `nginx/` subdirectory
  (`nginx/conf.d/`, `nginx/maps/`, `nginx/snippets/`).

### Removed

- `spx-horizon-rules.conf` — enforcement location blocks are now the
  operator's responsibility (see `docs/operator-example-server-block.conf`).
- `spx-firewall-gate.conf` — gate is inlined per location as
  `if ($spx_final_decision) { return 444; }`.
- `spx-security-headers.conf` — security response headers are owned by the
  platform baseline, not Event Horizon.
- `spx-static-assets-runtime.conf` — static asset bypass is defined in the
  operator server block.

---

## [2.0.0] — 2026-01-01

### Added

- Initial public release.
- `000-spx-horizon-logic.conf` — http-context map library translating 8G
  Firewall if-block rules to zero-latency map directives.
- `spx-cloudflare-trust.conf` — RealIP trust list for Cloudflare edge IPs.
- `update_cloudflare.py` — automated Cloudflare IP range refresh script.
- `update_bots.py` — automated bad-bot signature refresh script.
- `tests/test_firewall.py` — attack simulation test suite.
- CI workflow: Nginx syntax validation + live attack simulation on every push.
- Emergency Bypass (`$spx_firewall_active`) — IP-based only, no header bypass.
- Ghosting Protocol — all blocks use `return 444` (no 403 response).
- `X-SPX-*` threat signal propagation to upstream PHP (Helios / Sirus).

---

*Entries marked [SPX] in config comments are SPARXSTAR additions to the
base 8G Firewall logic.*
