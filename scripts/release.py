#!/usr/bin/env python3
"""Release automation script for Plottini.

This script automates the release process using Calendar Versioning (CalVer):
1. --prepare: Create a release PR with version updates and changelog
2. --tag: Tag the release on main after PR is merged
3. --post-release: Bump to dev version after tagging

CalVer Format: YYYY.M.MICRO (PEP 440 compliant, no zero-padding)
- YYYY: Full year (e.g., 2026)
- M: Month (1-12, no zero-padding for PEP 440 compliance)
- MICRO: Release number within that month (0, 1, 2...)

Usage:
    # Step 1: Create release PR (from main)
    python scripts/release.py --prepare

    # Step 2: After PR is merged, tag the release (on main)
    git checkout main && git pull
    python scripts/release.py --tag

    # Step 3: Bump to dev version (on main)
    python scripts/release.py --post-release

    # With explicit version:
    python scripts/release.py --prepare --version 2026.2.0
    python scripts/release.py --tag --version 2026.2.0
    python scripts/release.py --post-release --version 2026.2.0

    # Preview changes:
    python scripts/release.py --prepare --dry-run
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
    "uv.lock",
]
CHANGELOG_FILE = PROJECT_ROOT / "CHANGELOG.md"

# CalVer pattern: YYYY.M.MICRO (with optional .devN suffix)
# Accepts 1-2 digit months for flexibility (e.g., 2026.2.0 or 2026.02.0)
CALVER_PATTERN = re.compile(r"^(\d{4})\.(\d{1,2})\.(\d+)(?:\.dev\d+)?$")


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
        version: Version string to validate (e.g., "2026.2.0" or "2026.02.0")

    Returns:
        PEP 440 compliant version (no zero-padding), without .dev suffix

    Raises:
        SystemExit: If version format is invalid
    """
    normalized = strip_dev_suffix(version)

    match = CALVER_PATTERN.match(normalized)
    if not match:
        print(f"Error: Invalid CalVer format: {version}")
        print("Version must be in YYYY.M.MICRO format (e.g., 2026.2.0)")
        sys.exit(1)

    year_str, month_str, micro_str = match.groups()
    month_int = int(month_str)
    micro_int = int(micro_str)

    if not (1 <= month_int <= 12):
        print(f"Error: Invalid CalVer month: {version}")
        print("Month component must be between 1 and 12.")
        sys.exit(1)

    # Return PEP 440 compliant version (no zero-padding)
    return f"{year_str}.{month_int}.{micro_int}"


def calculate_next_version(current: str, force_micro: bool = False) -> str:
    """Calculate next CalVer version.

    Args:
        current: Current version (may have .dev suffix)
        force_micro: If True, increment micro within same year.month

    Returns:
        Next version in YYYY.M.MICRO format (PEP 440 compliant)
    """
    # Strip any .dev suffix from current version
    base_version = strip_dev_suffix(current)

    # Parse current version
    match = CALVER_PATTERN.match(base_version)
    if not match:
        # If current version isn't CalVer, start fresh with current date
        now = datetime.now(timezone.utc)
        return f"{now.year}.{now.month}.0"

    current_year = int(match.group(1))
    current_month = int(match.group(2))
    current_micro = int(match.group(3))

    # Get current date
    now = datetime.now(timezone.utc)
    target_year = now.year
    target_month = now.month

    if force_micro or (target_year == current_year and target_month == current_month):
        # Same year.month: increment micro
        return f"{current_year}.{current_month}.{current_micro + 1}"
    else:
        # New month: reset micro to 0
        return f"{target_year}.{target_month}.0"


def calculate_dev_version(release_version: str) -> str:
    """Calculate the dev version to set after a release.

    After releasing 2026.2.0, set version to 2026.2.1.dev0
    """
    match = CALVER_PATTERN.match(release_version)
    if not match:
        print(f"Error: Invalid release version: {release_version}")
        sys.exit(1)

    year = int(match.group(1))
    month = int(match.group(2))
    micro = int(match.group(3))

    return f"{year}.{month}.{micro + 1}.dev0"


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
        # Match version number only (not the closing quote)
        new_content = re.sub(
            r"Plottini version [0-9]+\.[0-9]+\.[0-9]+(?:\.dev[0-9]+)?",
            f"Plottini version {new_version}",
            content,
        )
    elif "uv.lock" in str(filepath):
        # Match the plottini package version line
        new_content = re.sub(
            r'(name = "plottini"\nversion = ")[^"]+(")',
            rf"\g<1>{new_version}\g<2>",
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


def get_last_tag() -> str | None:
    """Get the most recent version tag."""
    result = run_command(["git", "describe", "--tags", "--abbrev=0", "--match", "v*"], check=False)
    if result.returncode == 0:
        return result.stdout.strip()
    return None


def get_current_branch() -> str:
    """Get the current git branch name."""
    result = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    return result.stdout.strip()


def verify_on_main() -> None:
    """Verify we're on the main branch, exit if not."""
    branch = get_current_branch()
    if branch != "main":
        print(f"Error: Must be on main branch to perform this action (currently on '{branch}')")
        sys.exit(1)


def verify_clean_working_directory() -> None:
    """Verify working directory has no uncommitted changes."""
    result = run_command(["git", "status", "--porcelain"], check=False)
    if result.stdout.strip():
        print("\nError: Working directory has uncommitted changes.")
        print("Please commit or stash them before releasing.")
        sys.exit(1)


def verify_gh_cli_available() -> None:
    """Verify GitHub CLI (gh) is installed and authenticated."""
    result = run_command(["gh", "auth", "status"], check=False)
    if result.returncode != 0:
        print("Error: GitHub CLI (gh) is not installed or not authenticated.")
        print("Install it from https://cli.github.com/ and run 'gh auth login'")
        sys.exit(1)


def branch_exists(branch_name: str) -> bool:
    """Check if a local branch exists."""
    result = run_command(["git", "rev-parse", "--verify", branch_name], check=False)
    return result.returncode == 0


def remote_branch_exists(branch_name: str) -> bool:
    """Check if a branch exists on remote origin."""
    result = run_command(["git", "ls-remote", "--heads", "origin", branch_name], check=False)
    return bool(result.stdout.strip())


def tag_exists(tag_name: str) -> bool:
    """Check if a tag exists."""
    result = run_command(["git", "rev-parse", "--verify", f"refs/tags/{tag_name}"], check=False)
    return result.returncode == 0


def verify_version_in_files(expected_version: str) -> None:
    """Verify the version in pyproject.toml matches the expected version."""
    current = get_current_version()
    # Normalize both versions for comparison (strip dev suffix)
    current_normalized = strip_dev_suffix(current)
    expected_normalized = strip_dev_suffix(expected_version)
    if current_normalized != expected_normalized:
        print(f"Error: Version mismatch. Files have {current}, expected {expected_version}")
        print("Make sure you're on the correct commit and using the correct --version.")
        sys.exit(1)


def verify_main_up_to_date() -> None:
    """Verify local main is up to date with origin/main."""
    print("\nFetching latest from origin...")
    run_command(["git", "fetch", "origin"])

    local_head = run_command(["git", "rev-parse", "HEAD"]).stdout.strip()
    remote_head = run_command(["git", "rev-parse", "origin/main"]).stdout.strip()

    if local_head != remote_head:
        print("Error: Local 'main' is not up to date with 'origin/main'.")
        print("Please run 'git pull --ff-only' and try again.")
        sys.exit(1)
    print("  ✓ Local main is up to date with origin/main")


def prepare_release(version: str, current_version: str, dry_run: bool) -> None:
    """Create a release branch with version updates and changelog, then create a PR.

    Args:
        version: The release version to prepare
        current_version: The current version in files
        dry_run: If True, only show what would be done
    """
    branch_name = f"release/{version}"

    if dry_run:
        print("\n[DRY RUN] Would perform the following actions:")
        print("  - Verify on main branch")
        print("  - Verify GitHub CLI is available")
        print(f"  - Create and checkout branch: {branch_name}")
        print(f"  - Update version files from {current_version} to {version}")
        print("  - Generate changelog from commits")
        print(f"  - Commit: chore(release): {version}")
        print(f"  - Push branch: {branch_name}")
        print(f"  - Create PR to main with title: chore(release): {version}")
        return

    # Verify prerequisites
    verify_on_main()
    print("  ✓ Verified on main branch")

    verify_gh_cli_available()
    print("  ✓ GitHub CLI is available")

    verify_clean_working_directory()

    # Check if branch already exists (locally or on remote)
    local_exists = branch_exists(branch_name)
    remote_exists = remote_branch_exists(branch_name)
    if local_exists or remote_exists:
        print(f"Error: Branch '{branch_name}' already exists.")
        if local_exists:
            print(f"  Delete local branch: git branch -D {branch_name}")
        if remote_exists:
            print(f"  Delete remote branch: git push origin --delete {branch_name}")
        sys.exit(1)

    # Create and checkout release branch
    print(f"\nCreating branch: {branch_name}")
    run_command(["git", "checkout", "-b", branch_name])
    print(f"  ✓ Created and checked out branch: {branch_name}")

    # Update version files
    update_all_version_files(current_version, version)

    # Get commits since last tag and generate changelog
    last_tag = get_last_tag()
    if last_tag:
        commits = get_commits_since_tag(last_tag)
    else:
        commits = get_commits_since_tag("HEAD~50")  # Fallback: last 50 commits

    update_changelog(version, commits)

    # Stage and commit
    print("\nCommitting changes...")
    files_to_add = VERSION_FILES + ["CHANGELOG.md"]
    for filepath in files_to_add:
        full_path = PROJECT_ROOT / filepath
        if full_path.exists():
            run_command(["git", "add", str(full_path)])

    run_command(["git", "commit", "-m", f"chore(release): {version}"])
    print(f"  ✓ Committed: chore(release): {version}")

    # Push branch
    print("\nPushing branch...")
    run_command(["git", "push", "-u", "origin", branch_name])
    print(f"  ✓ Pushed branch: {branch_name}")

    # Create PR
    print("\nCreating pull request...")
    pr_body = f"""## Release {version}

This PR prepares the release of version {version}.

### Changes
- Updated version in all tracked files
- Generated changelog from commits since last release

### After merging
1. Checkout main and pull: `git checkout main && git pull`
2. Tag the release: `python scripts/release.py --tag --version {version}`
3. Bump to dev version: `python scripts/release.py --post-release --version {version}`
"""
    run_command(
        [
            "gh",
            "pr",
            "create",
            "--title",
            f"chore(release): {version}",
            "--body",
            pr_body,
            "--base",
            "main",
        ]
    )
    print(f"  ✓ Created PR for release {version}")

    print(f"\n✓ Release PR prepared for v{version}")
    print("\nNext steps:")
    print("  1. Review and merge the PR")
    print("  2. After merge: git checkout main && git pull")
    print(f"  3. Tag release: python scripts/release.py --tag --version {version}")
    print(f"  4. Bump to dev: python scripts/release.py --post-release --version {version}")


def tag_release(version: str, dry_run: bool) -> None:
    """Create and push the release tag on main.

    Args:
        version: The release version to tag
        dry_run: If True, only show what would be done
    """
    tag_name = f"v{version}"

    if dry_run:
        print("\n[DRY RUN] Would perform the following actions:")
        print("  - Verify on main branch")
        print("  - Verify local main is up to date with origin/main")
        print("  - Verify version in files matches target version")
        print(f"  - Create annotated tag: {tag_name}")
        print(f"  - Push tag: {tag_name}")
        print("  - This will trigger the PyPI publish workflow")
        return

    # Verify on main branch
    verify_on_main()
    print("  ✓ Verified on main branch")

    # Verify local main is up to date
    verify_main_up_to_date()

    # Verify version in files matches
    verify_version_in_files(version)
    print(f"  ✓ Version in files matches {version}")

    # Check if tag already exists
    if tag_exists(tag_name):
        print(f"Error: Tag '{tag_name}' already exists.")
        print("If you need to re-tag, delete it first with:")
        print(f"  git tag -d {tag_name} && git push origin :refs/tags/{tag_name}")
        sys.exit(1)

    # Create annotated tag
    print(f"\nCreating tag: {tag_name}")
    run_command(["git", "tag", "-a", tag_name, "-m", f"Release {tag_name}"])
    print(f"  ✓ Created tag: {tag_name}")

    # Push tag
    print("\nPushing tag...")
    run_command(["git", "push", "origin", tag_name])
    print(f"  ✓ Pushed tag: {tag_name}")

    print(f"\n✓ Tagged release {tag_name}")
    print("\nPyPI publish will be triggered automatically by the tag push.")
    print(f"\nNext step: python scripts/release.py --post-release --version {version}")


def post_release(version: str, dry_run: bool) -> None:
    """Bump to dev version after a release.

    Note: This commits directly to main, bypassing PR review. This is intentional
    for the dev version bump as it's a routine post-release step.

    Args:
        version: The release version that was just tagged
        dry_run: If True, only show what would be done
    """
    dev_version = calculate_dev_version(version)

    if dry_run:
        print("\n[DRY RUN] Would perform the following actions:")
        print("  - Verify on main branch")
        print("  - Verify local main is up to date with origin/main")
        print("  - Verify version in files matches release version")
        print(f"  - Update version files from {version} to {dev_version}")
        print(f"  - Commit: chore(release): bump to {dev_version} [skip ci]")
        print("  - Push to main (direct push, no PR)")
        return

    # Verify on main branch
    verify_on_main()
    print("  ✓ Verified on main branch")

    # Verify local main is up to date
    verify_main_up_to_date()

    # Verify clean working directory
    verify_clean_working_directory()

    # Verify version in files matches the release version
    verify_version_in_files(version)
    print(f"  ✓ Version in files matches {version}")

    # Update version files to dev version
    update_all_version_files(version, dev_version)

    # Stage and commit with [skip ci]
    print("\nCommitting dev version bump...")
    for filepath in VERSION_FILES:
        full_path = PROJECT_ROOT / filepath
        if full_path.exists():
            run_command(["git", "add", str(full_path)])

    run_command(["git", "commit", "-m", f"chore(release): bump to {dev_version} [skip ci]"])
    print(f"  ✓ Committed: chore(release): bump to {dev_version} [skip ci]")

    # Push to main
    print("\nPushing to main...")
    run_command(["git", "push", "origin", "main"])
    print("  ✓ Pushed to main")

    print(f"\n✓ Bumped to development version {dev_version}")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Release automation for Plottini using CalVer (YYYY.MM.MICRO)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Steps for a release (version auto-calculated from date):
  1. python scripts/release.py --prepare               # Create release PR
  2. (merge the PR on GitHub)
  3. git checkout main && git pull
  4. python scripts/release.py --tag                   # Tag the release
  5. python scripts/release.py --post-release         # Bump to dev version

With explicit version (recommended for --tag and --post-release):
  python scripts/release.py --prepare --version 2026.3.0
  python scripts/release.py --tag --version 2026.3.0
  python scripts/release.py --post-release --version 2026.3.0
""",
    )
    parser.add_argument(
        "--prepare",
        action="store_true",
        help="Create release branch, commit version updates, and create PR to main",
    )
    parser.add_argument(
        "--tag",
        action="store_true",
        help="Tag the release on main (run after PR is merged)",
    )
    parser.add_argument(
        "--post-release",
        action="store_true",
        help="Bump to dev version after tagging (commits directly to main)",
    )
    parser.add_argument(
        "--micro",
        action="store_true",
        help="Force micro version increment within same month (only affects --prepare; "
        "use --version for --tag and --post-release)",
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

    # Ensure exactly one action is specified
    actions = [args.prepare, args.tag, args.post_release]
    if sum(actions) == 0:
        print("Error: Must specify one of --prepare, --tag, or --post-release")
        print("\nUse --help for usage information.")
        sys.exit(1)
    if sum(actions) > 1:
        print("Error: Cannot combine --prepare, --tag, and --post-release")
        print("Run each step separately in order.")
        sys.exit(1)

    # Get current version
    current_version = get_current_version()
    print(f"Current version: {current_version}")

    # Calculate target version based on action
    if args.explicit_version:
        version = validate_calver(args.explicit_version)
    elif args.prepare:
        # --prepare: calculate next version (date-based)
        version = calculate_next_version(current_version, force_micro=args.micro)
    else:
        # --tag and --post-release: default to current version in files (stripped of .dev)
        version = strip_dev_suffix(current_version)
        version = validate_calver(version)  # Normalize format

    print(f"Target version: {version}")

    # Dispatch to appropriate action
    if args.prepare:
        prepare_release(version, current_version, args.dry_run)
    elif args.tag:
        tag_release(version, args.dry_run)
    elif args.post_release:
        post_release(version, args.dry_run)


if __name__ == "__main__":
    main()
