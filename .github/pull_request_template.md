## Summary

<!-- One paragraph: what does this PR do and why? -->

---

## Type of Change

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] Feature (non-breaking new capability)
- [ ] Breaking change (fix or feature that changes existing operator behaviour)
- [ ] Documentation only
- [ ] CI/CD / tooling
- [ ] Security fix

---

## Changes Made

<!-- List the files changed and what was changed in each. -->

- `nginx/conf.d/000-spx-horizon-logic.conf` —
- `nginx/snippets/` —
- `scripts/` —
- `tests/` —
- `docs/` —
- `README.md` —

---

## Testing

- [ ] `nginx -t` passes locally against the updated config.
- [ ] `pytest tests/test_firewall.py -v` passes locally.
- [ ] `python3 -m compileall scripts tests` passes.
- [ ] New or changed logic has a corresponding test (or explain why one is not needed).

**Test results:**
```
(paste pytest output here)
```

---

## Risk Assessment

**False-positive risk:** <!-- Could this change ghost legitimate traffic? Describe. -->

**False-negative risk:** <!-- Could this change allow malicious traffic through? Describe. -->

**Operator action required after merge:**
- [ ] None — transparent upgrade.
- [ ] Manual config edit required — describe below.
- [ ] New file must be deployed — describe below.
- [ ] Nginx reload required.
- [ ] Cron job must be updated.

**Details (if any operator action is required):**

---

## Breaking Change / Rollback Notes

<!-- If this is a breaking change, describe what operators must do to upgrade safely.
     If rollback is needed, what is the procedure? -->

---

## Checklist

- [ ] Branch is based on `main`.
- [ ] Commit messages follow `<type>(<scope>): <summary>` format.
- [ ] No secrets, credentials, or real IPs are present in any committed file.
- [ ] All new config variables follow the `spx_` prefix convention.
- [ ] Any new blocking rule uses `return 444;` (never `return 403;`).
- [ ] Any new blocking rule honours `$spx_firewall_active`.
- [ ] CHANGELOG.md updated if this is a user-facing change.
- [ ] README.md updated if installation or operation steps changed.
- [ ] CI is passing on this branch.
