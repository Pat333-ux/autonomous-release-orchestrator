"""
Autonomous Release Manager
Calculates semantic version bumps, creates git tags, and publishes 
automated GitHub releases governed by Officer Tarwater.
Governing Authority: Governing Officer Tarwater
"""

import os
import yaml
import logging
import requests
import subprocess
from changelog_generator import generate_changelog_markdown

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

GITHUB_API_URL = "https://api.github.com"


def get_github_headers() -> dict:
    token = os.getenv("GH_PAT") or os.getenv("GITHUB_TOKEN")
    if not token:
        raise EnvironmentError("Missing GH_PAT or GITHUB_TOKEN environment variable.")
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }


def calculate_next_version(bump_type: str) -> str:
    """Calculates the next semantic version based on the existing tag history."""
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True, text=True, check=False
        )
        latest_tag = result.stdout.strip().lstrip("v")
        if not latest_tag:
            return "v1.0.0"

        parts = [int(p) for p in latest_tag.split(".")]
        while len(parts) < 3:
            parts.append(0)
        major, minor, patch = parts

        if bump_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif bump_type == "minor":
            minor += 1
            patch = 0
        else:
            patch += 1

        return f"v{major}.{minor}.{patch}"
    except Exception:
        return "v1.0.0"


def verify_kill_switch_clearance() -> None:
    """Ensures Governing Officer Tarwater has not engaged the global kill switch."""
    if os.path.exists("governance_config.yaml"):
        with open("governance_config.yaml", "r", encoding="utf-8") as f:
            policy = yaml.safe_load(f)
        if policy.get("communication_and_oversight", {}).get("emergency_override", {}).get("global_kill_switch"):
            logging.critical("EMERGENCY OVERRIDE ACTIVE: Release Orchestrator halted.")
            raise SystemExit(1)
    
    if os.getenv("TARWATER_KILL_SWITCH", "false").lower() == "true":
        logging.critical("EMERGENCY OVERRIDE ACTIVE: Release Orchestrator halted by environment variable.")
        raise SystemExit(1)


def publish_release() -> None:
    """Orchestrates version calculation, changelog generation, tagging, and GitHub release publishing."""
    verify_kill_switch_clearance()

    repo_slug = os.getenv("GITHUB_REPOSITORY")
    if not repo_slug:
        raise EnvironmentError("Missing GITHUB_REPOSITORY environment variable.")

    bump_type, changelog_body = generate_changelog_markdown()
    new_version = calculate_next_version(bump_type)

    logging.info(f"Calculated version bump [{bump_type.upper()}]: New release -> {new_version}")

    headers = get_github_headers()
    
    # Create GitHub Release
    release_payload = {
        "tag_name": new_version,
        "target_commitish": "main",
        "name": f"Autonomous Release {new_version}",
        "body": changelog_body + f"\n\n*Governed under the authority of Governing Officer Tarwater.*",
        "draft": False,
        "prerelease": False
    }

    resp = requests.post(
        f"{GITHUB_API_URL}/repos/{repo_slug}/releases",
        headers=headers,
        json=release_payload,
        timeout=30
    )

    if resp.status_code == 201:
        logging.info(f"Successfully published release {new_version} for {repo_slug}!")
    else:
        logging.error(f"Failed to publish GitHub release: {resp.text}")
        raise SystemExit(1)


if __name__ == "__main__":
    publish_release()
