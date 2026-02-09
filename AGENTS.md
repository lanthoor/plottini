# Plottini - Implementation Plan

## Project Overview

**Plottini** is a user-friendly, UI-driven graph builder that allows non-technical users to create publication-quality graphs from TSV data files using matplotlib as the rendering backend.

| Attribute | Value |
|-----------|-------|
| Package name | `plottini` |
| License | MIT |
| Config format | TOML |
| Python version | >=3.10 |
| UI framework | NiceGUI |
| Backend | matplotlib |

---

## 1. Project Structure

```
plottini/
├── src/plottini/
│   ├── __init__.py              # Package init, version info
│   ├── __main__.py              # Entry point: `python -m plottini`
│   ├── cli.py                   # CLI entry point for `plottini` command
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── parser.py            # TSV parsing with validation
│   │   ├── dataframe.py         # Data container & operations
│   │   ├── transforms.py        # Mathematical transformations
│   │   ├── plotter.py           # Matplotlib graph generation
│   │   └── exporter.py          # Export to PNG/SVG/PDF/EPS
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── schema.py            # Configuration dataclasses
│   │   ├── loader.py            # TOML config file handling
│   │   └── defaults.py          # Default values and presets
│   │
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── app.py               # Main NiceGUI application
│   │   ├── state.py             # UI state management
│   │   └── components/
│   │       ├── __init__.py
│   │       ├── file_selector.py     # File upload/selection
│   │       ├── data_preview.py      # Data table preview
│   │       ├── column_mapper.py     # Column to axis mapping
│   │       ├── transform_panel.py   # Transformations UI
│   │       ├── chart_config.py      # Chart type & styling
│   │       ├── export_panel.py      # Export options
│   │       └── plot_preview.py      # Live matplotlib preview
│   │
│   └── utils/
│       ├── __init__.py
│       ├── errors.py            # Custom exceptions
│       └── validators.py        # Input validation helpers
│
├── tests/
│   ├── __init__.py
│   ├── test_parser.py
│   ├── test_dataframe.py
│   ├── test_transforms.py
│   ├── test_plotter.py
│   ├── test_config.py
│   └── fixtures/                # Sample TSV files for testing
│       ├── simple.tsv
│       ├── with_headers.tsv
│       ├── multifile/
│       └── malformed/
│
├── pyproject.toml               # Package metadata, dependencies
├── README.md
├── LICENSE
└── .gitignore
```

---

## 2. Core Modules Design

### 2.1 Parser Module (`core/parser.py`)

**Responsibilities:**
- Read TSV files with configurable comment delimiters
- Validate all data is numeric
- Handle header row detection
- Produce detailed error messages with file name, line number, column

**Key Classes/Functions:**

```python
@dataclass
class ParserConfig:
    has_header: bool = True
    comment_chars: list[str] = field(default_factory=lambda: ["#"])
    delimiter: str = "\t"
    encoding: str = "utf-8"

@dataclass  
class ParseError:
    file_path: Path
    line_number: int
    column: int | None
    message: str
    raw_value: str | None

class TSVParser:
    def __init__(self, config: ParserConfig): ...
    def parse(self, file_path: Path) -> ParsedData: ...
    def parse_multiple(self, file_paths: list[Path]) -> list[ParsedData]: ...
```

**Error Handling Example:**
```
ParseError: Invalid numeric value in file 'data.tsv'
  Line 42, Column 3: expected number, got 'N/A'
  Context: "1.5    2.3    N/A    4.1"
                          ^^^
```

---

### 2.2 DataFrame Module (`core/dataframe.py`)

**Responsibilities:**
- Store parsed data with column metadata
- Support derived column creation
- Handle multi-file alignment by common column
- Provide data filtering capabilities

**Key Classes:**

```python
@dataclass
class Column:
    name: str                    # Header name or "Column 1", "Column 2", etc.
    index: int                   # Original column index
    data: np.ndarray             # Numeric values
    is_derived: bool = False     # True if computed from other columns

@dataclass
class DataFrame:
    columns: dict[str, Column]
    source_file: Path
    row_count: int
    
    def add_derived_column(self, name: str, expression: str) -> None: ...
    def filter_rows(self, column: str, min_val: float | None, max_val: float | None) -> DataFrame: ...
    def get_column_names(self) -> list[str]: ...

def align_dataframes(
    dataframes: list[DataFrame], 
    align_column: str
) -> AlignedDataFrames: ...
```

**Notes:**
- If files don't have headers, columns are named "Column 1", "Column 2", etc. (starting from 1)
- Derived columns use safe math expression evaluation (no arbitrary code execution)
- Multi-file alignment matches rows by a common column value across files

---

### 2.3 Transforms Module (`core/transforms.py`)

**Responsibilities:**
- Apply mathematical transformations to data
- Provide preset transformation functions
- Parse and validate derived column expressions (safe evaluation only)

**Available Presets:**

| Category | Transforms |
|----------|------------|
| **Logarithmic** | log (natural), log10, log2 |
| **Power** | square (x²), cube (x³), sqrt, cbrt |
| **Trigonometric** | sin, cos, tan, arcsin, arccos, arctan |
| **Other** | abs, inverse (1/x), exp, negate (-x) |

**Key Classes:**

```python
class Transform(Enum):
    LOG = "log"
    LOG10 = "log10"
    LOG2 = "log2"
    SQUARE = "square"
    SQRT = "sqrt"
    CUBE = "cube"
    CBRT = "cbrt"
    SIN = "sin"
    COS = "cos"
    TAN = "tan"
    ARCSIN = "arcsin"
    ARCCOS = "arccos"
    ARCTAN = "arctan"
    ABS = "abs"
    INVERSE = "inverse"
    EXP = "exp"
    NEGATE = "negate"

TRANSFORM_FUNCTIONS: dict[Transform, Callable[[np.ndarray], np.ndarray]]

def apply_transform(data: np.ndarray, transform: Transform) -> np.ndarray: ...

# For derived columns - safe expression evaluation using AST
def evaluate_expression(
    expression: str, 
    columns: dict[str, np.ndarray]
) -> np.ndarray: ...
```

**Derived Column Expression Syntax:**
- Reference columns by name: `col1`, `col2` or `"Column 1"`, `"Column 2"`
- Supported operators: `+`, `-`, `*`, `/`, `**`, `%`
- Supported functions: `log`, `log10`, `sqrt`, `abs`, `sin`, `cos`, etc.
- Example: `col1 / col2`, `sqrt(col1**2 + col2**2)`
- **Security**: Uses AST parsing with whitelist approach - only math operations allowed

---

### 2.4 Plotter Module (`core/plotter.py`)

**Responsibilities:**
- Generate matplotlib figures from data and configuration
- Support all matplotlib chart types
- Handle single plot vs subplots layout
- Manage dual Y-axis scenarios

**Supported Chart Types (Implementation Order):**

| Phase | Types |
|-------|-------|
| **Phase 2a** | Line, Bar (vertical), Pie |
| **Phase 2b** | Polar/Radial, Histogram, Scatter |
| **Phase 2c** | Box, Violin, Area, Bar (horizontal), Stem, Step, Error bar |

**Key Classes:**

```python
class ChartType(Enum):
    LINE = "line"
    SCATTER = "scatter"
    BAR = "bar"
    BAR_HORIZONTAL = "barh"
    HISTOGRAM = "histogram"
    BOX = "box"
    VIOLIN = "violin"
    AREA = "area"
    STEM = "stem"
    STEP = "step"
    ERRORBAR = "errorbar"
    PIE = "pie"
    POLAR = "polar"

@dataclass
class SeriesConfig:
    x_column: str
    y_column: str
    label: str | None = None
    color: str | None = None          # Auto-assigned if None
    line_style: str = "-"             # For line plots
    marker: str | None = None
    transform_x: Transform | None = None
    transform_y: Transform | None = None
    use_secondary_y: bool = False
    source_file_index: int = 0        # Which file this series comes from

@dataclass
class PlotConfig:
    chart_type: ChartType
    title: str = ""
    x_label: str = ""
    y_label: str = ""
    y2_label: str = ""                # Secondary Y-axis label
    
    # Axis ranges (None = auto)
    x_min: float | None = None
    x_max: float | None = None
    y_min: float | None = None
    y_max: float | None = None
    
    # Styling
    figure_width: float = 10.0
    figure_height: float = 6.0
    show_grid: bool = True
    show_legend: bool = True
    legend_position: str = "best"
    
    # Font sizes
    title_fontsize: int = 14
    label_fontsize: int = 12
    tick_fontsize: int = 10
    legend_fontsize: int = 10

@dataclass
class MultiPlotConfig:
    layout: Literal["overlay", "subplots"]
    subplot_rows: int = 1             # For subplots layout
    subplot_cols: int = 1
    share_x: bool = False
    share_y: bool = False

class Plotter:
    def __init__(self, plot_config: PlotConfig): ...
    
    def create_figure(
        self, 
        data: DataFrame | list[DataFrame],
        series: list[SeriesConfig],
        multi_config: MultiPlotConfig | None = None
    ) -> matplotlib.figure.Figure: ...
    
    def update_figure(self, **kwargs) -> matplotlib.figure.Figure: ...
```

**Publication-Quality Defaults:**

```python
# Colorblind-safe color palette
PUBLICATION_COLORS = [
    "#0072B2",  # Blue
    "#D55E00",  # Vermillion/Orange
    "#009E73",  # Bluish Green
    "#CC79A7",  # Reddish Purple
    "#F0E442",  # Yellow
    "#56B4E9",  # Sky Blue
    "#E69F00",  # Orange
    "#000000",  # Black
]

# Default styling
PUBLICATION_STYLE = {
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.edgecolor": "black",
    "axes.linewidth": 1.0,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "grid.linestyle": "--",
    "font.family": "sans-serif",
    "font.size": 12,
}
```

---

### 2.5 Exporter Module (`core/exporter.py`)

**Responsibilities:**
- Export figures to PNG/SVG/PDF/EPS formats
- Handle format-specific parameters
- Ensure publication-quality output

**Key Classes:**

```python
class ExportFormat(Enum):
    PNG = "png"
    SVG = "svg"
    PDF = "pdf"
    EPS = "eps"

@dataclass
class ExportConfig:
    format: ExportFormat
    dpi: int = 300                    # For raster formats
    transparent: bool = False
    bbox_inches: str = "tight"        # Trim whitespace
    pad_inches: float = 0.1
    
    # Format-specific
    png_compression: int = 6          # 0-9
    svg_fonttype: str = "path"        # 'path' or 'none'
    pdf_backend: str = "pdf"          # 'pdf' or 'pgf'

class Exporter:
    def export(
        self, 
        figure: Figure, 
        path: Path, 
        config: ExportConfig
    ) -> None: ...
    
    def export_multiple(
        self,
        figure: Figure,
        base_path: Path,
        formats: list[ExportFormat],
        config: ExportConfig
    ) -> list[Path]: ...
```

---

## 3. Configuration System

### 3.1 Configuration File Format (TOML)

Expert users can supply a complete configuration file:

```toml
# plottini-config.toml

[[files]]
path = "data/experiment1.tsv"
has_header = true
comment_chars = ["#", "//"]

[[files]]
path = "data/experiment2.tsv"
has_header = true

[alignment]
enabled = true
column = "time"              # Align files by this column

[[derived_columns]]
name = "velocity"
expression = "distance / time"

[[derived_columns]]
name = "energy"
expression = "0.5 * mass * velocity**2"

[[filters]]
column = "time"
min = 0.0
max = 100.0

[[series]]
x = "time"
y = "velocity"
label = "Experiment 1"
color = "#1f77b4"
transform_y = "log10"

[[series]]
x = "time"
y = "velocity"
source_file_index = 1        # Second file
label = "Experiment 2"
color = "#ff7f0e"
secondary_y = true

[plot]
type = "line"
title = "Velocity over Time"
x_label = "Time (s)"
y_label = "Velocity (m/s)"
y2_label = "Velocity - Log Scale"

figure_width = 12.0
figure_height = 8.0
show_grid = true
show_legend = true
legend_position = "upper right"

[plot.font_sizes]
title = 16
labels = 14
ticks = 12
legend = 11

[layout]
mode = "overlay"             # or "subplots"
# subplot_rows = 2
# subplot_cols = 1

[export]
format = "png"
dpi = 300
transparent = false
```

### 3.2 Configuration Schema

```python
@dataclass
class FileConfig:
    path: Path
    has_header: bool = True
    comment_chars: list[str] = field(default_factory=lambda: ["#"])
    delimiter: str = "\t"

@dataclass
class AlignmentConfig:
    enabled: bool
    column: str

@dataclass
class DerivedColumnConfig:
    name: str
    expression: str

@dataclass
class FilterConfig:
    column: str
    min: float | None = None
    max: float | None = None

@dataclass
class GrapherConfig:
    """Complete configuration for a graph."""
    files: list[FileConfig]
    alignment: AlignmentConfig | None
    derived_columns: list[DerivedColumnConfig]
    filters: list[FilterConfig]
    series: list[SeriesConfig]
    plot: PlotConfig
    layout: MultiPlotConfig
    export: ExportConfig

def load_config(path: Path) -> GrapherConfig: ...
def save_config(config: GrapherConfig, path: Path) -> None: ...
def validate_config(config: GrapherConfig) -> list[str]: ...  # Returns warnings
```

---

## 4. UI Design (NiceGUI)

### 4.1 Main Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PLOTTINI                                             [Load Config] [Save]  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────┐  ┌──────────────────────────────────┐  │
│  │  📁 DATA SOURCE                 │  │  📊 LIVE PREVIEW                 │  │
│  │  ┌───────────────────────────┐  │  │                                  │  │
│  │  │ [+ Add Files]             │  │  │                                  │  │
│  │  │ ┌─────────────────────┐   │  │  │      ┌──────────────────┐       │  │
│  │  │ │ ✓ data1.tsv    [×]  │   │  │  │      │                  │       │  │
│  │  │ │ ✓ data2.tsv    [×]  │   │  │  │      │   MATPLOTLIB     │       │  │
│  │  │ └─────────────────────┘   │  │  │      │     FIGURE       │       │  │
│  │  │                           │  │  │      │                  │       │  │
│  │  │ ☑ Has header row          │  │  │      │                  │       │  │
│  │  │ Comment chars: [#]        │  │  │      └──────────────────┘       │  │
│  │  └───────────────────────────┘  │  │                                  │  │
│  │                                 │  │  ┌──────────────────────────────┐│  │
│  │  📋 DATA PREVIEW                │  │  │ [PNG] [SVG] [PDF] [EPS]     ││  │
│  │  ┌───────────────────────────┐  │  │  │ DPI: [300▼]  [💾 Export]   ││  │
│  │  │ Col1 │ Col2 │ Col3 │ ... │  │  │  └──────────────────────────────┘│  │
│  │  │──────┼──────┼──────┼─────│  │  └──────────────────────────────────┘  │
│  │  │ 1.2  │ 3.4  │ 5.6  │     │  │                                        │
│  │  │ 2.3  │ 4.5  │ 6.7  │     │  │                                        │
│  │  └───────────────────────────┘  │                                        │
│  │  Showing 10 of 1,234 rows       │                                        │
│  └─────────────────────────────────┘                                        │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  📈 SERIES CONFIGURATION                                                ││
│  │  ┌────────────────────────────────────────────────────────────────────┐ ││
│  │  │ Series 1                                              [🗑️ Remove] │ ││
│  │  │ File: [data1.tsv ▼]  X: [time ▼]  Y: [velocity ▼]                 │ ││
│  │  │ Label: [___________]  Color: [■]  Transform Y: [None ▼]           │ ││
│  │  │ ☐ Secondary Y-axis                                                 │ ││
│  │  └────────────────────────────────────────────────────────────────────┘ ││
│  │  [+ Add Series]                                                         ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│  ┌──────────────────────────────┐  ┌────────────────────────────────────┐  │
│  │  📐 PLOT SETTINGS            │  │  🔧 ADVANCED                       │  │
│  │  Type: [Line ▼]              │  │                                    │  │
│  │  Title: [________________]   │  │  [Derived Columns]  [Filters]     │  │
│  │  X Label: [______________]   │  │  [Multi-file Alignment]           │  │
│  │  Y Label: [______________]   │  │  [Layout: ○ Overlay ○ Subplots]   │  │
│  │  ☑ Show Grid  ☑ Show Legend │  │                                    │  │
│  │  Size: W[10] × H[6] inches   │  │                                    │  │
│  └──────────────────────────────┘  └────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 UI Components

| Component | File | Description |
|-----------|------|-------------|
| **File Selector** | `file_selector.py` | Upload/browse files, toggle header, set comment chars |
| **Data Preview** | `data_preview.py` | Paginated table showing parsed data |
| **Column Mapper** | `column_mapper.py` | Series configuration with X/Y column selection |
| **Transform Panel** | `transform_panel.py` | Dropdown for applying transforms to axes |
| **Chart Config** | `chart_config.py` | Chart type, titles, labels, styling options |
| **Plot Preview** | `plot_preview.py` | Live-updating matplotlib figure display |
| **Export Panel** | `export_panel.py` | Format selection, DPI, export button |

### 4.3 UI State Management

```python
@dataclass
class AppState:
    # File state
    loaded_files: list[Path]
    parser_config: ParserConfig
    parsed_data: dict[Path, DataFrame]  # Cached parsed data
    
    # Transform state
    derived_columns: list[DerivedColumnConfig]
    filters: list[FilterConfig]
    alignment_config: AlignmentConfig | None
    
    # Plot state
    series: list[SeriesConfig]
    plot_config: PlotConfig
    multi_config: MultiPlotConfig
    
    # UI state
    selected_file_for_preview: Path | None
    current_figure: Figure | None
    error_message: str | None
    
    # Export state
    export_config: ExportConfig

class StateManager:
    """Reactive state management for UI updates."""
    def __init__(self): ...
    def update(self, **kwargs) -> None: ...
    def on_change(self, callback: Callable) -> None: ...
    def trigger_replot(self) -> None: ...
```

### 4.4 Live Preview Implementation

The live preview will update automatically when:
- Files are added/removed
- Column mappings change
- Transforms are applied
- Plot settings change
- Filters are modified

**Debouncing**: Updates are debounced by 200ms to avoid excessive redraws during rapid changes.

---

## 5. CLI Entry Point

### 5.1 Command Structure

```bash
# Start UI (default)
plottini

# Start UI on specific port
plottini --port 8080

# Start UI without opening browser
plottini --no-open

# Load configuration file directly
plottini --config my-config.toml

# Expert mode: render without UI
plottini render --config my-config.toml --output chart.png
```

### 5.2 Implementation (`cli.py`)

```python
import click
from plottini.ui.app import start_app
from plottini.config.loader import load_config
from plottini.core.plotter import Plotter
from plottini.core.exporter import Exporter

@click.group(invoke_without_command=True)
@click.option('--port', default=8050, help='Port for web UI')
@click.option('--no-open', is_flag=True, help='Do not open browser')
@click.option('--config', type=click.Path(exists=True), help='Load config file')
@click.pass_context
def cli(ctx, port, no_open, config):
    """Plottini - User-friendly graph builder"""
    if ctx.invoked_subcommand is None:
        start_app(port=port, open_browser=not no_open, config_file=config)

@cli.command()
@click.option('--config', required=True, type=click.Path(exists=True))
@click.option('--output', required=True, type=click.Path())
def render(config, output):
    """Render graph without UI (expert mode)."""
    cfg = load_config(config)
    # ... render and export
    click.echo(f"Graph exported to {output}")
```

---

## 6. Implementation Phases

### Phase 1: Core Foundation (Priority: Critical)
| Task | Description | Files |
|------|-------------|-------|
| Project setup | Create package structure, pyproject.toml | All structure files |
| TSV Parser | Implement parser with validation & error handling | `parser.py` |
| DataFrame | Data container with column operations | `dataframe.py` |
| Basic Exporter | Export to PNG/SVG/PDF/EPS | `exporter.py` |

### Phase 2a: Core Plotting - First Charts (Priority: High)
| Task | Description | Files |
|------|-------------|-------|
| Plotter base + Line | Core plotter infrastructure with Line chart | `plotter.py` |
| Bar chart | Vertical bar chart support | `plotter.py` |
| Pie chart | Pie chart support | `plotter.py` |
| Transforms | Preset math transformations | `transforms.py` |
| Derived columns | Safe expression evaluator | `transforms.py` |

### Phase 2b: Extended Chart Types (Priority: High)
| Task | Description | Files |
|------|-------------|-------|
| Polar/Radial | Polar plot support | `plotter.py` |
| Histogram | Histogram support | `plotter.py` |
| Scatter | Scatter plot support | `plotter.py` |

### Phase 2c: Remaining Chart Types (Priority: Medium)
| Task | Description | Files |
|------|-------------|-------|
| Box plot | Box plot support | `plotter.py` |
| Violin plot | Violin plot support | `plotter.py` |
| Area chart | Area chart support | `plotter.py` |
| Remaining types | Stem, Step, Errorbar, Bar horizontal | `plotter.py` |

### Phase 3: Advanced Data Features (Priority: High)
| Task | Description | Files |
|------|-------------|-------|
| Data filtering | Filter rows by value range | `dataframe.py` |
| Multi-file alignment | Align data by common column | `dataframe.py` |
| Secondary Y-axis | Dual axis support | `plotter.py` |
| TOML config | Configuration loader/saver | `loader.py`, `schema.py` |

### Phase 4: UI Implementation (Priority: High)
| Task | Description | Files |
|------|-------------|-------|
| NiceGUI app shell | Basic layout & routing | `app.py` |
| State management | Reactive state updates | `state.py` |
| File selector | File upload & configuration | `file_selector.py` |
| Data preview | Paginated data display | `data_preview.py` |
| Series config | Column mapping UI | `column_mapper.py` |
| Plot settings | Chart type, titles, styling | `chart_config.py` |
| Transform UI | Transforms & derived columns | `transform_panel.py` |
| Live preview | Real-time matplotlib rendering | `plot_preview.py` |
| Export panel | Format selection & download | `export_panel.py` |
| Filter UI | Data filtering dialog | `transform_panel.py` |
| Alignment UI | Multi-file alignment | `transform_panel.py` |

### Phase 5: CLI & Polish (Priority: Medium)
| Task | Description | Files |
|------|-------------|-------|
| CLI implementation | Click-based CLI | `cli.py` |
| Headless render | `--config` mode without UI | `cli.py` |
| Error UX | User-friendly error display | UI components |
| Unit tests | Core module tests | `tests/` |
| Documentation | README, usage examples | `README.md` |

---

## 7. Dependencies

```toml
dependencies = [
    "matplotlib>=3.7",
    "numpy>=1.24",
    "nicegui>=1.4",
    "click>=8.1",
    "tomli>=2.0; python_version<'3.11'",  # TOML parsing for Python 3.10
    "tomli-w>=1.0",                        # TOML writing
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "ruff>=0.1",
    "mypy>=1.0",
]
```

---

## 8. Key Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Config format | TOML | Python-native, readable, stdlib support (3.11+) |
| Expression safety | AST-based whitelist | Prevents code injection, math-only |
| State management | Dataclass + callbacks | Simple, no extra dependencies |
| Live preview | Debounced (200ms) | Responsive without excessive redraws |
| Color palette | Colorblind-safe defaults | Publication-friendly |
| Column numbering | 1-based when no headers | More user-friendly for non-programmers |

---

## 9. Error Handling Strategy

### Parser Errors
- Provide exact file path, line number, column index
- Show context (the problematic line with pointer)
- Suggest fixes when possible (e.g., "Did you mean to use # as comment?")

### Expression Errors
- Validate expressions before evaluation
- Show which column names are available
- Provide example expressions

### UI Errors
- Display errors in a prominent but non-modal way
- Allow users to continue working while fixing issues
- Provide "Learn More" links to documentation

---

## 10. Testing Strategy

### Unit Tests
- Parser: Test with various TSV formats, edge cases, malformed data
- DataFrame: Test filtering, derived columns, alignment
- Transforms: Test all transformation functions
- Plotter: Test each chart type with sample data
- Config: Test TOML loading/saving

### Integration Tests
- End-to-end: Load files → transform → plot → export
- Multi-file: Test alignment and overlay scenarios
- Config: Load config file and render complete graph

### Test Fixtures
```
tests/fixtures/
├── simple.tsv              # Basic 2-column data
├── with_headers.tsv        # Data with header row
├── no_headers.tsv          # Data without headers
├── comments.tsv            # Data with comment lines
├── multifile/
│   ├── exp1.tsv           # First dataset
│   └── exp2.tsv           # Second dataset (same time column)
└── malformed/
    ├── non_numeric.tsv    # Contains text in data columns
    ├── ragged.tsv         # Inconsistent column counts
    └── empty.tsv          # Empty file
```

---

## 11. Publication Quality Guidelines

### Colors
- Use colorblind-safe palette (8 distinct colors)
- High contrast against white background
- Distinct when printed in grayscale

### Fonts
- Sans-serif for readability
- Minimum 10pt for tick labels
- Clear, descriptive axis labels

### Layout
- Tight bounding box (minimal whitespace)
- Grid lines for readability (subtle)
- Legend positioned to not obscure data

### Export
- Default 300 DPI for raster formats
- Vector formats (SVG, PDF, EPS) for scalability
- Embed fonts in vector formats

---

## 12. Future Enhancements (Post-MVP)

| Feature | Description | Priority |
|---------|-------------|----------|
| Session persistence | Remember last used settings | Low |
| Plot templates | Common configurations as presets | Low |
| Trendlines | Linear/polynomial regression | Low |
| Error bars | Uncertainty visualization | Low |
| Annotations | Add text labels, arrows | Low |
| Batch export | Export in multiple formats at once | Low |
| Dark mode | Optional dark UI theme | Low |

---

## 13. Getting Started for Developers

```bash
# Clone repository
git clone <repo-url>
cd plottini

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check .

# Run type checker
mypy src/plottini

# Start application
plottini
```

---

## 14. Release Process

1. Update version in `src/plottini/__init__.py`
2. Update `CHANGELOG.md`
3. Create git tag: `git tag v0.1.0`
4. Push tag: `git push --tags`
5. GitHub Actions will automatically build and publish to PyPI

---

## Notes

- **User Experience First**: Every design decision prioritizes ease of use for non-technical users
- **Publication Ready**: Default settings produce high-quality, publication-ready graphs
- **Fail-Fast**: Validate early and provide clear, actionable error messages
- **Progressive Disclosure**: Simple defaults with advanced options available but not overwhelming
- **No Arbitrary Code Execution**: Safe expression evaluation for derived columns
