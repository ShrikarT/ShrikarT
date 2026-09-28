#!/usr/bin/env python3
"""Refresh assets/telemetry.svg. Same card as the original. Only the numbers move.

One repo, one vote, using the language GitHub shows on the repo.
Byte totals made GhostLaunch's circuits and its gnark module look like the whole profile.
"""

import os
import sys
import json
import urllib.request
from collections import Counter

USER = "ShrikarT"
WINS = 3
OUT = sys.argv[1] if len(sys.argv) > 1 else "assets/telemetry.svg"


def get(url: str):
    headers = {
        "User-Agent": "profile-telemetry",
        "Accept": "application/vnd.github+json",
    }
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=60) as res:
        return json.load(res)


def list_repos():
    repos = []
    page = 1
    while True:
        batch = get(
            f"https://api.github.com/users/{USER}/repos?per_page=100&page={page}&type=owner"
        )
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return repos


def percent_rows(counts: Counter) -> list[tuple[str, int]]:
    ranked = counts.most_common()
    top = ranked[:5]
    names = [n for n, _ in top]
    other = sum(counts.values()) - sum(n for _, n in top)
    rows = list(top)
    if other:
        rows.append(("other", other))
    total = sum(n for _, n in rows) or 1
    raw = [100 * n / total for _, n in rows]
    floors = [int(v) for v in raw]
    left = 100 - sum(floors)
    order = sorted(range(len(rows)), key=lambda i: raw[i] - floors[i], reverse=True)
    for i in order[:left]:
        floors[i] += 1
    return [(name, pct) for (name, _), pct in zip(rows, floors)]


def render(public_n: int, shipped_n: int, rows: list[tuple[str, int]]) -> str:
    name_y = [104, 138, 172, 206, 240, 274]
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="320" viewBox="0 0 900 320">',
        '  <rect width="900" height="320" fill="#0A0A0A"/>',
        "",
        '  <text x="30" y="36" fill="#FFFFFF" font-family="monospace" font-size="11" letter-spacing="3">TELEMETRY — WHAT THE HANDS ARE DOING</text>',
        '  <text x="870" y="36" fill="#FFFFFF" font-family="monospace" font-size="11" letter-spacing="3" text-anchor="end">FIG. 01</text>',
        '  <rect x="30" y="48" width="840" height="1" fill="#FFFFFF" opacity="0.55"/>',
        "",
        '  <text x="30" y="78" fill="#FFFFFF" font-family="monospace" font-size="10" letter-spacing="2" opacity="0.55">LANGUAGE DISTRIBUTION · EST.</text>',
        "",
    ]
    for i, (name, pct) in enumerate(rows[:6]):
        y = name_y[i]
        width = max(8, pct * 8)
        lines.append(
            f'  <text x="30" y="{y}" fill="#FFFFFF" font-family="monospace" font-size="11">{name}</text>'
        )
        lines.append(
            f'  <rect x="30" y="{y + 8}" width="{width}" height="6" fill="#FFFFFF"/>'
        )
        lines.append(
            f'  <text x="{30 + width + 10}" y="{y + 15}" fill="#FFFFFF" font-family="monospace" font-size="10" opacity="0.7">{pct}%</text>'
        )
        lines.append("")

    def big(n: int) -> str:
        return f"{n:02d}" if n < 100 else str(n)

    lines += [
        '  <rect x="500" y="78" width="1" height="212" fill="#FFFFFF" opacity="0.25"/>',
        "",
        f'  <text x="545" y="122" fill="#FFFFFF" font-family="monospace" font-size="32">{big(public_n)}</text>',
        '  <text x="620" y="118" fill="#FFFFFF" font-family="monospace" font-size="10" letter-spacing="2" opacity="0.75">PUBLIC REPOSITORIES</text>',
        "",
        f'  <text x="545" y="176" fill="#FFFFFF" font-family="monospace" font-size="32">{big(shipped_n)}</text>',
        '  <text x="620" y="172" fill="#FFFFFF" font-family="monospace" font-size="10" letter-spacing="2" opacity="0.75">PROJECTS SHIPPED</text>',
        "",
        f'  <text x="545" y="230" fill="#FFFFFF" font-family="monospace" font-size="32">{big(WINS)}</text>',
        '  <text x="620" y="226" fill="#FFFFFF" font-family="monospace" font-size="10" letter-spacing="2" opacity="0.75">COMPETITIONS WON</text>',
        "",
        '  <text x="545" y="284" fill="#FFFFFF" font-family="monospace" font-size="32">∞</text>',
        '  <text x="620" y="280" fill="#FFFFFF" font-family="monospace" font-size="10" letter-spacing="2" opacity="0.75">TERMINAL TABS OPEN</text>',
        "</svg>",
        "",
    ]
    return "\n".join(lines)


def main():
    me = get(f"https://api.github.com/users/{USER}")
    repos = list_repos()
    owned = [r for r in repos if not r.get("fork") and r["name"] != USER and r.get("language")]
    counts: Counter[str] = Counter((r["language"] or "other").lower() for r in owned)
    if not counts:
        sys.exit("no languages; refusing to blank the chart")
    rows = percent_rows(counts)
    svg = render(me["public_repos"], len(owned), rows)
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {OUT} public={me['public_repos']} shipped={len(owned)} {rows}")


if __name__ == "__main__":
    main()
