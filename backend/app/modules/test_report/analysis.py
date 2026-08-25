"""Deterministic data analysis for tabular engineering measurements.

Pure functions over a pandas DataFrame: descriptive statistics, z-score based
anomaly detection, and matplotlib chart rendering to base64 PNG. No AI here —
this is the *evidence* the AI narrative is grounded in.
"""

from __future__ import annotations

import base64
import io

import matplotlib

matplotlib.use("Agg")  # headless rendering — must precede pyplot import
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from app.modules.test_report.schemas import (  # noqa: E402
    Anomaly,
    ChartArtifact,
    ColumnStat,
)

MAX_CHARTS = 4
ZSCORE_THRESHOLD = 3.0


def load_dataframe(extension: str, data: bytes) -> pd.DataFrame:
    """Parse raw bytes into a DataFrame based on file extension."""
    buffer = io.BytesIO(data)
    if extension == ".csv":
        return pd.read_csv(buffer)
    if extension == ".xlsx":
        return pd.read_excel(buffer)
    raise ValueError(f"Test Report Agent cannot tabularize '{extension}' files.")


def compute_statistics(df: pd.DataFrame) -> list[ColumnStat]:
    stats: list[ColumnStat] = []
    for col in df.columns:
        series = df[col]
        numeric = pd.to_numeric(series, errors="coerce")
        if numeric.notna().any():
            stats.append(
                ColumnStat(
                    name=str(col),
                    count=int(numeric.notna().sum()),
                    mean=_finite(numeric.mean()),
                    std=_finite(numeric.std()),
                    minimum=_finite(numeric.min()),
                    maximum=_finite(numeric.max()),
                    missing=int(numeric.isna().sum()),
                )
            )
        else:
            stats.append(
                ColumnStat(
                    name=str(col),
                    count=int(series.notna().sum()),
                    missing=int(series.isna().sum()),
                )
            )
    return stats


def detect_anomalies(df: pd.DataFrame) -> list[Anomaly]:
    """Flag outliers using a z-score threshold on numeric columns."""
    anomalies: list[Anomaly] = []
    for col in df.columns:
        numeric = pd.to_numeric(df[col], errors="coerce")
        if numeric.notna().sum() < 3:
            continue
        std = numeric.std()
        if not std or np.isnan(std):
            continue
        z = (numeric - numeric.mean()) / std
        outliers = z.abs() > ZSCORE_THRESHOLD
        n = int(outliers.sum())
        if n:
            severity = "high" if n > 0.05 * len(numeric) else "medium" if n > 2 else "low"
            anomalies.append(
                Anomaly(
                    column=str(col),
                    description=(
                        f"{n} outlier value(s) exceed ±{ZSCORE_THRESHOLD}σ "
                        f"(mean={numeric.mean():.3g}, std={std:.3g})."
                    ),
                    severity=severity,
                    sample_indices=[int(i) for i in numeric.index[outliers][:10]],
                )
            )
    return anomalies


def render_charts(df: pd.DataFrame) -> list[ChartArtifact]:
    numeric_df = df.apply(pd.to_numeric, errors="coerce").dropna(axis=1, how="all")
    numeric_cols = list(numeric_df.columns)[:MAX_CHARTS]
    charts: list[ChartArtifact] = []

    for col in numeric_cols:
        series = numeric_df[col].dropna()
        if series.empty:
            continue
        fig, ax = plt.subplots(figsize=(6, 3.2), dpi=120)
        ax.plot(series.index, series.values, color="#00E5FF", linewidth=1.4)
        ax.set_title(f"{col} — trend", color="#e5e7eb")
        _style_axes(ax)
        charts.append(
            ChartArtifact(title=f"{col} trend", kind="line", image_base64=_fig_to_b64(fig))
        )

    if len(numeric_cols) >= 2:
        corr = numeric_df[numeric_cols].corr()
        fig, ax = plt.subplots(figsize=(5, 4), dpi=120)
        im = ax.imshow(corr.values, cmap="viridis", vmin=-1, vmax=1)
        ax.set_xticks(range(len(numeric_cols)))
        ax.set_yticks(range(len(numeric_cols)))
        ax.set_xticklabels(numeric_cols, rotation=45, ha="right", color="#e5e7eb")
        ax.set_yticklabels(numeric_cols, color="#e5e7eb")
        ax.set_title("Correlation matrix", color="#e5e7eb")
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        charts.append(
            ChartArtifact(
                title="Correlation matrix", kind="correlation", image_base64=_fig_to_b64(fig)
            )
        )

    return charts


# --- helpers ---------------------------------------------------------------
def _finite(value: object) -> float | None:
    try:
        f = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return None if np.isnan(f) or np.isinf(f) else f


def _style_axes(ax) -> None:
    ax.set_facecolor("#0a0a0a")
    ax.figure.set_facecolor("#040404")
    ax.tick_params(colors="#9ca3af")
    for spine in ax.spines.values():
        spine.set_color("#1f2937")
    ax.grid(True, color="#111827", linewidth=0.5)


def _fig_to_b64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("ascii")
