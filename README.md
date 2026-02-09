# Plottini

**A user-friendly graph builder for creating publication-quality plots from TSV data**

[![PyPI version](https://badge.fury.io/py/plottini.svg)](https://badge.fury.io/py/plottini)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Overview

Plottini is designed for researchers, scientists, and anyone who needs to create high-quality graphs from tabular data without writing code. With an intuitive web-based UI powered by NiceGUI and matplotlib as the rendering backend, Plottini makes it easy to:

- Load TSV data files with automatic validation
- Create various chart types (line, bar, scatter, histogram, and more)
- Apply mathematical transformations to your data
- Overlay multiple datasets on the same plot
- Export publication-ready figures in PNG, SVG, PDF, or EPS formats

---

## Features

### Core Capabilities
- **Multiple data sources**: Load one or more TSV files with configurable headers and comment delimiters
- **Rich chart types**: Line, Bar, Pie, Scatter, Histogram, Polar, Box, Violin, Area, and more
- **Data transformations**: Apply preset functions (log, sqrt, power, trig functions) to your data
- **Derived columns**: Create computed columns using safe mathematical expressions
- **Data filtering**: Filter rows by value ranges before plotting
- **Multi-file alignment**: Align multiple datasets by a common column
- **Secondary Y-axis**: Display two different scales on the same plot
- **Live preview**: See your changes in real-time as you configure your plot
- **Publication quality**: Colorblind-safe palettes and professional styling by default

### Export Options
- **Formats**: PNG, SVG, PDF, EPS
- **Configurable DPI**: High-resolution output for publications
- **Vector formats**: Scalable graphics for presentations and papers

### Advanced Features
- **Configuration files**: Expert users can use TOML files for reproducible workflows
- **Headless rendering**: Batch processing without the UI
- **Detailed error messages**: Clear, actionable feedback for data issues

---

## Installation

### From PyPI

```bash
pip install plottini
```

### From Source

```bash
git clone https://github.com/lanthoor/plottini.git
cd plottini
pip install -e .
```

### Development Installation

```bash
git clone https://github.com/lanthoor/plottini.git
cd plottini
pip install -e ".[dev]"
```

---

## Quick Start

### Start the UI

```bash
plottini
```

This will start the web interface on `http://localhost:8050` and automatically open it in your browser.

### Command-Line Options

```bash
# Start on a specific port
plottini --port 8080

# Don't open browser automatically
plottini --no-open

# Load a configuration file
plottini --config my-graph.toml
```

### Expert Mode: Headless Rendering

For automation and batch processing:

```bash
plottini render --config my-graph.toml --output figure.png
```

---

## Usage

### 1. Load Your Data

- Click **"+ Add Files"** to load one or more TSV files
- Toggle **"Has header row"** if your files have column names
- Set comment characters (default: `#`)

### 2. Preview Your Data

- View a paginated table of your parsed data
- Verify that all values were correctly interpreted as numbers

### 3. Configure Series

- Select which columns to plot on X and Y axes
- Choose colors, line styles, and markers
- Apply transformations (log scale, square root, etc.)
- Use secondary Y-axis for different scales

### 4. Customize Plot Settings

- Select chart type
- Add title and axis labels
- Configure grid, legend, and figure size
- Adjust font sizes for publication

### 5. Advanced Options

- **Derived Columns**: Create new columns from expressions like `col1 / col2`
- **Filters**: Exclude data outside specified ranges
- **Multi-file Alignment**: Merge datasets by a common column
- **Layout**: Overlay series or create separate subplots

### 6. Export

- Choose format: PNG, SVG, PDF, or EPS
- Set DPI for raster formats
- Click **"Export"** to save your figure

---

## Configuration File Format

For reproducible workflows, you can create a TOML configuration file:

```toml
# my-graph.toml

[[files]]
path = "data/experiment1.tsv"
has_header = true
comment_chars = ["#"]

[[series]]
x = "time"
y = "velocity"
label = "Experiment 1"
color = "#0072B2"
transform_y = "log10"

[plot]
type = "line"
title = "Velocity over Time"
x_label = "Time (s)"
y_label = "Velocity (m/s)"
figure_width = 10.0
figure_height = 6.0

[export]
format = "png"
dpi = 300
```

Load it with:

```bash
plottini --config my-graph.toml
```

Or render directly:

```bash
plottini render --config my-graph.toml --output velocity.png
```

See the [configuration documentation](AGENTS.md#3-configuration-system) for full details.

---

## Supported Chart Types

| Category | Chart Types |
|----------|-------------|
| **Basic** | Line, Scatter, Bar (vertical/horizontal) |
| **Statistical** | Histogram, Box plot, Violin plot |
| **Area** | Area, Stacked area |
| **Specialized** | Stem, Step, Error bar, Pie, Polar |

---

## Mathematical Transformations

Available preset transformations:

- **Logarithmic**: log, log10, log2
- **Power**: square, cube, sqrt, cbrt
- **Trigonometric**: sin, cos, tan, arcsin, arccos, arctan
- **Other**: abs, inverse (1/x), exp, negate

**Derived Columns**: Create custom expressions like:
- `col1 / col2`
- `sqrt(col1**2 + col2**2)`
- `0.5 * mass * velocity**2`

---

## Requirements

- Python 3.10 or higher
- matplotlib ≥ 3.7
- numpy ≥ 1.24
- nicegui ≥ 1.4
- click ≥ 8.1

---

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/lanthoor/plottini.git
cd plottini

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
```

### Code Quality

```bash
# Linting
ruff check .

# Type checking
mypy src/plottini

# Format check
ruff format --check .
```

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run the test suite and linters
5. Submit a pull request

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Roadmap

See [AGENTS.md](AGENTS.md) for the detailed implementation plan.

### Current Status: Project Setup Complete ✅

- [x] Project structure
- [x] Package configuration
- [x] CLI framework
- [ ] Core parsing (Phase 1)
- [ ] Basic plotting (Phase 2a)
- [ ] UI implementation (Phase 4)
- [ ] Full feature set (Phases 2b-3)

---

## Support

- **Issues**: [GitHub Issues](https://github.com/lanthoor/plottini/issues)
- **Documentation**: See [AGENTS.md](AGENTS.md) for technical details
- **Author**: Lallu Anthoor (dev@spendly.co.in)

---

## Acknowledgments

Built with:
- [matplotlib](https://matplotlib.org/) - The plotting backend
- [NiceGUI](https://nicegui.io/) - The web UI framework
- [Click](https://click.palletsprojects.com/) - CLI framework
- [NumPy](https://numpy.org/) - Numerical computing

---

**Plottini** - Making publication-quality graphs accessible to everyone.
