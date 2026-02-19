#!/usr/bin/env python3
"""
SPARXSTAR Event Horizon - Bad Bot Signature Updater
Fetches a curated bad-bot User-Agent list, sanitizes it, and regenerates
the $spx_bad_bot map block inside conf.d/spx-horizon-logic.conf.

Usage:
    python scripts/update_bots.py [--output conf.d/spx-horizon-logic.conf]

The script replaces the entire "Bad User Agents" map block in the target
file so that manual edits are never needed.
"""

import argparse
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

# ---------------------------------------------------------------------------
# Source: https://raw.githubusercontent.com/mitchellkrogza/nginx-ultimate-bad-bot-blocker/master/_generator_lists/bad-user-agents.list
# This list is maintained by the community and updated regularly.
BOT_LIST_URL = (
    "https://raw.githubusercontent.com/mitchellkrogza/nginx-ultimate-bad-bot-blocker"
    "/master/_generator_lists/bad-user-agents.list"
)

# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LOGIC_FILE = REPO_ROOT / "conf.d" / "spx-horizon-logic.conf"

# Characters that are not safe inside an Nginx map string value
_UNSAFE_RE = re.compile(r'[";{}\\]')


def fetch_bot_list(url: str) -> list[str]:
    """Download the raw bot list and return non-empty, non-comment lines."""
    if not url.startswith("https://"):
        print(f"ERROR: Only HTTPS URLs are accepted: {url}", file=sys.stderr)
        sys.exit(1)

    print(f"Fetching bot list from {url} …", flush=True)
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            lines = response.read().decode("utf-8", errors="replace").splitlines()
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
        print(f"ERROR: Could not fetch bot list: {exc}", file=sys.stderr)
        sys.exit(1)

    agents = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        agents.append(stripped)

    print(f"  → {len(agents)} raw entries downloaded.", flush=True)
    return agents


def sanitize(agent: str) -> str:
    """Remove characters that would break the Nginx map syntax."""
    return _UNSAFE_RE.sub("", agent)


def build_map_block(agents: list[str]) -> str:
    """
    Convert a flat list of User-Agent strings into a single Nginx map block.
    Each entry is wrapped in a case-insensitive regex (~*).
    Entries are grouped 8 per map value line to keep files scannable.
    """
    sanitized = sorted({sanitize(a) for a in agents if sanitize(a)})

    # Build alternation groups of up to 8 entries per regex line
    group_size = 8
    groups = [
        sanitized[i : i + group_size] for i in range(0, len(sanitized), group_size)
    ]

    lines = [
        "# Bad User Agents (auto-generated — do not edit manually)",
        "# Run: python scripts/update_bots.py  to refresh.",
        "map $http_user_agent $spx_bad_bot {",
        "    default 0;",
        '    "~^$" 1;',
    ]
    for group in groups:
        escaped = [re.escape(a) for a in group]
        pattern = "|".join(escaped)
        lines.append(f'    "~*({pattern})" 1;')
    lines.append("}")

    return "\n".join(lines) + "\n"


def update_logic_file(logic_file: Path, new_map_block: str) -> None:
    """Replace the existing $spx_bad_bot map block with the regenerated one."""
    original = logic_file.read_text(encoding="utf-8")

    # Match from the comment/header above the map through the closing '}'
    pattern = re.compile(
        r"# Bad User Agents.*?^}",
        re.DOTALL | re.MULTILINE,
    )

    if not pattern.search(original):
        print(
            "WARNING: Could not locate the existing $spx_bad_bot map block.\n"
            "         Appending the new block at the end of the file.",
            file=sys.stderr,
        )
        updated = original.rstrip() + "\n\n" + new_map_block
    else:
        updated = pattern.sub(new_map_block.rstrip(), original)

    logic_file.write_text(updated, encoding="utf-8")
    print(f"  → Updated: {logic_file}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Update the $spx_bad_bot map block.")
    parser.add_argument(
        "--output",
        default=str(DEFAULT_LOGIC_FILE),
        help="Path to spx-horizon-logic.conf (default: %(default)s)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the generated map block without modifying any file.",
    )
    args = parser.parse_args()

    agents = fetch_bot_list(BOT_LIST_URL)
    map_block = build_map_block(agents)

    if args.dry_run:
        print("\n--- Generated map block (dry-run) ---")
        print(map_block)
        return

    logic_file = Path(args.output)
    if not logic_file.exists():
        print(f"ERROR: Logic file not found: {logic_file}", file=sys.stderr)
        sys.exit(1)

    update_logic_file(logic_file, map_block)
    print("Done. Run  nginx -t  to verify syntax before reloading.", flush=True)


if __name__ == "__main__":
    main()
