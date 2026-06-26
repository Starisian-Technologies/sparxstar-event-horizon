# Contributing to SPARXSTAR Event Horizon

> **NOTICE — Proprietary Repository**
> This project is proprietary software owned by Starisian Technologies.
> All contributions are subject to the terms in [LICENSE.md](LICENSE.md).
> By submitting a contribution you assign all intellectual property rights
> to Starisian Technologies unless a separate written agreement states otherwise.

---

## Who Can Contribute

Contributions are accepted from:

- Authorised Starisian Technologies personnel.
- Approved collaborators operating under a signed NDA or MOU.
- Community users submitting bug reports or security disclosures via the
  appropriate issue templates.

If you are unsure of your status, contact the maintainers before opening
a pull request.

---

## Reporting Bugs

Use the **Bug Report** issue template. Provide:

- Nginx version and OS distribution.
- The exact error or unexpected behaviour.
- Steps to reproduce.
- Expected behaviour vs actual behaviour.
- Relevant log output from `/var/log/nginx/spx-blocked.log` or `nginx -t`.

Do not include secrets, credentials, or your admin bypass IP in reports.

---

## Reporting Security Vulnerabilities

**Do not open a public issue for security vulnerabilities.**

Read [SECURITY.md](SECURITY.md) for the responsible disclosure process.

---

## Proposing Changes

1. Open a **Feature Request** issue and discuss the change before writing code.
2. Fork the repository through the GitHub UI.
3. Create a branch from `main` using the pattern `fix/<slug>` or `feat/<slug>`.
4. Make your changes following the standards below.
5. Open a pull request against `main` using the provided PR template.

---

## Development Standards

### Nginx Config

- 4-space indentation in all `.conf` files.
- All variables, maps, and zones must use the `spx_` prefix.
- Logic goes in `nginx/conf.d/000-spx-horizon-logic.conf` (http context).
- Do not add `if` blocks in server context for threat detection — use maps only.
- All blocking rules must honour the `$spx_firewall_active` check.
- Use `return 444;` for blocks. Never `return 403;` for security blocks.
- Comment every new regex with a plain-English description of what it catches.

### Python Scripts

- Python 3.11+ required.
- Only HTTPS URLs may be fetched.
- Use atomic writes (write to `.tmp`, then rename) for config file output.
- Run `python3 -m compileall scripts tests` before committing.

### Tests

- Tests are in `tests/test_firewall.py` using `pytest` and `requests`.
- `ConnectionError` = PASS (firewall ghosted). `200`/`404` on a blocked route = FAIL.
- Do not add placeholder or skipped tests — only commit runnable, asserting tests.

---

## Pull Request Checklist

Complete every item in the PR template before requesting review.
PRs that skip checklist items will be closed without merge.

---

## CI

Every PR must pass the **SPARXSTAR Quality Control** workflow:

1. `Nginx Syntax Validation` — `nginx -t` against the deployed config.
2. `Attack Simulation` — full `pytest` suite against a live Nginx instance.

A failing CI run blocks merge regardless of review approval.

---

## Commit Messages

Use the conventional format:

```
<type>(<scope>): <short summary>
```

Types: `fix`, `feat`, `docs`, `refactor`, `test`, `ci`, `chore`.

Examples:
- `fix(maps): correct path traversal regex for encoded slashes`
- `feat(geo): add configurable amplifier threshold variable`
- `docs(readme): update installation paths to nginx/ prefix`
- `ci(quality): pin pytest and requests versions`
