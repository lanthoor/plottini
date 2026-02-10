# Instructions for AI Agents

This document provides guidance for AI agents (like Claude, GPT, etc.) working on the Plottini project.

---

## Project Overview

**Plottini** is a user-friendly graph builder that allows non-technical users to create publication-quality plots from TSV data files. It features:

- A NiceGUI-based web UI for interactive graph creation
- Matplotlib backend for rendering
- Support for multiple chart types and data transformations
- Export to PNG, SVG, PDF, and EPS formats
- Configuration file support (TOML) for reproducible workflows

**Target Users**: Researchers, scientists, and data analysts who need publication-quality graphs without writing code.

**Tech Stack**: Python 3.10+, NiceGUI, matplotlib, numpy, Click

---

## Key Files and Their Purpose

| File | Purpose |
|------|---------|
| `PLAN.md` | Complete implementation plan with detailed specifications |
| `CONTRIBUTING.md` | Development setup, workflow, and contribution guidelines |
| `README.md` | User-facing documentation and quick start guide |
| `pyproject.toml` | Package configuration, dependencies, and tool settings |
| `src/plottini/` | Main package source code |
| `tests/` | Test suite with fixtures |

---

## Development Principles

### 1. Trunk-Based Development
- Work directly on `main` branch or short-lived feature branches
- CI runs on every push to `main`
- All tests must pass before merging

### 2. Test-Driven Development
- Write tests BEFORE implementing features
- Aim for high test coverage (>80%)
- Tests must be comprehensive and meaningful

### 3. Type Safety
- Use type hints for all function signatures
- Run `mypy` to catch type errors early
- Enable strict mode in mypy configuration

### 4. Code Quality
- Follow PEP 8 (enforced by Ruff)
- Line length: 100 characters max
- Write clear, descriptive docstrings
- Keep functions focused and single-purpose

### 5. User-Centric Design
- Prioritize ease of use over technical complexity
- Provide clear, actionable error messages
- Default to sensible values (publication-ready styling)

---

## Critical Rules

### NEVER Break These Rules

**1. Testing is Sacred**
- ❌ **NEVER delete or disable existing tests**
- ❌ **NEVER comment out tests to make them pass**
- ❌ **NEVER reduce test coverage**
- ✅ **ALWAYS start with all tests passing**
- ✅ **ALWAYS end with same or more tests passing**
- ✅ **ALWAYS maintain or improve coverage**

**2. Clean Development Cycles**
- Each cycle MUST start: All tests passing ✅
- Each cycle MUST end: All tests passing ✅ + coverage ≥ previous
- If tests fail after changes, FIX the code, not the tests

**3. No Feature Creep**
- ❌ **NEVER add features not in PLAN.md**
- ❌ **NEVER implement "nice to have" features**
- ❌ **NEVER add extra functionality "while you're at it"**
- ✅ **ONLY implement what's specified in current phase/task**
- ✅ If you think something is missing, note it but don't implement

**4. No Unnecessary Documentation**
- ❌ **NEVER create unsolicited documentation files**
- ❌ **NEVER add verbose inline comments explaining obvious code**
- ❌ **NEVER write tutorial-style comments**
- ✅ **ONLY add docstrings for public APIs**
- ✅ **ONLY add comments for non-obvious logic**
- ✅ Code should be self-documenting through clear naming

**5. No Premature Optimization**
- ❌ **NEVER optimize before measuring**
- ❌ **NEVER add complexity for hypothetical performance**
- ✅ **ONLY optimize if performance is actually a problem**

**6. Stick to the Specification**
- The specification in PLAN.md is the source of truth
- If something is unclear, ask - don't assume
- If you think the spec is wrong, note it but follow it anyway

---

## Development Workflow

When implementing a feature or fixing a bug, follow this workflow:

### 0. Verify Clean State (REQUIRED)

**Before starting ANY work, ensure:**

```bash
# All tests must pass
pytest -v

# Check current coverage
pytest --cov=plottini --cov-report=term

# Note the coverage percentage - you must maintain or improve it
```

**If any tests fail:**
- ❌ DO NOT proceed
- ✅ Fix the failing tests first
- ✅ Or revert to last known good state

**Clean Slate Principle:**
- Every development cycle starts with: ✅ All tests passing
- Every development cycle ends with: ✅ All tests passing + coverage ≥ previous

### 1. Create a Branch

```bash
# For new features
git checkout -b feature/short-description

# For bug fixes
git checkout -b fix/short-description
```

### 2. Update Version Number

Update version in the following files:
- `src/plottini/__init__.py` - Main version string
- `pyproject.toml` - Package version
- `tests/test_basic.py` - Version assertion test
- `tests/test_cli.py` - CLI version output test

Version guidelines:
- **Minor version** (0.X.0): New features, new modules, significant additions
- **Patch version** (0.0.X): Bug fixes, small improvements, documentation

Example:
```python
__version__ = "0.2.0"  # For new feature
__version__ = "0.1.1"  # For bug fix
```

### 3. Implement Changes

1. **Read the specification** in `PLAN.md` for the module/feature
2. **Create test file first** (`tests/test_<module>.py`)
3. **Write failing tests** for the functionality
4. **Implement the feature** to make tests pass
5. **Add type hints** to all functions
6. **Write comprehensive docstrings**

### 4. Run Quality Checks

```bash
# Run tests
pytest -v

# Check coverage (aim for >80%)
pytest --cov=plottini --cov-report=term

# Run linter
ruff check src/ tests/

# Run type checker
mypy src/plottini

# Format code
ruff format src/ tests/
```

### 5. Commit Changes

We use [Conventional Commits](https://www.conventionalcommits.org/) for all commit messages.

```bash
# Add files
git add .

# Commit with conventional commit format
git commit -m "feat(parser): implement TSV parser with validation"
# or
git commit -m "fix(parser): handle empty files gracefully"
```

**Commit message format:** `<type>(<scope>): <subject>`

| Type | Description | Example |
|------|-------------|---------|
| `feat` | New feature | `feat(exporter): add PDF export support` |
| `fix` | Bug fix | `fix(parser): handle scientific notation` |
| `docs` | Documentation | `docs: update README installation` |
| `style` | Formatting | `style: fix indentation in parser.py` |
| `refactor` | Code restructure | `refactor(dataframe): simplify column access` |
| `perf` | Performance | `perf(parser): optimize large file parsing` |
| `test` | Tests | `test(exporter): add PNG export tests` |
| `chore` | Build/tooling | `chore: update CI workflow` |

**Scopes:** `parser`, `dataframe`, `exporter`, `plotter`, `ui`, `config`, `cli`, `deps`

**Rules:**
- Use imperative mood: "add" not "added"
- No capitalization at start
- No period at end
- Max 50 characters for subject line
- Add `!` after type for breaking changes: `feat(parser)!: change API`

### 6. Push and Create PR

```bash
# Push to GitHub
git push origin feature/your-branch-name

# Create PR via GitHub UI or gh CLI
# NOTE: PR title must follow conventional commit format
gh pr create --title "feat(parser): implement TSV parser with validation" --body "Implements Phase 1: TSV parser with validation and error handling"
```

**PR Title Format:** PR titles must follow conventional commit format (`<type>(<scope>): <subject>`). When PRs are squash-merged, the title becomes the commit message in `main`.

### 7. After PR is Merged

```bash
# Switch back to main
git checkout main

# Pull latest changes
git pull origin main

# Delete feature branch
git branch -d feature/your-branch-name
```

---

## Implementation Guidelines

### Before You Start

1. Check `PLAN.md` for the module specification
2. Review existing tests to understand expected behavior
3. Look at similar code in the project for consistency

### Code Template

```python
"""Module description.

This module provides...
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


@dataclass
class ConfigClass:
    """Configuration for XYZ.
    
    Attributes:
        param1: Description of param1
        param2: Description of param2
    """
    param1: str
    param2: int = 10


class MainClass:
    """Main class description.
    
    This class handles...
    """
    
    def __init__(self, config: ConfigClass) -> None:
        """Initialize the class.
        
        Args:
            config: Configuration object
        """
        self.config = config
    
    def main_method(self, input_data: np.ndarray) -> dict[str, Any]:
        """Process input data.
        
        Args:
            input_data: Array of numeric values
            
        Returns:
            Dictionary containing processed results
            
        Raises:
            ValueError: If input_data is empty
        """
        if len(input_data) == 0:
            raise ValueError("input_data cannot be empty")
        
        # Implementation here
        return {"result": "value"}
```

### Error Handling

Provide detailed, user-friendly error messages:

```python
raise ParseError(
    file_path=Path("data.tsv"),
    line_number=42,
    column=3,
    message="Expected numeric value, got 'N/A'",
    raw_value="N/A"
)
```

Display format:
```
ParseError: Invalid numeric value in file 'data.tsv'
  Line 42, Column 3: expected number, got 'N/A'
  Context: "1.5    2.3    N/A    4.1"
                          ^^^
```

### Testing Guidelines

Structure tests using Arrange-Act-Assert:

```python
def test_parser_handles_headers():
    """Test that parser correctly identifies header rows."""
    # Arrange: Set up test data
    config = ParserConfig(has_header=True)
    parser = TSVParser(config)
    
    # Act: Execute the code being tested
    result = parser.parse("tests/fixtures/with_headers.tsv")
    
    # Assert: Verify the results
    assert result.columns[0].name == "Time"
    assert result.columns[1].name == "Value"
```

Place test fixtures in `tests/fixtures/`:
- `simple.tsv` - Basic valid data
- `with_headers.tsv` - Data with header row
- `malformed/` - Invalid data for error testing
- `multifile/` - Multiple files for alignment testing

---

## Common Patterns

### Configuration with Dataclasses

```python
@dataclass
class PlotConfig:
    """Configuration for plot appearance."""
    title: str = ""
    x_label: str = ""
    y_label: str = ""
    figure_width: float = 10.0
    figure_height: float = 6.0
    show_grid: bool = True
```

### File Path Handling

```python
from pathlib import Path

def load_file(file_path: Path | str) -> DataFrame:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    # ...
```

### Numpy Type Hints

```python
import numpy as np
from numpy.typing import NDArray

def process_data(data: NDArray[np.float64]) -> NDArray[np.float64]:
    return np.log10(data)
```

---

## Security Considerations

### Safe Expression Evaluation

When implementing derived columns:

- **Use AST parsing** with whitelist approach
- **Never use `eval()` or `exec()`**
- Allow only math operations and numpy functions
- Validate expressions before evaluation

```python
import ast

ALLOWED_OPERATIONS = {
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow,
    ast.USub, ast.UAdd
}

ALLOWED_FUNCTIONS = {
    'log', 'log10', 'sqrt', 'abs', 'sin', 'cos'
}

def validate_expression(expr: str) -> bool:
    """Check if expression is safe to evaluate."""
    tree = ast.parse(expr, mode='eval')
    # Validate all nodes in the tree
    # ...
```

---

## Performance Considerations

- Use numpy for numerical operations (vectorized)
- Avoid Python loops over large arrays
- Cache parsed data to avoid re-reading files
- Debounce UI updates (200ms for live preview)

---

## Useful Commands

```bash
# Install dependencies
uv sync --dev

# Run tests
uv run pytest -v
uv run pytest --cov=plottini --cov-report=html

# Check code quality
uv run ruff check src/ tests/
uv run mypy src/plottini

# Format code
uv run ruff format src/ tests/

# Run CLI
uv run plottini --help
uv run plottini version

# Build package
uv build

# Check package
uv run twine check dist/*
```

---

## Questions to Ask Before Implementation

1. Does this match the specification in PLAN.md?
2. Are there tests for this functionality?
3. Is the API intuitive for users?
4. Are error cases handled gracefully?
5. Is the code type-safe?
6. Is the implementation performant?
7. Is security considered (especially for expressions)?

---

## Project Values

When in doubt, prioritize:

1. **User experience** over technical elegance
2. **Clarity** over cleverness
3. **Correctness** over speed (then optimize if needed)
4. **Simplicity** over flexibility
5. **Publication quality** over quick hacks

---

**Remember**: Plottini aims to make publication-quality graphs accessible to non-technical users. Every decision should serve that goal.
