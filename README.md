# Plottini

**A user-friendly graph builder for creating publication-quality plots from TSV data**

[![PyPI version](https://badge.fury.io/py/plottini.svg)](https://badge.fury.io/py/plottini)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Overview

Plottini is designed for researchers, scientists, and anyone who needs to create high-quality graphs from tabular data without writing code. With an intuitive UI powered by Streamlit (available as a desktop app via PyWebView or in the browser) and matplotlib as the rendering backend, Plottini makes it easy to:

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

---

## Quick Start

### Start the UI

```bash
plottini
```

This will start the desktop app (using PyWebView) with the Streamlit-based interface.

### Command-Line Options

```bash
# Start on a specific port
plottini --port 8080

# Show version
plottini version
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

---

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:

- Development setup instructions
- Code style guidelines
- Testing requirements
- Pull request process

---

## License

[MIT License](LICENSE)

---

## Support

- **Issues**: [GitHub Issues](https://github.com/lanthoor/plottini/issues)
- **Author**: Lallu Anthoor (dev@spendly.co.in)

---

## Acknowledgments

Built with:
- [matplotlib](https://matplotlib.org/) - The plotting backend
- [Streamlit](https://streamlit.io/) - The web UI framework
- [PyWebView](https://pywebview.flowrl.com/) - Desktop app wrapper
- [Click](https://click.palletsprojects.com/) - CLI framework
- [NumPy](https://numpy.org/) - Numerical computing

---

**Plottini** - Making publication-quality graphs accessible to everyone.
