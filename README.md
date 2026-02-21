# HDV — Hierarchical Data Viewer

Interactive terminal app to explore CSV data by drilling down through dimensions. Built with [Textual](https://textual.textualize.io/).

## Features

- **Load any CSV**: Columns are classified into numeric (summed) and non-numeric (dimensions).
- **Top level**: First non-numeric column is grouped; numeric columns are summed per value.
- **Drill down**: Move with **↑/↓**, press **→** to expand the selected row and see the next dimension (with aggregates filtered to that selection).
- **Go back**: Press **←** to move up one level.
- **Breadcrumb**: Shows current path (e.g. `North / Sales`).
- **Path columns**: Columns that look like file paths (e.g. a/b/c) can have the components treated as columns

## Install

### With Homebrew (recommended)

```bash
brew tap acbeers/tap
brew update
brew install hdv
```

### With uv from source

```bash
uv tool install hdv
# or from a local checkout:
cd /path/to/hdv && uv pip install -e .
hdv path/to/file.csv
```

### With pip

```bash
pip install hdv
hdv file.csv
```

## Usage

```bash
hdv path/to/data.csv
# Read from stdin (e.g. pipe or redirect)
cat data.csv | hdv
cat data.csv | hdv -
```

Keyboard commands:

- **↑ / ↓** — Change selected row
- **→** — Expand (drill into selected value)
- **←** — Back (one level up)
- **s** - Change sorting between numeric and non-numeric columns
- **q** — Quit

Options:

| Option                      | Description                                                                            |
| --------------------------- | -------------------------------------------------------------------------------------- |
| -h, --help                  | Show help                                                                              |
| -p, --path-column COLUMN    | Treat COLUMN as a slash-separated path and drill by path segments                      |
| -s, --string-column COLUMN  | Treat COLUMN as a regular string (disable path auto-detection for it); may be repeated |
| -c, --columns COL1,COL2,... | Comma-separated list of columns to show (in order); unlisted columns are hidden        |

## Example

Given `sample.csv`:

| region | department | product  | revenue | units |
| ------ | ---------- | -------- | ------- | ----- |
| North  | Sales      | Widget A | 1000    | 10    |
| North  | Sales      | Widget B | 1500    | 15    |
| ...    | ...        | ...      | ...     | ...   |

- Top level: regions (North, South) with total revenue and units.
- Expand **North** → departments (Sales, Support) with totals for North only.
- Expand **Sales** → products (Widget A, Widget B) with totals for North + Sales.

## Development

```bash
uv sync
uv run hdv sample.csv
# or
uv run python -m hdv sample.csv
```

## License

MIT
