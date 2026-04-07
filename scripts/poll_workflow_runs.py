"""Poll recent GitHub Actions workflow runs with authenticated GitHub API access."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any
from urllib import error, parse, request

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

API_BASE = "https://api.github.com"


def _github_token() -> str:
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if not token:
        raise RuntimeError(
            "Missing GitHub token. Set GITHUB_TOKEN (or GH_TOKEN) before polling workflow runs."
        )
    return token


def _request_json(url: str, token: str) -> dict[str, Any]:
    req = request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "predictive-ltv-survival-pipeline/actions-poll",
        },
    )
    try:
        with request.urlopen(req, timeout=20) as response:  # nosec: B310 - HTTPS GitHub API call
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API error {exc.code}: {details}") from exc


def fetch_workflow_runs(repo: str, limit: int = 10) -> list[dict[str, Any]]:
    token = _github_token()
    params = parse.urlencode({"per_page": str(limit)})
    url = f"{API_BASE}/repos/{repo}/actions/runs?{params}"
    payload = _request_json(url, token)
    return payload.get("workflow_runs", [])


def filter_runs(
    runs: list[dict[str, Any]],
    sha: str | None = None,
    workflow_name: str | None = None,
) -> list[dict[str, Any]]:
    out = runs
    if sha:
        out = [run for run in out if str(run.get("head_sha", "")).startswith(sha)]
    if workflow_name:
        out = [run for run in out if run.get("name") == workflow_name]
    return out


def _print_table(runs: list[dict[str, Any]]) -> None:
    if not runs:
        print("No workflow runs matched the provided filters.")
        return

    print(
        f"{'id':<12} {'workflow':<20} {'status':<12} {'conclusion':<12} {'sha':<8} url"
    )
    for run in runs:
        print(
            f"{str(run.get('id', '')):<12} "
            f"{str(run.get('name', ''))[:20]:<20} "
            f"{str(run.get('status', '')):<12} "
            f"{str(run.get('conclusion', '')):<12} "
            f"{str(run.get('head_sha', ''))[:7]:<8} "
            f"{run.get('html_url', '')}"
        )


def _all_completed(runs: list[dict[str, Any]]) -> bool:
    return all(run.get("status") == "completed" for run in runs)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Poll GitHub Actions workflow runs")
    parser.add_argument(
        "--repo",
        default="theo-lyd/predictive-ltv-survival-pipeline",
        help="Repository in owner/name format",
    )
    parser.add_argument("--limit", type=int, default=10, help="Number of recent runs to fetch")
    parser.add_argument(
        "--sha",
        help="Optional commit SHA (full or prefix) to filter workflow runs",
    )
    parser.add_argument(
        "--workflow",
        help="Optional workflow name filter (for example: CI, Enhanced CI/CD)",
    )
    parser.add_argument(
        "--wait",
        action="store_true",
        help="Poll until filtered runs are completed or timeout is reached",
    )
    parser.add_argument(
        "--interval-seconds",
        type=int,
        default=20,
        help="Polling interval when --wait is used",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=900,
        help="Maximum wait duration when --wait is used",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    args = parser.parse_args(argv)

    started = time.time()
    while True:
        runs = fetch_workflow_runs(args.repo, args.limit)
        filtered = filter_runs(runs, args.sha, args.workflow)

        if args.json:
            print(json.dumps(filtered, indent=2))
        else:
            _print_table(filtered)

        if not args.wait:
            return 0

        if filtered and _all_completed(filtered):
            return 0

        elapsed = time.time() - started
        if elapsed >= args.timeout_seconds:
            return 1

        time.sleep(max(args.interval_seconds, 1))


if __name__ == "__main__":
    raise SystemExit(main())
