#!/usr/bin/env python3
"""Release automation script for Plottini.

This script automates the release process by:
1. Bumping the version number based on semantic versioning
2. Updating all version files
3. Generating changelog from conventional commits
4. Committing, tagging, and pushing to origin

Usage:
    python scripts/release.py patch    # 0.6.0 -> 0.6.1
    python scripts/release.py minor    # 0.6.0 -> 0.7.0
    python scripts/release.py major    # 0.6.0 -> 1.0.0
    python scripts/release.py --version 1.0.0  # Set explicit version
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

# Semantic version pattern (X.Y.Z)
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")


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


def validate_version(version: str) -> str:
    """Validate and normalize version string.

    Args:
        version: Version string to validate (e.g., "1.0.0" or "v1.0.0")

    Returns:
        Normalized version without leading 'v'

    Raises:
        SystemExit: If version format is invalid
    """
    # Strip leading 'v' if present
    normalized = version.lstrip("v")

    if not VERSION_PATTERN.match(normalized):
        print(f"Error: Invalid version format: {version}")
        print("Version must be in X.Y.Z format (e.g., 1.0.0)")
        sys.exit(1)

    return normalized


def calculate_new_version(current: str, bump_type: str) -> str:
    """Calculate new version based on bump type.

    Note: This function expects a clean semantic version (X.Y.Z) without
    dev/pre-release suffixes. The CI workflow temporarily modifies versions
    with .dev suffixes for TestPyPI, but those changes are never committed.
    This script should only be run on a clean working directory with the
    base version in pyproject.toml.
    """
    parts = current.split(".")
    if len(parts) != 3:
        print(f"Error: Invalid version format: {current}")
        print("Expected X.Y.Z format (e.g., 0.6.0)")
        print("Note: Dev versions (e.g., 0.6.0.dev123) are not supported.")
        sys.exit(1)

    try:
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError:
        print(f"Error: Invalid version format: {current}")
        print("Version components must be integers (X.Y.Z)")
        sys.exit(1)

    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    elif bump_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        print(f"Error: Invalid bump type: {bump_type}")
        sys.exit(1)


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
        new_content = content.replace(f'== "{old_version}"', f'== "{new_version}"')
    elif "test_cli.py" in str(filepath):
        new_content = content.replace(f"version {old_version}", f"version {new_version}")
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
            print(f"  \u2713 {filepath}")
        else:
            print(f"  \u2717 {filepath} (no changes or not found)")


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
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

{new_section}
"""

    CHANGELOG_FILE.write_text(new_content)
    print("  \u2713 CHANGELOG.md updated")


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
    print(f"  \u2713 Committed: chore(release): {version}")

    # Tag
    run_command(["git", "tag", "-a", f"v{version}", "-m", f"Release v{version}"])
    print(f"  \u2713 Tagged: v{version}")


def git_push() -> None:
    """Push commit and tags to origin."""
    print("\nPushing to origin...")

    # Get current branch
    result = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    branch = result.stdout.strip()

    run_command(["git", "push", "origin", branch, "--tags"])
    print(f"  \u2713 Pushed {branch} and tags")


def get_last_tag() -> str | None:
    """Get the most recent version tag."""
    result = run_command(
        ["git", "describe", "--tags", "--abbrev=0", "--match", "v*.*.*"], check=False
    )
    if result.returncode == 0:
        return result.stdout.strip()
    return None


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Release automation for Plottini")
    parser.add_argument(
        "bump_type",
        nargs="?",
        choices=["major", "minor", "patch"],
        help="Version bump type",
    )
    parser.add_argument(
        "--version",
        dest="explicit_version",
        help="Set explicit version (e.g., 1.0.0)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )

    args = parser.parse_args()

    if not args.bump_type and not args.explicit_version:
        parser.print_help()
        sys.exit(1)

    # Get current version
    current_version = get_current_version()
    print(f"Current version: {current_version}")

    # Calculate new version
    if args.explicit_version:
        new_version = validate_version(args.explicit_version)
    else:
        new_version = calculate_new_version(current_version, args.bump_type)

    print(f"New version: {new_version}")

    if args.dry_run:
        print("\n[DRY RUN] Would perform the following actions:")
        print(f"  - Update version files from {current_version} to {new_version}")
        print("  - Generate changelog from commits")
        print(f"  - Commit: chore(release): {new_version}")
        print(f"  - Tag: v{new_version}")
        print("  - Push to origin")
        sys.exit(0)

    # Check for uncommitted changes
    result = run_command(["git", "status", "--porcelain"], check=False)
    if result.stdout.strip():
        print("\nError: Working directory has uncommitted changes.")
        print("Please commit or stash them before releasing.")
        sys.exit(1)

    # Update version files
    update_all_version_files(current_version, new_version)

    # Get commits since last tag and generate changelog
    last_tag = get_last_tag()
    if last_tag:
        commits = get_commits_since_tag(last_tag)
    else:
        commits = get_commits_since_tag("HEAD~50")  # Fallback: last 50 commits

    update_changelog(new_version, commits)

    # Commit and tag
    git_commit_and_tag(new_version)

    # Push
    git_push()

    print(f"\n\u2713 Released v{new_version}")
    print("PyPI publish will be triggered automatically by the tag push.")


if __name__ == "__main__":
    main()
