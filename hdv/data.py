"""CSV loading, column classification, and hierarchical aggregation."""

from __future__ import annotations

from pathlib import Path
from typing import IO

import pandas as pd


def _path_segments(s: str) -> list[str]:
    """Return list of non-empty path segments (leading/trailing slashes stripped)."""
    return [x for x in str(s).strip("/").split("/") if x]


def _common_path_prefix(values: list[str]) -> str:
    """Return the longest common path prefix (by segments) for the given path strings.
    E.g. ['/a/b/c', '/a/b/d', '/a/b'] -> 'a/b'. Returns '' if no common prefix.
    """
    if not values:
        return ""
    segs_list = [_path_segments(v) for v in values if pd.notna(v) and str(v).strip()]
    if not segs_list:
        return ""
    common = segs_list[0]
    for segs in segs_list[1:]:
        n = 0
        while n < len(common) and n < len(segs) and common[n] == segs[n]:
            n += 1
        common = common[:n]
        if not common:
            return ""
    return "/".join(common)


def _strip_path_prefix(value: str, prefix: str) -> str:
    """Remove the given segment prefix from value. Returns value with prefix and following slash removed."""
    if not prefix or pd.isna(value):
        return str(value) if not pd.isna(value) else ""
    val_segs = _path_segments(value)
    pre_segs = _path_segments(prefix)
    if pre_segs and val_segs[: len(pre_segs)] == pre_segs:
        remainder = val_segs[len(pre_segs) :]
        return "/".join(remainder) if remainder else ""
    return str(value).strip("/") if isinstance(value, str) else str(value)


def _expand_path_column(
    df: pd.DataFrame,
    path_column: str,
    dimension_columns: list[str],
) -> tuple[pd.DataFrame, list[str]]:
    """Expand a slash-separated path column into path_0, path_1, ... path_{depth-1}.
    path_i is the prefix with i+1 segments (e.g. 'a', 'a/b', 'a/b/c').
    Returns (df with new columns, new dimension_columns with path levels in place of path_column).
    """
    if path_column not in dimension_columns:
        return df, dimension_columns
    # Max depth = max number of segments in any cell
    def segments(s: str) -> list[str]:
        return _path_segments(s)

    depths = df[path_column].apply(lambda s: len(segments(s)))
    max_depth = int(depths.max()) if len(depths) else 0
    if max_depth == 0:
        # Path column is empty everywhere; one level with empty string
        max_depth = 1
    new_cols: list[str] = []
    for i in range(max_depth):
        def prefix(j: int):
            def get_prefix(val):
                segs = segments(val)
                if j >= len(segs):
                    return "/".join(segs) if segs else ""
                return "/".join(segs[: j + 1])

            return get_prefix

        col_name = f"{path_column}_{i}"
        df[col_name] = df[path_column].apply(prefix(i))
        new_cols.append(col_name)
    # Replace path_column with path_0, path_1, ... in dimension order
    new_dims: list[str] = []
    for c in dimension_columns:
        if c == path_column:
            new_dims.extend(new_cols)
        else:
            new_dims.append(c)
    return df, new_dims


def _detect_path_column(
    df: pd.DataFrame,
    dimension_columns: list[str],
    string_columns: list[str],
) -> str | None:
    """Return the dimension column that looks most like a path (has the most '/' per entry on average),
    and is not in string_columns. Returns None if none found.
    """
    best_col: str | None = None
    best_mean_slashes: float = -1.0
    for col in dimension_columns:
        if col in string_columns:
            continue
        if col not in df.columns:
            continue
        s = df[col].astype(str)
        if not s.str.contains("/", regex=False).any():
            continue
        mean_slashes = s.str.count("/").mean()
        if mean_slashes > best_mean_slashes:
            best_mean_slashes = mean_slashes
            best_col = col
    return best_col


def load_and_classify(
    source: str | Path | IO[str],
    path_column: str | None = None,
    string_columns: list[str] | None = None,
    column_filter: list[str] | None = None,
) -> tuple[pd.DataFrame, list[str], list[str], str | None]:
    """Load CSV from path or file-like and return (df, dimension_columns, numeric_columns, path_column_used).
    If path_column is set, that column is expanded into segment levels (path_0, path_1, ...).
    Otherwise, a path column is auto-detected (dimension with the most '/' per entry on average, not in string_columns).
    string_columns: dimension columns to treat as regular strings (no path expansion).
    column_filter: if set, only these columns are kept (in this order); others are never displayed.
    """
    df = pd.read_csv(source)
    numeric_columns: list[str] = []
    for col in df.columns:
        coerced = pd.to_numeric(df[col], errors="coerce")
        # Column is numeric if it has at least one valid number (and isn't all NaN)
        if coerced.notna().any():
            numeric_columns.append(col)
    # Dimensions = non-numeric, in original column order
    dimension_columns = [c for c in df.columns if c not in numeric_columns]

    str_cols = string_columns or []
    if path_column is None:
        path_column = _detect_path_column(df, dimension_columns, str_cols)
    if path_column:
        if path_column not in df.columns:
            raise ValueError(
                f"Path column {path_column!r} not found in CSV columns: {list(df.columns)}"
            )
        # Auto-remove common path prefix so all entries are relative
        path_values = df[path_column].dropna().astype(str).tolist()
        prefix = _common_path_prefix(path_values)
        if prefix:
            df = df.copy()
            df[path_column] = df[path_column].apply(lambda v: _strip_path_prefix(v, prefix))
        df, dimension_columns = _expand_path_column(df, path_column, dimension_columns)

    if column_filter:
        # Build allowed list: for each name in filter, include it (or path_column_0, path_column_1, ...
        # if it's the path column that was expanded); preserve filter order
        allowed: list[str] = []
        for c in column_filter:
            if c == path_column and path_column:
                # Include all expanded path levels (path_column_0, path_column_1, ...)
                path_cols = [col for col in dimension_columns if col.startswith(path_column + "_")]
                allowed.extend(path_cols)
            elif c in df.columns:
                allowed.append(c)
        if not allowed:
            raise ValueError(
                f"None of the specified columns {column_filter!r} exist in CSV: {list(df.columns)}"
            )
        df = df[allowed].copy()
        dimension_columns = [c for c in allowed if c in dimension_columns]
        numeric_columns = [c for c in allowed if c in numeric_columns]

    return df, dimension_columns, numeric_columns, path_column


def aggregate_level(
    df: pd.DataFrame,
    dim_columns: list[str],
    numeric_columns: list[str],
    path: list[str],
    level: int | None = None,
) -> list[tuple[str, dict[str, float]]]:
    """
    For the current path (filter), group by the dimension at level and sum numerics.
    Returns list of (dim_value, {num_col: sum, ...}).
    If level is given and level > len(path), filters only by path[0:len(path)]
    (so the next dimension is shown for the whole current path, skipping path-segment drill).
    """
    if level is None:
        level = len(path)
    if level >= len(dim_columns):
        return []
    dim_col = dim_columns[level]
    # Filter by path (only the path elements we have)
    subset = df
    for i in range(min(level, len(path))):
        v = path[i]
        subset = subset[subset[dim_columns[i]].astype(str) == str(v)]
    if subset.empty:
        return []
    grouped = subset.groupby(dim_col, dropna=False)
    if numeric_columns:
        numeric_agg = grouped[numeric_columns].sum()
        result = [
            (str(k) if pd.notna(k) else "", row.to_dict())
            for k, row in numeric_agg.iterrows()
        ]
    else:
        # No numeric columns: use row count as the aggregate (synthetic "count" = 1 per row)
        result = [
            (str(k) if pd.notna(k) else "", {"count": len(g)})
            for k, g in grouped
        ]
    return result
