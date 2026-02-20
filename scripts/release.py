#!/usr/bin/env python3
"""Release automation script for Plottini.

This script automates the release process using Calendar Versioning (CalVer):
1. Calculating the next CalVer version (YYYY.MM.MICRO)
2. Updating all version files
3. Generating changelog from conventional commits
4. Committing, tagging, and pushing to origin

CalVer Format: YYYY.MM.MICRO (PEP 440 compliant)
- YYYY: Full year (e.g., 2026)
- MM: Month (01-12, zero-padded)
- MICRO: Release number within that month (0, 1, 2...)

Usage:
    python scripts/release.py              # Auto-calculate next version
    python scripts/release.py --micro      # Force micro increment within same month
    python scripts/release.py --version 2026.03.0  # Set explicit version
    python scripts/release.py --dry-run    # Preview changes
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# File paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent
VERSION_FILES = [
    "pyproject.toml",
    "src/plottini/__init__.py",
    "tests/test_basic.py",
    "tests/test_cli.py",
]
CHANGELOG_FILE = PROJECT_ROOT / "CHANGELOG.md"

# CalVer pattern: YYYY.MM.MICRO (with optional .devN suffix)
CALVER_PATTERN = re.compile(r"^(\d{4})\.(\d{2})\.(\d+)(?:\.dev\d+)?$")


def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run a shell command and return the result."""
    return subprocess.run(cmd, capture_output=True, text=True, check=check, cwd=PROJECT_ROOT)


def get_current_version() -> str:
    """Read current version from pyproject.toml."""
    pyproject = PROJECT_ROOT / "pyproject.toml"
    content = pyproject.read_text()
    match = re.search(r'^version = "([^"]+)"', content, re.MULTILINE)
    if not match:
        print("Error: Could not find version in pyproject.toml")
        sys.exit(1)
    return match.group(1)


def strip_dev_suffix(version: str) -> str:
    """Strip .devN suffix from version string."""
    return re.sub(r"\.dev\d+$", "", version)


def validate_calver(version: str) -> str:
    """Validate and normalize CalVer version string.

    Args:
        version: Version string to validate (e.g., "2026.02.0")

    Returns:
        Normalized version without .dev suffix

    Raises:
        SystemExit: If version format is invalid
    """
    normalized = strip_dev_suffix(version)

    if not CALVER_PATTERN.match(normalized):
        print(f"Error: Invalid CalVer format: {version}")
        print("Version must be in YYYY.MM.MICRO format (e.g., 2026.02.0)")
        sys.exit(1)

    return normalized


def calculate_next_version(current: str, force_micro: bool = False) -> str:
    """Calculate next CalVer version.

    Args:
        current: Current version (may have .dev suffix)
        force_micro: If True, increment micro within same year.month

    Returns:
        Next version in YYYY.MM.MICRO format
    """
    # Strip any .dev suffix from current version
    base_version = strip_dev_suffix(current)

    # Parse current version
    match = CALVER_PATTERN.match(base_version)
    if not match:
        # If current version isn't CalVer, start fresh with current date
        now = datetime.now(timezone.utc)
        return f"{now.year}.{now.month:02d}.0"

    current_year = int(match.group(1))
    current_month = int(match.group(2))
    current_micro = int(match.group(3))

    # Get current date
    now = datetime.now(timezone.utc)
    target_year = now.year
    target_month = now.month

    if force_micro or (target_year == current_year and target_month == current_month):
        # Same year.month: increment micro
        return f"{current_year}.{current_month:02d}.{current_micro + 1}"
    else:
        # New month: reset micro to 0
        return f"{target_year}.{target_month:02d}.0"


def calculate_dev_version(release_version: str) -> str:
    """Calculate the dev version to set after a release.

    After releasing 2026.02.0, set version to 2026.02.1.dev0
    """
    match = CALVER_PATTERN.match(release_version)
    if not match:
        print(f"Error: Invalid release version: {release_version}")
        sys.exit(1)

    year = int(match.group(1))
    month = int(match.group(2))
    micro = int(match.group(3))

    return f"{year}.{month:02d}.{micro + 1}.dev0"


def update_version_file(filepath: Path, old_version: str, new_version: str) -> bool:
    """Update version in a single file."""
    if not filepath.exists():
        print(f"  Warning: File not found: {filepath}")
        return False

    content = filepath.read_text()
    # Create replacement pattern based on the file type
    if "pyproject.toml" in str(filepath):
        new_content = re.sub(
            r'^version = "[^"]+"', f'version = "{new_version}"', content, flags=re.MULTILINE
        )
    elif "__init__.py" in str(filepath):
        new_content = re.sub(
            r'^__version__ = "[^"]+"',
            f'__version__ = "{new_version}"',
            content,
            flags=re.MULTILINE,
        )
    elif "test_basic.py" in str(filepath):
        # Match any version format for replacement
        new_content = re.sub(
            r'__version__ == "[^"]+"',
            f'__version__ == "{new_version}"',
            content,
        )
    elif "test_cli.py" in str(filepath):
        # Match any version format for replacement
        new_content = re.sub(
            r"Plottini version [^\s]+",
            f"Plottini version {new_version}",
            content,
        )
    else:
        return False

    if new_content != content:
        filepath.write_text(new_content)
        return True
    return False


def update_all_version_files(old_version: str, new_version: str) -> None:
    """Update version in all tracked files."""
    print("\nUpdating files...")
    for filepath in VERSION_FILES:
        full_path = PROJECT_ROOT / filepath
        if update_version_file(full_path, old_version, new_version):
            print(f"  ✓ {filepath}")
        else:
            print(f"  ✗ {filepath} (no changes or not found)")


def get_commits_since_tag(tag: str) -> list[dict[str, str]]:
    """Get commits since the specified tag.

    Uses full commit message (subject + body) to detect BREAKING CHANGE markers.
    """
    try:
        # Use %B for full message, %h for short SHA, with explicit separators
        # %x1f is unit separator, %x1e is record separator
        result = run_command(
            [
                "git",
                "log",
                f"{tag}..HEAD",
                "--pretty=format:%B%x1f%h%x1e",
                "--no-merges",
            ],
            check=False,
        )
        if result.returncode != 0:
            # Tag might not exist, get recent commits
            result = run_command(
                [
                    "git",
                    "log",
                    "-50",
                    "--pretty=format:%B%x1f%h%x1e",
                    "--no-merges",
                ],
                check=False,
            )
    except Exception:
        return []

    commits: list[dict[str, str]] = []
    output = result.stdout
    if not output:
        return commits

    # Split by record separator (\x1e) to get each commit entry
    for entry in output.strip().split("\x1e"):
        if not entry.strip():
            continue
        # Each entry is "full_message<US>sha" where <US> is \x1f
        if "\x1f" not in entry:
            continue
        message, sha = entry.rsplit("\x1f", 1)
        commits.append({"message": message.strip(), "sha": sha.strip()})
    return commits


def parse_conventional_commit(full_message: str) -> tuple[str | None, str | None, bool, str]:
    """Parse a conventional commit message.

    Args:
        full_message: Full commit message (subject + body)

    Returns: (type, scope, is_breaking, subject_line)
    """
    # Get subject line (first line of message)
    subject = full_message.split("\n")[0].strip()

    # Pattern: type(scope)!: description or type!: description or type: description
    pattern = r"^(\w+)(?:\(([^)]+)\))?(!)?\s*:\s*(.+)$"
    match = re.match(pattern, subject)
    if match:
        commit_type, scope, breaking, description = match.groups()
        # Check for breaking change in subject (!) or body (BREAKING CHANGE:)
        is_breaking = breaking == "!" or "BREAKING CHANGE" in full_message
        return commit_type, scope, is_breaking, subject
    return None, None, False, subject


def generate_changelog_section(version: str, commits: list[dict[str, str]]) -> str:
    """Generate changelog section from commits."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    sections: dict[str, list[str]] = {
        "Breaking Changes": [],
        "Features": [],
        "Fixes": [],
        "Other": [],
    }

    for commit in commits:
        commit_type, scope, is_breaking, subject = parse_conventional_commit(commit["message"])

        # Determine category
        if is_breaking:
            category = "Breaking Changes"
        elif commit_type == "feat":
            category = "Features"
        elif commit_type == "fix":
            category = "Fixes"
        else:
            category = "Other"

        # Use commit subject line as changelog entry
        sections[category].append(f"- {subject}")

    # Build changelog section
    lines = [f"## [{version}] - {today}", ""]

    # Order: Breaking Changes, Features, Fixes, Other
    for category in ["Breaking Changes", "Features", "Fixes", "Other"]:
        if sections[category]:
            lines.append(f"### {category}")
            lines.append("")
            lines.extend(sections[category])
            lines.append("")

    return "\n".join(lines)


def update_changelog(version: str, commits: list[dict[str, str]]) -> None:
    """Update CHANGELOG.md with new version section."""
    print("\nGenerating changelog...")
    print(f"  Found {len(commits)} commits since last tag")

    new_section = generate_changelog_section(version, commits)

    if CHANGELOG_FILE.exists():
        content = CHANGELOG_FILE.read_text()
        # Insert after the ## [Unreleased] section or at the top after header
        unreleased_pattern = r"(## \[Unreleased\].*?\n)"
        if re.search(unreleased_pattern, content):
            new_content = re.sub(unreleased_pattern, rf"\1\n{new_section}\n", content)
        else:
            # Find first ## section and insert before it
            first_section = re.search(r"^## \[", content, re.MULTILINE)
            if first_section:
                pos = first_section.start()
                new_content = content[:pos] + new_section + "\n" + content[pos:]
            else:
                new_content = content + "\n" + new_section
    else:
        # Create new changelog
        new_content = f"""# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project uses [Calendar Versioning](https://calver.org/) (YYYY.MM.MICRO).

## [Unreleased]

{new_section}
"""

    CHANGELOG_FILE.write_text(new_content)
    print("  ✓ CHANGELOG.md updated")


def git_commit_and_tag(version: str) -> None:
    """Commit changes and create tag."""
    print("\nCommitting and tagging...")

    # Stage all version files and changelog
    files_to_add = VERSION_FILES + ["CHANGELOG.md"]
    for filepath in files_to_add:
        full_path = PROJECT_ROOT / filepath
        if full_path.exists():
            run_command(["git", "add", str(full_path)])

    # Commit
    run_command(["git", "commit", "-m", f"chore(release): {version}"])
    print(f"  ✓ Committed: chore(release): {version}")

    # Tag
    run_command(["git", "tag", "-a", f"v{version}", "-m", f"Release v{version}"])
    print(f"  ✓ Tagged: v{version}")


def git_push() -> None:
    """Push commit and tags to origin."""
    print("\nPushing to origin...")

    # Get current branch
    result = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    branch = result.stdout.strip()

    run_command(["git", "push", "origin", branch, "--tags"])
    print(f"  ✓ Pushed {branch} and tags")


def get_last_tag() -> str | None:
    """Get the most recent version tag."""
    result = run_command(["git", "describe", "--tags", "--abbrev=0", "--match", "v*"], check=False)
    if result.returncode == 0:
        return result.stdout.strip()
    return None


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Release automation for Plottini using CalVer (YYYY.MM.MICRO)"
    )
    parser.add_argument(
        "--micro",
        action="store_true",
        help="Force micro version increment within same month",
    )
    parser.add_argument(
        "--version",
        dest="explicit_version",
        help="Set explicit version (e.g., 2026.03.0)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )

    args = parser.parse_args()

    # Get current version
    current_version = get_current_version()
    print(f"Current version: {current_version}")

    # Calculate new version
    if args.explicit_version:
        new_version = validate_calver(args.explicit_version)
    else:
        new_version = calculate_next_version(current_version, force_micro=args.micro)

    print(f"New version: {new_version}")

    # Calculate dev version for after release
    dev_version = calculate_dev_version(new_version)
    print(f"Post-release dev version: {dev_version}")

    if args.dry_run:
        print("\n[DRY RUN] Would perform the following actions:")
        print(f"  - Update version files from {current_version} to {new_version}")
        print("  - Generate changelog from commits")
        print(f"  - Commit: chore(release): {new_version}")
        print(f"  - Tag: v{new_version}")
        print("  - Push to origin")
        print(f"  - Update version files to {dev_version}")
        print(f"  - Commit: chore(release): bump to {dev_version}")
        print("  - Push to origin")
        sys.exit(0)

    # Check for uncommitted changes
    result = run_command(["git", "status", "--porcelain"], check=False)
    if result.stdout.strip():
        print("\nError: Working directory has uncommitted changes.")
        print("Please commit or stash them before releasing.")
        sys.exit(1)

    # Update version files to release version
    update_all_version_files(current_version, new_version)

    # Get commits since last tag and generate changelog
    last_tag = get_last_tag()
    if last_tag:
        commits = get_commits_since_tag(last_tag)
    else:
        commits = get_commits_since_tag("HEAD~50")  # Fallback: last 50 commits

    update_changelog(new_version, commits)

    # Commit and tag release
    git_commit_and_tag(new_version)

    # Push release
    git_push()

    print(f"\n✓ Released v{new_version}")

    # Now bump to dev version
    print("\nBumping to development version...")
    update_all_version_files(new_version, dev_version)

    # Stage and commit dev version
    for filepath in VERSION_FILES:
        full_path = PROJECT_ROOT / filepath
        if full_path.exists():
            run_command(["git", "add", str(full_path)])

    run_command(["git", "commit", "-m", f"chore(release): bump to {dev_version}"])
    print(f"  ✓ Committed: chore(release): bump to {dev_version}")

    # Push dev version commit
    result = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    branch = result.stdout.strip()
    run_command(["git", "push", "origin", branch])
    print(f"  ✓ Pushed {branch}")

    print("\nPyPI publish will be triggered automatically by the tag push.")


if __name__ == "__main__":
    main()
