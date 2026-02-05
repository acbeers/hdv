# HDV — Hierarchical Data Viewer

Interactive terminal app to explore CSV data by drilling down through dimensions. Built with [Textual](https://textual.textualize.io/).

## Features

- **Load any CSV**: Columns are classified into numeric (summed) and non-numeric (dimensions).
- **Top level**: First non-numeric column is grouped; numeric columns are summed per value.
- **Drill down**: Move with **↑/↓**, press **→** to expand the selected row and see the next dimension (with aggregates filtered to that selection).
- **Go back**: Press **←** to move up one level.
- **Breadcrumb**: Shows current path (e.g. `North / Sales`).

## Install

### With uv (recommended)

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

### Homebrew (when published)

A Homebrew formula can install the package via `pip` in a dedicated venv, or use a bottled wheel. Example formula (tap):

```ruby
class Hdv < Formula
  desc "Hierarchical Data Viewer for CSV"
  homepage "https://github.com/yourusername/hdv"
  url "https://files.pythonhosted.org/packages/.../hdv-0.1.0.tar.gz"
  sha256 "..."

  depends_on "python@3.10"

  def install
    venv = virtualenv_create(libexec, "python3.10")
    venv.pip_install resources
    venv.pip_install_and_link buildpath
    bin.install_symlink libexec/"bin/hdv"
  end

  test do
    assert_match "usage", shell_output("#{bin}/hdv --help")
  end
end
```

Or use `brew install hdv` once the formula is in a tap.

## Usage

```bash
hdv path/to/data.csv
# Read from stdin (e.g. pipe or redirect)
cat data.csv | hdv
cat data.csv | hdv -
```

- **↑ / ↓** — Change selected row  
- **→** — Expand (drill into selected value)  
- **←** — Back (one level up)  
- **q** — Quit  

## Example

Given `sample.csv`:

| region | department | product | revenue | units |
|--------|------------|---------|---------|-------|
| North  | Sales      | Widget A| 1000    | 10    |
| North  | Sales      | Widget B| 1500   | 15    |
| ...    | ...        | ...     | ...     | ...   |

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
