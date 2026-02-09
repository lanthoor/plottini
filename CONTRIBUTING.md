# Contributing to Plottini

Thank you for your interest in contributing to Plottini! This document provides guidelines and instructions for contributing to the project.

---

## Table of Contents

- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Code Quality](#code-quality)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Project Structure](#project-structure)
- [Implementation Plan](#implementation-plan)

---

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Git
- A GitHub account

### Getting Started

1. **Fork and Clone**

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/plottini.git
cd plottini
```

2. **Set Up Virtual Environment**

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Or use uv for faster installation
uv venv
source .venv/bin/activate
```

3. **Install Dependencies**

```bash
# Install in development mode with all dev dependencies
pip install -e ".[dev]"

# Or with uv
uv pip install -e ".[dev]"
```

4. **Verify Installation**

```bash
# Run tests to ensure everything works
pytest

# Check that the CLI works
plottini --version
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
   - Write code following the project structure (see [PLAN.md](PLAN.md))
   - Add tests for new functionality
   - Update documentation if needed

3. **Test your changes**
```bash
# Run tests
pytest

# Run with coverage
pytest --cov=plottini --cov-report=term

# Check code quality
ruff check src/ tests/
mypy src/plottini
```

4. **Commit and push**
```bash
git add .
git commit -m "Brief description of changes"
git push origin main  # or your branch name
```

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
ruff check src/ tests/

# Auto-fix issues
ruff check --fix src/ tests/

# Format code
ruff format src/ tests/
```

### Type Checking with Mypy

```bash
# Check types
mypy src/plottini

# Check specific file
mypy src/plottini/core/parser.py
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
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_parser.py

# Run specific test function
pytest tests/test_parser.py::test_parse_simple_tsv

# Run with coverage
pytest --cov=plottini --cov-report=html
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

## Pull Request Process

1. **Ensure all tests pass**
   - CI runs automatically on PRs
   - Fix any failing tests before requesting review

2. **Update documentation**
   - Update README.md if user-facing changes
   - Update PLAN.md if architecture changes
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
│   ├── ui/                # NiceGUI user interface
│   └── utils/             # Helper utilities
├── tests/                 # Test suite
│   ├── fixtures/          # Test data files
│   └── test_*.py          # Test modules
├── .github/workflows/     # CI/CD pipelines
├── PLAN.md                # Detailed implementation plan
├── CONTRIBUTING.md        # This file
└── README.md              # User documentation
```

---

## Implementation Plan

The project is being built in phases. See [PLAN.md](PLAN.md) for the complete implementation plan.

### Current Phase: Phase 1 - Core Foundation

Priority tasks:
1. **TSV Parser** (`src/plottini/core/parser.py`)
   - Read TSV files with validation
   - Handle headers and comments
   - Detailed error messages

2. **DataFrame** (`src/plottini/core/dataframe.py`)
   - Data container with column operations
   - Support for derived columns
   - Data filtering

3. **Plotter** (`src/plottini/core/plotter.py`)
   - Matplotlib figure generation
   - Start with Line, Bar, Pie charts

4. **Exporter** (`src/plottini/core/exporter.py`)
   - Export to PNG/SVG/PDF/EPS

### How to Contribute to Current Phase

1. Pick a module from Phase 1
2. Check [PLAN.md](PLAN.md) for detailed specifications
3. Implement following the design
4. Write comprehensive tests
5. Submit PR

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
from nicegui import ui

# Local
from plottini.core.parser import TSVParser
from plottini.utils.errors import ParseError
```

---

## Getting Help

- **Questions**: Open a [GitHub Discussion](https://github.com/lanthoor/plottini/discussions)
- **Bugs**: Open a [GitHub Issue](https://github.com/lanthoor/plottini/issues)
- **Design Questions**: Refer to [PLAN.md](PLAN.md)
- **Contact**: Lallu Anthoor (dev@spendly.co.in)

---

## License

By contributing to Plottini, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Plottini! 🎉
