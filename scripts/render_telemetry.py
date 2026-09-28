#!/usr/bin/env python3
"""Rewrite assets/telemetry.svg from live GitHub stats.

Same canvas, type, and bars. Only the language mix and the counts move.
Competitions won and the terminal-tabs joke are not on the API, so they stay.
"""

import json
import os
import sys
import urllib.request

USER = "ShrikarT"
WINS = 3  # namastejupiverse, avalanche team1, avalanche pitch day
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


def main():
    me = get(f"https://api.github.com/users/{USER}")
    repos = list_repos()
    owned = [r for r in repos if not r.get("fork") and r["name"] != USER]

    langs = {}
    for repo in owned:
        try:
            data = get(repo["languages_url"])
        except Exception as exc:
            print(f"skip {repo['name']}: {exc}", file=sys.stderr)
            continue
        for name, n in data.items():
            langs[name] = langs.get(name, 0) + n

    total = sum(langs.values())
    if total <= 0:
        sys.exit("no language bytes; refusing to blank the chart")

    ranked = sorted(langs.items(), key=lambda kv: -kv[1])
    top = ranked[:5]
    other = total - sum(v for _, v in top)
    rows = [(name.lower(), n) for name, n in top]
    if other > 0:
        rows.append(("other", other))
    rows = rows[:6]

    def bar_w(n):
        return max(8, min(400, round(400 * n / total)))

    name_y = [104, 138, 172, 206, 240, 274]
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="320" viewBox="0 0 900 320">',
        '  <rect width="900" height="320" fill="#0A0A0A"/>',
        '  <text x="30" y="36" fill="#FFFFFF" font-family="monospace" font-size="11" letter-spacing="3">TELEMETRY — WHAT THE HANDS ARE DOING</text>',
        '  <text x="870" y="36" fill="#FFFFFF" font-family="monospace" font-size="11" letter-spacing="3" text-anchor="end">FIG. 01</text>',
        '  <rect x="30" y="48" width="840" height="1" fill="#FFFFFF" opacity="0.55"/>',
        '  <text x="30" y="78" fill="#FFFFFF" font-family="monospace" font-size="10" letter-spacing="2" opacity="0.55">LANGUAGE DISTRIBUTION · LIVE</text>',
    ]
    for i, (name, n) in enumerate(rows):
        y = name_y[i]
        w = bar_w(n)
        pct = round(100 * n / total)
        label_x = min(w + 40, 460)
        parts.append(
            f'  <text x="30" y="{y}" fill="#FFFFFF" font-family="monospace" font-size="11">{name}</text>'
        )
        parts.append(
            f'  <rect x="30" y="{y + 8}" width="{w}" height="6" fill="#FFFFFF"/>'
        )
        parts.append(
            f'  <text x="{label_x}" y="{y + 15}" fill="#FFFFFF" font-family="monospace" font-size="10" opacity="0.7">{pct}%</text>'
        )

    def big(n):
        return f"{n:02d}" if n < 100 else str(n)

    stats = [
        (122, big(me["public_repos"]), "PUBLIC REPOSITORIES"),
        (176, big(len(owned)), "PROJECTS SHIPPED"),
        (230, big(WINS), "COMPETITIONS WON"),
        (284, "∞", "TERMINAL TABS OPEN"),
    ]
    parts.append('  <rect x="500" y="78" width="1" height="212" fill="#FFFFFF" opacity="0.25"/>')
    for y, num, label in stats:
        parts.append(
            f'  <text x="545" y="{y}" fill="#FFFFFF" font-family="monospace" font-size="32">{num}</text>'
        )
        parts.append(
            f'  <text x="620" y="{y - 4}" fill="#FFFFFF" font-family="monospace" font-size="10" letter-spacing="2" opacity="0.75">{label}</text>'
        )
    parts.append("</svg>")
    parts.append("")
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    print(f"wrote {OUT} repos={me['public_repos']} shipped={len(owned)}")


if __name__ == "__main__":
    main()
