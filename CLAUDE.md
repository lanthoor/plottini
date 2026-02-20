# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Plottini is a user-friendly graph builder for creating publication-quality plots from TSV data. It features a Streamlit-based web UI, matplotlib backend, and supports multiple chart types with data transformations. Target users are researchers and scientists who need publication-quality graphs without writing code.

**Tech Stack**: Python 3.10+, Streamlit, matplotlib, numpy, Click

## Development Commands

```bash
# Install dependencies (using uv - recommended)
uv sync --extra dev

# Run the web UI
uv run plottini                    # Default port 8501
uv run plottini --port 8080        # Custom port
uv run plottini --no-open          # Don't open browser

# Headless rendering
uv run plottini render --config graph.toml --output figure.png

# Run tests
uv run pytest                      # All tests
uv run pytest tests/test_parser.py # Single file
uv run pytest tests/test_parser.py::test_parse_simple_tsv  # Single test
uv run pytest --cov=plottini --cov-report=html  # With coverage

# Code quality
uv run ruff check src/ tests/      # Lint
uv run ruff check --fix src/ tests/  # Auto-fix
uv run ruff format src/ tests/     # Format
uv run mypy src/plottini           # Type check
```

## Architecture

```
src/plottini/
├── cli.py              # Click CLI: launches Streamlit or headless render
├── core/
│   ├── parser.py       # TSVParser: reads TSV files into DataFrames
│   ├── dataframe.py    # DataFrame/Column: data container with operations
│   ├── plotter.py      # Plotter: creates matplotlib figures from data
│   ├── exporter.py     # Exporter: saves figures to PNG/SVG/PDF/EPS
│   └── transforms.py   # Mathematical transformations (log, sqrt, trig)
├── config/
│   ├── schema.py       # Dataclasses for TOML configuration
│   ├── loader.py       # TOML config file parser
│   └── defaults.py     # Default values
├── ui/
│   ├── app.py          # Streamlit main app
│   ├── state.py        # Session state management
│   └── components/     # UI tabs (data, series, settings, export, preview)
└── utils/
    └── errors.py       # Custom exceptions: ParseError, ValidationError, ExportError
```

**Data Flow**: TSV files → TSVParser → DataFrame → (transforms/filters) → Plotter → matplotlib Figure → Exporter → output file

## Key Conventions

- **Conventional Commits**: `feat(scope): message`, `fix(scope): message`
- **Scopes**: parser, dataframe, exporter, plotter, ui, config, cli, deps
- **Type hints**: Required for all function signatures (mypy strict mode)
- **Line length**: 100 characters (Ruff configured)
- **Tests**: In `tests/`, fixtures in `tests/fixtures/`, use Arrange-Act-Assert pattern

## Development Workflow

Follow this workflow for all changes:

1. **Start from clean main**
   ```bash
   git checkout main
   git pull origin main
   ```

2. **Create feature branch**
   ```bash
   git checkout -b feat/short-description   # or fix/short-description
   ```

3. **Verify clean state** - all CI checks must pass before making changes
   ```bash
   uv run ruff check src/ tests/
   uv run ruff format --check src/ tests/
   uv run mypy src/plottini
   uv run pytest
   ```

4. **Write test first** - add test case for the new feature/fix
   ```bash
   uv run pytest tests/test_<module>.py -v
   ```
   Verify only the new test fails.

5. **Implement the code** - make the test pass

6. **Run full CI checks again**
   ```bash
   uv run ruff check src/ tests/
   uv run ruff format src/ tests/
   uv run mypy src/plottini
   uv run pytest
   ```
   All checks must pass.

7. **Ask for manual confirmation** before committing

8. **Commit and create/update PR**
   ```bash
   git add <specific files>
   git commit -m "feat(scope): description"
   git push origin feat/short-description
   gh pr create --title "feat(scope): description" --body "..."
   # Or if PR exists: git push (updates existing PR)
   ```

## Critical Rules

1. **Never disable or delete tests** - fix the code, not the tests
2. **No feature creep** - only implement what's in PLAN.md
3. **Safe expression evaluation** - use AST parsing with whitelist, never `eval()`
4. **Update version in 4 places** when releasing: `src/plottini/__init__.py`, `pyproject.toml`, `tests/test_basic.py`, `tests/test_cli.py`

## Versioning

This project uses **Calendar Versioning (CalVer)** with format `YYYY.MM.MICRO`:
- `YYYY` - Full year (e.g., 2026)
- `MM` - Month (01-12, zero-padded)
- `MICRO` - Release number within that month (0, 1, 2...)

**Examples**: `2026.02.0`, `2026.02.1`, `2026.03.0`

**Release commands**:
```bash
python scripts/release.py              # Auto-calculate next version
python scripts/release.py --micro      # Force micro increment within same month
python scripts/release.py --version 2026.03.0  # Set explicit version
python scripts/release.py --dry-run    # Preview changes
```

## Configuration System

TOML config files support:
- `[[files]]` - data sources with path, has_header, comment_chars, delimiter
- `[[series]]` - plot series with x, y, label, color, line_style, marker
- `[plot]` - chart type, title, labels, dimensions, grid/legend options
- `[export]` - format, dpi, transparent background
- `[[derived_columns]]` - computed columns from expressions
- `[[filters]]` - row filters by column value range
