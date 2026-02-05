"""CSV loading, column classification, and hierarchical aggregation."""

from __future__ import annotations

from pathlib import Path
from typing import IO

import pandas as pd


def load_and_classify(
    source: str | Path | IO[str],
) -> tuple[pd.DataFrame, list[str], list[str]]:
    """Load CSV from path or file-like and return (df, dimension_columns, numeric_columns)."""
    df = pd.read_csv(source)
    numeric_columns: list[str] = []
    for col in df.columns:
        coerced = pd.to_numeric(df[col], errors="coerce")
        # Column is numeric if it has at least one valid number (and isn't all NaN)
        if coerced.notna().any():
            numeric_columns.append(col)
    # Dimensions = non-numeric, in original column order
    dimension_columns = [c for c in df.columns if c not in numeric_columns]
    return df, dimension_columns, numeric_columns


def aggregate_level(
    df: pd.DataFrame,
    dim_columns: list[str],
    numeric_columns: list[str],
    path: list[str],
) -> list[tuple[str, dict[str, float]]]:
    """
    For the current path (filter), group by the next dimension and sum numerics.
    Returns list of (dim_value, {num_col: sum, ...}).
    """
    level = len(path)
    if level >= len(dim_columns):
        return []
    dim_col = dim_columns[level]
    # Filter by path
    subset = df
    for i, v in enumerate(path):
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
