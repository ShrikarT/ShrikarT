#!/usr/bin/env python3
"""Rewrite the telemetry card from GitHub primary languages.

Counts repos, not bytes. Byte share made one Circom repo look like a third
of the work and pulled Go in from inside other trees. One repo, one vote.
"""

import json
import os
import sys
import urllib.request
from collections import Counter

USER = "ShrikarT"
WINS = 3  # namastejupiverse, avalanche team1, avalanche pitch day
OUT = sys.argv[1] if len(sys.argv) > 1 else "assets/telemetry-card.svg"


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


def render(public_n: int, shipped_n: int, rows: list[tuple[str, int]]) -> str:
    total = sum(n for _, n in rows) or 1
    # Whole card stays inside 720px so the readme column cannot crop the stats.
    w, h = 720, 78 + len(rows) * 36 + 78
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        f'  <rect width="{w}" height="{h}" fill="#0A0A0A"/>',
        '  <text x="24" y="32" fill="#FFFFFF" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="12">TELEMETRY — WHAT THE HANDS ARE DOING</text>',
        f'  <text x="{w - 24}" y="32" fill="#FFFFFF" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="12" text-anchor="end">FIG. 01</text>',
        f'  <rect x="24" y="44" width="{w - 48}" height="1" fill="#FFFFFF" opacity="0.55"/>',
        '  <text x="24" y="68" fill="#FFFFFF" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="10" opacity="0.55">LANGUAGE BY REPO · NOT BY BYTES</text>',
    ]
    bar_max = 460
    for i, (name, n) in enumerate(rows):
        y = 96 + i * 36
        bw = max(6, round(bar_max * n / total))
        pct = round(100 * n / total)
        parts.append(
            f'  <text x="24" y="{y}" fill="#FFFFFF" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="13">{name}</text>'
        )
        parts.append(
            f'  <text x="{w - 24}" y="{y}" fill="#FFFFFF" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="13" text-anchor="end" opacity="0.85">{n} · {pct}%</text>'
        )
        parts.append(
            f'  <rect x="24" y="{y + 8}" width="{bw}" height="5" fill="#FFFFFF"/>'
        )

    base = 96 + len(rows) * 36 + 28
    stats = [
        (public_n if public_n < 100 else public_n, "PUBLIC REPOS"),
        (shipped_n, "REPOS WITH CODE"),
        (f"{WINS:02d}", "COMPETITIONS WON"),
        ("∞", "TERMINAL TABS"),
    ]
    col = (w - 48) / 4
    for i, (num, label) in enumerate(stats):
        x = 24 + int(i * col)
        shown = f"{num:02d}" if isinstance(num, int) and num < 100 else str(num)
        parts.append(
            f'  <text x="{x}" y="{base}" fill="#FFFFFF" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="26">{shown}</text>'
        )
        parts.append(
            f'  <text x="{x}" y="{base + 18}" fill="#FFFFFF" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="10" opacity="0.6">{label}</text>'
        )
    parts.append("</svg>")
    parts.append("")
    return "\n".join(parts)


def main():
    me = get(f"https://api.github.com/users/{USER}")
    repos = list_repos()
    owned = [r for r in repos if not r.get("fork") and r["name"] != USER]
    counts: Counter[str] = Counter()
    for repo in owned:
        counts[(repo.get("language") or "other").lower()] += 1
    if not counts:
        sys.exit("no repos; refusing to blank the chart")

    ranked = counts.most_common()
    top = ranked[:5]
    other = sum(counts.values()) - sum(n for _, n in top)
    rows = [(name, n) for name, n in top if name != "other"]
    other += sum(n for name, n in top if name == "other")
    if other:
        rows.append(("other", other))
    rows = rows[:6]

    svg = render(me["public_repos"], len(owned), rows)
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {OUT} public={me['public_repos']} repos={len(owned)} {rows}")


if __name__ == "__main__":
    main()
