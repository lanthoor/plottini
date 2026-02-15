# Plottini - Implementation Plan

---

# Part 1: Architecture

## 1. Project Overview

**Plottini** is a user-friendly, UI-driven graph builder that allows non-technical users to create publication-quality graphs from TSV data files using matplotlib as the rendering backend.

| Attribute      | Value         |
|----------------|---------------|
| Package name   | `plottini`    |
| Author         | Lallu Anthoor |
| License        | MIT           |
| Config format  | TOML          |
| Python version | >=3.10        |
| UI framework   | NiceGUI       |
| Backend        | matplotlib    |

---

## 2. Requirements

### 2.1 Functional Requirements

**Data Input:**
- Load one or more TSV files
- Support configurable comment delimiters (default: `#`)
- Handle files with or without headers
- Validate all data is numeric
- Provide detailed error messages (file, line, column)

**Data Transformation:**
- Apply preset mathematical transformations (log, sqrt, power, trig)
- Create derived columns from expressions (safe evaluation only)
- Filter rows by value ranges
- Align multiple files by a common column

**Visualization:**
- Support chart types: Line, Bar, Pie, Scatter, Histogram, Polar, Box, Violin, Area, Stem, Step, Error bar
- Configure titles, labels, colors, line styles, markers
- Support secondary Y-axis
- Overlay multiple series or create subplots
- Live preview with debounced updates (200ms)
- Publication-quality defaults (colorblind-safe palette)

**Export:**
- Export to PNG, SVG, PDF, EPS formats
- Configurable DPI for raster formats
- High-quality output for publications

**Configuration:**
- Load/save complete graph configurations as TOML files
- Headless rendering mode for batch processing

### 2.2 Non-Functional Requirements

**Usability:**
- Intuitive UI for non-technical users
- Clear, actionable error messages
- Progressive disclosure of advanced options

**Performance:**
- Handle datasets with thousands of rows efficiently
- Responsive UI (no blocking operations)
- Cache parsed data to avoid re-reading

**Security:**
- Safe expression evaluation (no arbitrary code execution)
- AST-based whitelist for derived columns

**Quality:**
- Type-safe code with mypy strict mode
- &gt; 80% test coverage
- PEP 8 compliant (enforced by ruff)

---

## 3. Architecture Design

### 3.1 Project Structure

```
plottini/
├── src/plottini/
│   ├── __init__.py              # Package init, version
│   ├── __main__.py              # Entry point: python -m plottini
│   ├── cli.py                   # CLI with Click
│   ├── core/                    # Core functionality
│   │   ├── parser.py            # TSV parsing
│   │   ├── dataframe.py         # Data container
│   │   ├── transforms.py        # Math transformations
│   │   ├── plotter.py           # Matplotlib rendering
│   │   └── exporter.py          # Export functionality
│   ├── config/                  # Configuration management
│   │   ├── schema.py            # Configuration dataclasses
│   │   ├── loader.py            # TOML loader/saver
│   │   └── defaults.py          # Default values
│   ├── ui/                      # NiceGUI interface
│   │   ├── app.py               # Main app
│   │   ├── state.py             # State management
│   │   └── components/          # UI components
│   └── utils/                   # Utilities
│       ├── errors.py            # Custom exceptions
│       └── validators.py        # Input validation
└── tests/                       # Test suite
    ├── fixtures/                # Test data
    └── test_*.py                # Test modules
```

### 3.2 Module Specifications

#### Parser Module (`core/parser.py`)

**Purpose**: Read and validate TSV files

**Classes:**
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
    def parse(self, file_path: Path) -> DataFrame
    def parse_multiple(self, file_paths: list[Path]) -> list[DataFrame]
```

**Error Format:**
```
ParseError: Invalid numeric value in file 'data.tsv'
  Line 42, Column 3: expected number, got 'N/A'
  Context: "1.5    2.3    N/A    4.1"
                          ^^^
```

#### DataFrame Module (`core/dataframe.py`)

**Purpose**: Store and manipulate parsed data

**Classes:**
```python
@dataclass
class Column:
    name: str                    # Header or "Column 1", "Column 2", etc.
    index: int
    data: np.ndarray
    is_derived: bool = False

@dataclass
class DataFrame:
    columns: dict[str, Column]
    source_file: Path
    row_count: int
    
    def add_derived_column(self, name: str, expression: str) -> None
    def filter_rows(self, column: str, min_val: float | None, max_val: float | None) -> DataFrame
    def get_column_names(self) -> list[str]

def align_dataframes(dataframes: list[DataFrame], align_column: str) -> AlignedDataFrames
```

#### Transforms Module (`core/transforms.py`)

**Purpose**: Apply mathematical transformations

**Presets:**
- Logarithmic: log, log10, log2
- Power: square, cube, sqrt, cbrt
- Trigonometric: sin, cos, tan, arcsin, arccos, arctan
- Other: abs, inverse (1/x), exp, negate

**Classes:**
```python
class Transform(Enum):
    LOG = "log"
    LOG10 = "log10"
    SQUARE = "square"
    SQRT = "sqrt"
    # ...

def apply_transform(data: np.ndarray, transform: Transform) -> np.ndarray
def evaluate_expression(expression: str, columns: dict[str, np.ndarray]) -> np.ndarray
```

**Derived Column Syntax:**
- Reference columns: `col1`, `col2`, `"Column 1"`
- Operators: `+`, `-`, `*`, `/`, `**`, `%`
- Functions: `log`, `sqrt`, `sin`, etc.
- Example: `col1 / col2`, `sqrt(col1**2 + col2**2)`

#### Plotter Module (`core/plotter.py`)

**Purpose**: Generate matplotlib figures

**Chart Types (Implementation Order):**
1. **Phase 2a**: Line, Bar, Pie
2. **Phase 2b**: Polar, Histogram, Scatter
3. **Phase 2c**: Box, Violin, Area, Bar Horizontal, Stem, Step, Error bar

**Classes:**
```python
class ChartType(Enum):
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    # ...

@dataclass
class SeriesConfig:
    x_column: str
    y_column: str
    label: str | None = None
    color: str | None = None
    line_style: str = "-"
    marker: str | None = None
    transform_x: Transform | None = None
    transform_y: Transform | None = None
    use_secondary_y: bool = False
    source_file_index: int = 0

@dataclass
class PlotConfig:
    chart_type: ChartType
    title: str = ""
    x_label: str = ""
    y_label: str = ""
    y2_label: str = ""
    figure_width: float = 10.0
    figure_height: float = 6.0
    show_grid: bool = True
    show_legend: bool = True
    # ... styling options

class Plotter:
    def create_figure(self, data: DataFrame | list[DataFrame], series: list[SeriesConfig]) -> Figure
```

**Publication-Quality Defaults:**
- Colorblind-safe palette (8 colors)
- White background
- Clear, distinguishable colors
- Professional typography

#### Exporter Module (`core/exporter.py`)

**Purpose**: Export figures to various formats

**Classes:**
```python
class ExportFormat(Enum):
    PNG = "png"
    SVG = "svg"
    PDF = "pdf"
    EPS = "eps"

@dataclass
class ExportConfig:
    format: ExportFormat
    dpi: int = 300
    transparent: bool = False
    bbox_inches: str = "tight"
    pad_inches: float = 0.1

class Exporter:
    def export(self, figure: Figure, path: Path, config: ExportConfig) -> None
    def export_multiple(self, figure: Figure, base_path: Path, formats: list[ExportFormat]) -> list[Path]
```

### 3.3 Configuration System

**TOML Format:**
```toml
[[files]]
path = "data.tsv"
has_header = true
comment_chars = ["#"]

[alignment]
enabled = true
column = "time"

[[derived_columns]]
name = "velocity"
expression = "distance / time"

[[filters]]
column = "time"
min = 0.0
max = 100.0

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

**Configuration Schema:**
```python
@dataclass
class GrapherConfig:
    files: list[FileConfig]
    alignment: AlignmentConfig | None
    derived_columns: list[DerivedColumnConfig]
    filters: list[FilterConfig]
    series: list[SeriesConfig]
    plot: PlotConfig
    layout: MultiPlotConfig
    export: ExportConfig

def load_config(path: Path) -> GrapherConfig
def save_config(config: GrapherConfig, path: Path) -> None
```

### 3.4 UI Design (NiceGUI)

**Layout:**
- Left panel: Data source, preview, series configuration
- Right panel: Live preview, export options
- Bottom panel: Plot settings, advanced options

**State Management:**
```python
@dataclass
class AppState:
    loaded_files: list[Path]
    parser_config: ParserConfig
    parsed_data: dict[Path, DataFrame]
    derived_columns: list[DerivedColumnConfig]
    filters: list[FilterConfig]
    series: list[SeriesConfig]
    plot_config: PlotConfig
    current_figure: Figure | None
    error_message: str | None
```

**Live Preview:**
- Debounced updates (200ms)
- Update triggers: file changes, column mappings, transformations, settings

### 3.5 CLI Design

**Commands:**
```bash
# Start UI (default)
plottini [--port 8050] [--no-open] [--config FILE]

# Headless render
plottini render --config FILE --output FILE [--format FORMAT] [--dpi DPI]

# Version info
plottini version
```

---

## 4. Design Decisions

### 4.1 Technology Choices

| Decision          | Choice                | Rationale                               |
|-------------------|-----------------------|-----------------------------------------|
| Config format     | TOML                  | Python-native, readable, stdlib support |
| Expression safety | AST whitelist         | Prevents code injection, math-only      |
| State management  | Dataclass + callbacks | Simple, no extra dependencies           |
| Color palette     | Colorblind-safe       | Publication-friendly                    |
| Column numbering  | 1-based (no headers)  | User-friendly for non-programmers       |

### 4.2 Chart Type Priority

Implementation order based on user needs:
1. **Most common**: Line, Bar, Pie (Phase 2a)
2. **Scientific**: Polar, Histogram, Scatter (Phase 2b)
3. **Advanced**: Box, Violin, Area, etc. (Phase 2c)

### 4.3 Security Approach

**Derived Columns:**
- Use `ast.parse()` to analyze expressions
- Whitelist allowed operations and functions
- No `eval()` or `exec()` ever
- Validate before evaluation

### 4.4 Performance Strategy

- Use numpy vectorized operations
- Avoid Python loops on large arrays
- Cache parsed data in memory
- Debounce UI updates
- Background threads for long operations

---

# Part 2: Implementation Plan

## Phase 0: Project Setup ✅

| #    | Task                           | Status | Files                                                  |
|------|--------------------------------|--------|--------------------------------------------------------|
| 0.1  | Create project structure       | ✅      | All directories                                        |
| 0.2  | Configure pyproject.toml       | ✅      | `pyproject.toml`                                       |
| 0.3  | Create __init__.py files       | ✅      | All `__init__.py`                                      |
| 0.4  | Implement CLI framework        | ✅      | `cli.py`, `__main__.py`                                |
| 0.5  | Setup GitHub Actions (CI)      | ✅      | `.github/workflows/ci.yml`                             |
| 0.6  | Setup GitHub Actions (publish) | ✅      | `.github/workflows/publish.yml`                        |
| 0.7  | Create LICENSE (MIT)           | ✅      | `LICENSE`                                              |
| 0.8  | Create .gitignore              | ✅      | `.gitignore`                                           |
| 0.9  | Create basic tests             | ✅      | `tests/test_basic.py`, `tests/test_cli.py`             |
| 0.10 | Create documentation           | ✅      | `README.md`, `PLAN.md`, `CONTRIBUTING.md`, `AGENTS.md` |

**Phase 0 Status**: ✅ Complete

---

## Phase 1: Core Foundation ✅

**Priority**: Critical  
**Goal**: Implement core data handling and basic visualization

| #   | Task                     | Status | Files                                                         | Estimated Time |
|-----|--------------------------|--------|---------------------------------------------------------------|----------------|
| 1.1 | Implement TSV Parser     | ✅      | `src/plottini/core/parser.py`<br>`tests/test_parser.py`       | 2 hours        |
| 1.2 | Create test fixtures     | ✅      | `tests/fixtures/*.tsv`                                        | 0.5 hours      |
| 1.3 | Implement DataFrame      | ✅      | `src/plottini/core/dataframe.py`<br>`tests/test_dataframe.py` | 1.5 hours      |
| 1.4 | Implement Exporter       | ✅      | `src/plottini/core/exporter.py`<br>`tests/test_exporter.py`   | 1 hour         |
| 1.5 | Create custom exceptions | ✅      | `src/plottini/utils/errors.py`<br>`tests/test_errors.py`      | 0.5 hours      |

**Phase 1 Status**: ✅ Complete

---

## Phase 2a: Core Plotting - First Charts ✅

**Priority**: High  
**Goal**: Basic plotting functionality with essential chart types

**Dependencies**: Phase 1 (Complete)

| #    | Task                                          | Status | Files                                                               | Estimated Time |
|------|-----------------------------------------------|--------|---------------------------------------------------------------------|----------------|
| 2a.1 | Implement Plotter base + Line chart           | ✅      | `src/plottini/core/plotter.py`<br>`tests/test_plotter.py`           | 1.5 hours      |
| 2a.2 | Add Bar chart support                         | ✅      | `src/plottini/core/plotter.py`                                      | 1 hour         |
| 2a.3 | Add Pie chart support                         | ✅      | `src/plottini/core/plotter.py`                                      | 1 hour         |
| 2a.4 | Implement Transforms module                   | ✅      | `src/plottini/core/transforms.py`<br>`tests/test_transforms.py`     | 1 hour         |
| 2a.5 | Implement safe expression evaluator           | ✅      | `src/plottini/core/transforms.py`<br>`src/plottini/utils/errors.py` | 2 hours        |
| 2a.6 | Integrate expression evaluator with DataFrame | ✅      | `src/plottini/core/dataframe.py`<br>`tests/test_dataframe.py`       | 0.5 hours      |

**Phase 2a Status**: ✅ Complete

### Phase 2a Implementation Details

#### Task 2a.1: Plotter Base + Line Chart

**Classes to implement:**
- `ChartType` enum with LINE, BAR, PIE values
- `SeriesConfig` dataclass for series configuration
- `PlotConfig` dataclass for plot settings
- `Plotter` class with `create_figure()` method

**Publication-quality defaults:**
- Colorblind-safe 8-color palette: `['#0072B2', '#E69F00', '#009E73', '#CC79A7', '#F0E442', '#56B4E9', '#D55E00', '#000000']`
- White background, grid enabled
- Figure size: 10x6 inches

**Plotter module structure:**
```python
# src/plottini/core/plotter.py

from enum import Enum
from dataclasses import dataclass, field
from matplotlib.figure import Figure
from matplotlib.axes import Axes

class ChartType(Enum):
    LINE = "line"
    BAR = "bar"
    PIE = "pie"

@dataclass
class SeriesConfig:
    x_column: str
    y_column: str
    label: str | None = None
    color: str | None = None
    line_style: str = "-"
    marker: str | None = None
    line_width: float = 1.5
    use_secondary_y: bool = False
    source_file_index: int = 0

@dataclass 
class PlotConfig:
    chart_type: ChartType = ChartType.LINE
    title: str = ""
    x_label: str = ""
    y_label: str = ""
    figure_width: float = 10.0
    figure_height: float = 6.0
    show_grid: bool = True
    show_legend: bool = True

COLORBLIND_PALETTE = [
    '#0072B2',  # Blue
    '#E69F00',  # Orange
    '#009E73',  # Green
    '#CC79A7',  # Pink
    '#F0E442',  # Yellow
    '#56B4E9',  # Light blue
    '#D55E00',  # Red-orange
    '#000000',  # Black
]
```

#### Task 2a.4-2a.5: Transforms and Expression Evaluator

**Security requirements (CRITICAL):**
- Use AST parsing with whitelist approach
- **NEVER** use `eval()` or `exec()`
- Allow only: arithmetic operators, numeric literals, column references, whitelisted functions
- Reject: imports, attribute access, function calls outside whitelist

**Allowed operations:**
- Binary: `+`, `-`, `*`, `/`, `**`, `%`
- Unary: `-x`, `+x`
- Functions: `log`, `log10`, `log2`, `sqrt`, `abs`, `sin`, `cos`, `tan`, `exp`

**Expression syntax:**
- Column references: `col1`, `col2`, `"Column Name With Spaces"`
- Examples: `col1 / col2`, `sqrt(col1**2 + col2**2)`, `log10(col1)`

**Safe expression evaluator implementation:**
```python
# Allowed AST node types
ALLOWED_NODES = {
    ast.Expression,  # Top-level
    ast.BinOp,       # a + b, a * b, etc.
    ast.UnaryOp,     # -x, +x
    ast.Num,         # Legacy numeric literals (Python < 3.8)
    ast.Constant,    # Numeric literals (Python >= 3.8)
    ast.Name,        # Column references
    ast.Call,        # Function calls (validated separately)
    ast.Load,        # Variable loading context
}

# Allowed binary operators
ALLOWED_BINOPS = {ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod}

# Allowed unary operators  
ALLOWED_UNARYOPS = {ast.USub, ast.UAdd}

# Allowed function names
ALLOWED_FUNCTIONS = {'log', 'log10', 'log2', 'sqrt', 'abs', 'sin', 'cos', 'tan', 'exp'}
```

**What to reject:**
- `ast.Attribute` - No attribute access (e.g., `os.system`)
- `ast.Import` / `ast.ImportFrom` - No imports
- `ast.Lambda` - No lambda functions
- Any function call not in `ALLOWED_FUNCTIONS`

**Testing edge cases:**
```python
def test_log_of_negative_raises():
    """log of negative numbers should raise or return NaN."""
    
def test_division_by_zero():
    """Division by zero should handle gracefully (inf or error)."""
    
def test_invalid_expression_rejected():
    """Dangerous expressions must be rejected."""
    expressions_to_reject = [
        "__import__('os')",
        "os.system('rm -rf /')",
        "lambda x: x",
        "().__class__.__bases__[0]",
    ]
```

---

## Phase 2b: Extended Chart Types ✅

**Priority**: High  
**Goal**: Add scientific chart types

| #    | Task                     | Status | Files                          | Estimated Time |
|------|--------------------------|--------|--------------------------------|----------------|
| 2b.1 | Add Polar/Radial chart   | ✅      | `src/plottini/core/plotter.py` | 1 hour         |
| 2b.2 | Add Histogram support    | ✅      | `src/plottini/core/plotter.py` | 1 hour         |
| 2b.3 | Add Scatter plot support | ✅      | `src/plottini/core/plotter.py` | 1 hour         |

**Phase 2b Status**: ✅ Complete

---

## Phase 2c: Remaining Chart Types ✅

**Priority**: Medium  
**Goal**: Complete chart type coverage

| #    | Task                                                        | Status | Files                          | Estimated Time |
|------|-------------------------------------------------------------|--------|--------------------------------|----------------|
| 2c.1 | Add Box plot                                                | ✅      | `src/plottini/core/plotter.py` | 0.5 hours      |
| 2c.2 | Add Violin plot                                             | ✅      | `src/plottini/core/plotter.py` | 0.5 hours      |
| 2c.3 | Add Area chart                                              | ✅      | `src/plottini/core/plotter.py` | 0.5 hours      |
| 2c.4 | Add remaining types (Stem, Step, Error bar, Bar horizontal) | ✅      | `src/plottini/core/plotter.py` | 1.5 hours      |

**Phase 2c Status**: ✅ Complete

---

## Phase 3: Advanced Data Features ✅

**Priority**: High  
**Goal**: Data manipulation and multi-file support

| #   | Task                           | Status | Files                                                     | Estimated Time |
|-----|--------------------------------|--------|-----------------------------------------------------------|----------------|
| 3.1 | Implement data filtering       | ✅      | `src/plottini/core/dataframe.py`                          | 1 hour         |
| 3.2 | Implement multi-file alignment | ✅      | `src/plottini/core/dataframe.py`                          | 1.5 hours      |
| 3.3 | Implement secondary Y-axis     | ✅      | `src/plottini/core/plotter.py`                            | 1 hour         |
| 3.4 | Implement configuration schema | ✅      | `src/plottini/config/schema.py`<br>`tests/test_config.py` | 1.5 hours      |
| 3.5 | Implement TOML loader/saver    | ✅      | `src/plottini/config/loader.py`                           | 1.5 hours      |
| 3.6 | Implement defaults             | ✅      | `src/plottini/config/defaults.py`                         | 0.5 hours      |

**Phase 3 Status**: ✅ Complete

---

## Phase 4: UI Implementation ✅

**Priority**: High  
**Goal**: Complete NiceGUI user interface

| #    | Task                           | Status | Files                                           | Estimated Time |
|------|--------------------------------|--------|-------------------------------------------------|----------------|
| 4.1  | Create NiceGUI app shell       | ✅      | `src/plottini/ui/app.py`                        | 1.5 hours      |
| 4.2  | Implement state management     | ✅      | `src/plottini/ui/state.py`                      | 1.5 hours      |
| 4.3  | Implement file selector        | ✅      | `src/plottini/ui/components/file_selector.py`   | 1.5 hours      |
| 4.4  | Implement data preview table   | ✅      | `src/plottini/ui/components/data_preview.py`    | 1 hour         |
| 4.5  | Implement series configuration | ✅      | `src/plottini/ui/components/series_config.py`   | 2 hours        |
| 4.6  | Implement chart settings panel | ✅      | `src/plottini/ui/components/chart_config.py`    | 1.5 hours      |
| 4.7  | Implement transform UI         | ✅      | `src/plottini/ui/components/transform_panel.py` | 2 hours        |
| 4.8  | Implement live preview         | ✅      | `src/plottini/ui/components/plot_preview.py`    | 2 hours        |
| 4.9  | Implement export panel         | ✅      | `src/plottini/ui/components/export_panel.py`    | 1 hour         |
| 4.10 | Implement filter dialog        | ✅      | `src/plottini/ui/components/filter_panel.py`    | 1 hour         |
| 4.11 | Implement alignment UI         | ✅      | `src/plottini/ui/components/alignment_panel.py` | 1 hour         |

**Phase 4 Status**: ✅ Complete

---

## Phase 5: Polish & Testing

**Priority**: Medium  
**Goal**: Production readiness

| #   | Task                              | Status | Files                          | Estimated Time |
|-----|-----------------------------------|--------|--------------------------------|----------------|
| 5.1 | Complete CLI integration          | ✅      | `src/plottini/cli.py`          | 1 hour         |
| 5.2 | Implement headless render mode    | ✅      | `src/plottini/cli.py`          | 1 hour         |
| 5.3 | User-friendly error display in UI | ✅      | UI components                  | 1 hour         |
| 5.4 | Comprehensive unit tests          | ✅      | `tests/`                       | 3 hours        |
| 5.5 | Integration tests                 | ✅      | `tests/`                       | 2 hours        |
| 5.6 | Update documentation              | ✅      | `README.md`, `CONTRIBUTING.md` | 1.5 hours      |

**Phase 5 Status**: ✅ Complete

---

## Progress Summary

| Phase                      | Status           | Progress  | Total Time    |
|----------------------------|------------------|-----------|---------------|
| Phase 0: Setup             | ✅ Complete       | 10/10     | -             |
| Phase 1: Core Foundation   | ✅ Complete       | 5/5       | 5.5 hours     |
| Phase 2a: First Charts     | ✅ Complete       | 6/6       | 7 hours       |
| Phase 2b: Extended Charts  | ✅ Complete       | 3/3       | 3 hours       |
| Phase 2c: Remaining Charts | ✅ Complete       | 4/4       | 3 hours       |
| Phase 3: Advanced Features | ✅ Complete       | 6/6       | 7 hours       |
| Phase 4: UI                | ✅ Complete       | 11/11     | 16 hours      |
| Phase 5: Polish            | ✅ Complete       | 6/6       | 9.5 hours     |
| **TOTAL**                  | **100% Complete** | **51/51** | **~51 hours** |

---

## Project Complete

All phases have been completed. The project is now production-ready with:
- Full TSV parsing with multi-block support
- 13 chart types (Line, Bar, Pie, Scatter, Histogram, Polar, Box, Violin, Area, Stem, Step, Error bar, Horizontal bar)
- Data transformations and derived columns
- Multi-file support with alignment
- Secondary Y-axis
- Complete NiceGUI web interface
- Headless render mode for batch processing
- TOML configuration system
- 447 passing tests
- Comprehensive error handling
