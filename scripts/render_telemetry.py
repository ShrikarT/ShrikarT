#!/usr/bin/env python3
"""Refresh the profile telemetry cards without changing their design."""

import html
import json
import os
import sys
import urllib.request
from collections import Counter

USER = "ShrikarT"
WINS = 6
DEFAULT_OUTPUTS = ("assets/lang-card.svg", "assets/telemetry.svg")


def get(url: str):
    headers = {
        "User-Agent": "profile-telemetry",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def list_repos():
    repos = []
    page = 1
    while True:
        batch = get(
            f"https://api.github.com/users/{USER}/repos?per_page=100&page={page}&type=owner"
        )
        repos.extend(batch)
        if len(batch) < 100:
            return repos
        page += 1


def percent_rows(counts: Counter) -> list[tuple[str, int]]:
    ranked = counts.most_common()
    top = ranked[:5]
    other = sum(counts.values()) - sum(amount for _, amount in top)
    rows = list(top)
    if other:
        rows.append(("other", other))

    total = sum(amount for _, amount in rows) or 1
    raw = [100 * amount / total for _, amount in rows]
    percentages = [int(value) for value in raw]
    remainder = 100 - sum(percentages)
    order = sorted(
        range(len(rows)), key=lambda index: raw[index] - percentages[index], reverse=True
    )
    for index in order[:remainder]:
        percentages[index] += 1
    return [(name.lower(), percent) for (name, _), percent in zip(rows, percentages)]


def render(public_repos: int, projects_shipped: int, rows: list[tuple[str, int]]) -> str:
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

    for index, (name, percent) in enumerate(rows[:6]):
        y = name_y[index]
        width = max(8, percent * 8)
        safe_name = html.escape(name)
        lines.extend(
            [
                f'  <text x="30" y="{y}" fill="#FFFFFF" font-family="monospace" font-size="11">{safe_name}</text>',
                f'  <rect x="30" y="{y + 8}" width="{width}" height="6" fill="#FFFFFF"/>',
                f'  <text x="{30 + width + 10}" y="{y + 15}" fill="#FFFFFF" font-family="monospace" font-size="10" opacity="0.7">{percent}%</text>',
                "",
            ]
        )

    def display(number: int) -> str:
        return f"{number:02d}" if number < 100 else str(number)

    lines.extend(
        [
            '  <rect x="500" y="78" width="1" height="212" fill="#FFFFFF" opacity="0.25"/>',
            "",
            f'  <text x="545" y="122" fill="#FFFFFF" font-family="monospace" font-size="32">{display(public_repos)}</text>',
            '  <text x="620" y="118" fill="#FFFFFF" font-family="monospace" font-size="10" letter-spacing="2" opacity="0.75">PUBLIC REPOSITORIES</text>',
            "",
            f'  <text x="545" y="176" fill="#FFFFFF" font-family="monospace" font-size="32">{display(projects_shipped)}</text>',
            '  <text x="620" y="172" fill="#FFFFFF" font-family="monospace" font-size="10" letter-spacing="2" opacity="0.75">PROJECTS SHIPPED</text>',
            "",
            f'  <text x="545" y="230" fill="#FFFFFF" font-family="monospace" font-size="32">{display(WINS)}</text>',
            '  <text x="620" y="226" fill="#FFFFFF" font-family="monospace" font-size="10" letter-spacing="2" opacity="0.75">COMPETITIONS WON</text>',
            "",
            '  <text x="545" y="284" fill="#FFFFFF" font-family="monospace" font-size="32">∞</text>',
            '  <text x="620" y="280" fill="#FFFFFF" font-family="monospace" font-size="10" letter-spacing="2" opacity="0.75">TERMINAL TABS OPEN</text>',
            "</svg>",
            "",
        ]
    )
    return "\n".join(lines)


def main():
    profile = get(f"https://api.github.com/users/{USER}")
    repos = list_repos()
    projects = [
        repo
        for repo in repos
        if not repo.get("fork") and repo["name"] != USER and repo.get("language")
    ]
    counts = Counter(repo["language"] for repo in projects)
    if not counts:
        sys.exit("No repository languages found; refusing to blank the chart.")

    rows = percent_rows(counts)
    svg = render(profile["public_repos"], len(projects), rows)
    outputs = tuple(sys.argv[1:]) or DEFAULT_OUTPUTS
    for output in outputs:
        os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
        with open(output, "w", encoding="utf-8") as file:
            file.write(svg)

    print(
        f"updated {', '.join(outputs)}: public={profile['public_repos']} "
        f"shipped={len(projects)} languages={rows}"
    )


if __name__ == "__main__":
    main()
