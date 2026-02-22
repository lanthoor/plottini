# Contributing to Plottini

Thank you for your interest in contributing to Plottini! This document provides guidelines and instructions for contributing to the project.

---

## Table of Contents

- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Code Quality](#code-quality)
- [Testing](#testing)
- [Commit Message Format](#commit-message-format)
- [Pull Request Process](#pull-request-process)
- [Project Structure](#project-structure)
- [Project Status](#project-status)

---

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Git
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- A GitHub account

### Getting Started

1. **Fork and Clone**

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/plottini.git
cd plottini
```

2. **Install Dependencies**

```bash
# Using uv (recommended - faster and more reliable)
uv sync --extra dev

# Or using pip with virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

3. **Verify Installation**

```bash
# Run tests to ensure everything works
uv run pytest

# Check that the CLI works
uv run plottini --version
```

---

## Development Workflow

We follow **trunk-based development** on the `main` branch.

### Making Changes

1. **Create a branch** (optional, for larger features)
```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes**
   - Write code following the existing project structure
   - Add tests for new functionality
   - Update documentation if needed

3. **Test your changes**
```bash
# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=plottini --cov-report=term

# Check code quality
uv run ruff check src/ tests/
uv run mypy src/plottini
```

4. **Commit and push**
```bash
git add .
git commit -m "feat: add support for CSV parsing"
git push origin main  # or your branch name
```

> **Note**: We use [Conventional Commits](https://www.conventionalcommits.org/). See [Commit Message Format](#commit-message-format) below.

5. **Create Pull Request**
   - Go to GitHub and create a PR
   - CI will automatically run tests
   - Wait for review

---

## Code Quality

We use several tools to maintain code quality:

### Linting with Ruff

```bash
# Check for issues
uv run ruff check src/ tests/

# Auto-fix issues
uv run ruff check --fix src/ tests/

# Format code
uv run ruff format src/ tests/
```

### Type Checking with Mypy

```bash
# Check types
uv run mypy src/plottini

# Check specific file
uv run mypy src/plottini/core/parser.py
```

### Configuration

All tool configurations are in `pyproject.toml`:
- Ruff: Line length 100, Python 3.10 target
- Mypy: Strict mode enabled
- Pytest: Coverage reporting enabled

---

## Testing

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_parser.py

# Run specific test function
uv run pytest tests/test_parser.py::test_parse_simple_tsv

# Run with coverage
uv run pytest --cov=plottini --cov-report=html
# Open htmlcov/index.html to view coverage report
```

### Writing Tests

- Place tests in `tests/` directory
- Name test files `test_*.py`
- Name test functions `test_*`
- Use fixtures in `tests/fixtures/` for sample data

Example test:

```python
def test_parser_validates_numeric_data():
    """Test that parser rejects non-numeric data."""
    parser = TSVParser(ParserConfig(has_header=False))
    
    with pytest.raises(ParseError) as exc_info:
        parser.parse("tests/fixtures/malformed/non_numeric.tsv")
    
    assert "invalid numeric value" in str(exc_info.value).lower()
```

---

## Commit Message Format

We use [Conventional Commits](https://www.conventionalcommits.org/) for all commit messages. This enables automatic changelog generation and semantic versioning.

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

| Type | Description | Version Bump |
|------|-------------|--------------|
| `feat` | New feature | Minor |
| `fix` | Bug fix | Patch |
| `docs` | Documentation only | None |
| `style` | Formatting, no logic change | None |
| `refactor` | Code refactoring | None |
| `perf` | Performance improvement | Patch |
| `test` | Adding/updating tests | None |
| `chore` | Build, CI, tooling | None |

### Scope (Optional)

The scope provides additional context about what part of the codebase is affected:

- `parser` - TSV parser module
- `dataframe` - DataFrame module
- `exporter` - Export functionality
- `plotter` - Plotting functionality
- `ui` - User interface
- `config` - Configuration system
- `cli` - Command-line interface
- `deps` - Dependencies

### Subject

- Use imperative mood ("add" not "added")
- Don't capitalize first letter
- No period at the end
- Max 50 characters

### Examples

```bash
# Feature
git commit -m "feat(parser): add support for CSV delimiter"

# Bug fix
git commit -m "fix(exporter): correct DPI handling for PNG export"

# Documentation
git commit -m "docs: update installation instructions"

# Breaking change (add ! after type)
git commit -m "feat(parser)!: change default delimiter to comma"

# With body for more context
git commit -m "fix(dataframe): handle empty column names

Previously, empty column names caused a KeyError.
Now they are automatically named 'Column N'.

Fixes #42"
```

### Breaking Changes

For breaking changes:
1. Add `!` after type/scope: `feat(parser)!: ...`
2. Or add `BREAKING CHANGE:` in the footer

### Pull Request Titles

**PR titles must also follow conventional commit format.** When PRs are squash-merged, the PR title becomes the commit message in `main`.

Examples:
- `feat(parser): add CSV delimiter support`
- `fix(exporter): correct PNG DPI handling`
- `docs: update installation guide`

---

## Pull Request Process

1. **Ensure all tests pass**
   - CI runs automatically on PRs
   - Fix any failing tests before requesting review

2. **Update documentation**
   - Update README.md if user-facing changes
   - Add docstrings to new functions/classes

3. **PR Description**
   - Describe what changes were made and why
   - Reference any related issues
   - Include screenshots for UI changes

4. **Code Review**
   - Address reviewer feedback
   - Keep commits focused and atomic
   - Squash commits if needed before merge

5. **Merge**
   - PRs are merged to `main` via squash merge
   - Delete branch after merge

---

## Project Structure

```
plottini/
├── src/plottini/          # Main package code
│   ├── core/              # Core functionality (parsing, plotting, export)
│   ├── config/            # Configuration management
│   ├── ui/                # Streamlit user interface
│   └── utils/             # Helper utilities
├── tests/                 # Test suite
│   ├── fixtures/          # Test data files
│   └── test_*.py          # Test modules
├── .github/workflows/     # CI/CD pipelines
├── CONTRIBUTING.md        # This file
└── README.md              # User documentation
```

---

## Project Status

### Status: All Phases Complete

The project is production-ready with all planned features implemented:
- TSV parsing with multi-block support
- 13 chart types
- Data transformations and derived columns
- Multi-file support with alignment
- Streamlit web interface with PyWebView desktop mode
- Headless render mode for batch processing
- TOML configuration system

---

## Code Style Guidelines

### Python Style

- Follow PEP 8 (enforced by Ruff)
- Line length: 100 characters max
- Use type hints for all functions
- Write descriptive docstrings

Example:

```python
def parse_tsv_file(
    file_path: Path,
    has_header: bool = True,
    comment_chars: list[str] | None = None
) -> DataFrame:
    """Parse a TSV file into a DataFrame.
    
    Args:
        file_path: Path to the TSV file
        has_header: Whether the first row is a header
        comment_chars: Characters that start comment lines
        
    Returns:
        DataFrame containing the parsed data
        
    Raises:
        ParseError: If data is malformed or non-numeric
    """
    ...
```

### Naming Conventions

- Classes: `PascalCase`
- Functions/methods: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private members: `_leading_underscore`

### Import Organization

```python
# Standard library
import os
from pathlib import Path

# Third-party
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st

# Local
from plottini.core.parser import TSVParser
from plottini.utils.errors import ParseError
```

---

## Getting Help

- **Questions**: Open a [GitHub Discussion](https://github.com/lanthoor/plottini/discussions)
- **Bugs**: Open a [GitHub Issue](https://github.com/lanthoor/plottini/issues)
- **Contact**: Lallu Anthoor (dev@spendly.co.in)

---

## License

By contributing to Plottini, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Plottini! 🎉
