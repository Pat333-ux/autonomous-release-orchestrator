"""
Autonomous Changelog Generator
Synthesizes structured markdown changelogs from git commit history
prior to semantic release tagging.
Governing Authority: Governing Officer Tarwater
"""

import subprocess
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)


def get_commit_messages_since_last_tag() -> list[str]:
    """Retrieves commit messages since the last git tag, or all commits if no tag exists."""
    try:
        last_tag = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True, text=True, check=False
        ).stdout.strip()

        range_arg = f"{last_tag}..HEAD" if last_tag else "HEAD"
        result = subprocess.run(
            ["git", "log", range_arg, "--pretty=format:%s"],
            capture_output=True, text=True, check=True
        )
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except Exception as e:
        logging.warning(f"Could not fetch git commit history: {e}")
        return []


def generate_changelog_markdown() -> tuple[str, str]:
    """
    Parses commits and categorizes them into Features, Fixes, and Breaking Changes.
    Determines the required semantic version bump (major, minor, patch).
    """
    commits = get_commit_messages_since_last_tag()
    
    features = []
    fixes = []
    breaking = []
    bump_type = "patch"

    for msg in commits:
        if "BREAKING CHANGE" in msg or "!" in msg.split(":")[0]:
            breaking.append(msg)
            bump_type = "major"
        elif msg.startswith("feat") or "feat:" in msg:
            features.append(msg)
            if bump_type != "major":
                bump_type = "minor"
        elif msg.startswith("fix") or "fix:" in msg:
            fixes.append(msg)

    changelog = "### 🚀 Autonomous Release Changelog\n\n"
    
    if breaking:
        changelog += "#### ⚠️ Breaking Changes\n"
        for b in breaking:
            changelog += f"- {b}\n"
        changelog += "\n"

    if features:
        changelog += "#### ✨ New Features & Capabilities\n"
        for f in features:
            changelog += f"- {f}\n"
        changelog += "\n"

    if fixes:
        changelog += "#### 🐛 Bug Fixes & Self-Healing Patches\n"
        for fx in fixes:
            changelog += f"- {fx}\n"
        changelog += "\n"

    if not breaking and not features and not fixes:
        changelog += "- Routine system maintenance and automated dependency updates.\n"

    return bump_type, changelog
