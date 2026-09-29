#!/usr/bin/env python3
"""Update only the numeric telemetry counters; preserve the card design and language chart."""

import json
import os
import re
import urllib.request

USER = "ShrikarT"
WINS = 4
OUTPUTS = ("assets/lang-card.svg", "assets/telemetry.svg")


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


def display(number: int) -> str:
    return f"{number:02d}" if number < 100 else str(number)


def replace_counter(svg: str, y: int, value: int) -> str:
    pattern = rf'(<text x="545" y="{y}"[^>]*>)[^<]*(</text>)'
    updated, replacements = re.subn(pattern, rf"\g<1>{display(value)}\g<2>", svg, count=1)
    if replacements != 1:
        raise RuntimeError(f"Could not find telemetry counter at y={y}")
    return updated


def main():
    profile = get(f"https://api.github.com/users/{USER}")
    repos = list_repos()
    projects_shipped = sum(
        1
        for repo in repos
        if not repo.get("fork") and repo["name"] != USER and repo.get("language")
    )

    source = OUTPUTS[0]
    with open(source, encoding="utf-8") as file:
        svg = file.read()

    svg = replace_counter(svg, 122, profile["public_repos"])
    svg = replace_counter(svg, 176, projects_shipped)
    svg = replace_counter(svg, 230, WINS)

    for output in OUTPUTS:
        with open(output, "w", encoding="utf-8") as file:
            file.write(svg)

    print(
        f"updated counters only: public={profile['public_repos']} "
        f"shipped={projects_shipped} wins={WINS}"
    )


if __name__ == "__main__":
    main()
