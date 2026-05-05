# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "matplotlib>=3.10.0",
#     "polars>=1.26.0",
# ]
# ///
from __future__ import annotations

import math
from pathlib import Path

import matplotlib.pyplot as plt
from cycler import cycler
from matplotlib import font_manager
from matplotlib.lines import Line2D
from matplotlib.ticker import PercentFormatter
import polars as pl


SOURCE = Path(
    r"\\allen\programs\mindscope\workgroups\dynamicrouting\ben\behavior_tables\performance.parquet"
)
OUT_DIR = Path(__file__).resolve().parent
FIGURE_PATH = OUT_DIR / "plot.png"

PLOTS = (
    ("hit_rate", "line"),
    ("false_alarm_rate", "line"),
    ("vis_dprime", "bar"),
    ("aud_dprime", "bar"),
)
METRICS = tuple(metric for metric, _ in PLOTS)

ALLEN = {
    "black": "#000000",
    "white": "#FFFFFF",
    "page1": "#F3F0E8",
    "page2": "#DED9D1",
    "gray1": "#AAA39F",
    "gray2": "#737373",
    "blue": "#6464FF",
    "orange": "#FF6E00",
    "green": "#CDEB05",
    "rose": "#FF00FF",
    "maroon": "#CD0F55",
    "teal": "#00A59B",
    "violet": "#8246FF",
    "ochre": "#DC9600",
    "yellow": "#FFEB23",
}
ALLEN_SERIES = [
    ALLEN[key]
    for key in ("blue", "orange", "teal", "violet", "green", "rose", "maroon")
]
PANEL_STYLES = {
    "hit_rate": {
        "title": "hit rate",
        "ylabel": "mean hit rate",
        "color": ALLEN["blue"],
    },
    "false_alarm_rate": {
        "title": "false alarm rate",
        "ylabel": "mean false alarm rate",
        "color": ALLEN["orange"],
    },
    "vis_dprime": {
        "title": "visual d-prime",
        "ylabel": "mean d-prime",
        "color": ALLEN["teal"],
    },
    "aud_dprime": {
        "title": "auditory d-prime",
        "ylabel": "mean d-prime",
        "color": ALLEN["violet"],
    },
}


def load_session_summary() -> pl.DataFrame:
    return (
        pl.scan_parquet(SOURCE)
        .with_columns(
            pl.col("session_id")
            .str.extract(r"(\d{4}-\d{2}-\d{2})$", 1)
            .str.strptime(pl.Date, "%Y-%m-%d")
            .alias("session_date")
        )
        .drop_nulls("session_date")
        .group_by("session_id", "session_date")
        .agg(
            pl.col("n_trials").sum().alias("n_trials"),
            pl.col("n_contingent_rewards").sum().alias("n_contingent_rewards"),
            *[pl.col(metric).mean().alias(metric) for metric in METRICS],
        )
        .with_columns(
            pl.col("session_date").dt.weekday().alias("weekday_num"),
            pl.col("session_date").dt.strftime("%a").alias("weekday"),
        )
        .collect()
    )


def summarize_by_weekday(sessions: pl.DataFrame) -> pl.DataFrame:
    summary = (
        sessions.group_by("weekday_num", "weekday")
        .agg(
            pl.len().alias("n_sessions"),
            *[
                expr
                for metric in METRICS
                for expr in (
                    pl.col(metric).mean().alias(f"{metric}_mean"),
                    pl.col(metric).std().alias(f"{metric}_sd"),
                    pl.col(metric).count().alias(f"{metric}_n"),
                )
            ],
        )
        .with_columns(
            *[
                (
                    pl.col(f"{metric}_sd").fill_null(0)
                    / pl.col(f"{metric}_n").sqrt()
                ).alias(f"{metric}_sem")
                for metric in METRICS
            ]
        )
        .sort("weekday_num")
    )
    return summary


def resolve_allen_font() -> str:
    installed_fonts = {font.name for font in font_manager.fontManager.ttflist}
    return next(
        (
            font
            for font in (
                "Allen Institute Text",
                "Allen Institute",
                "Arial",
                "Segoe UI",
                "Bahnschrift",
                "Calibri",
                "DejaVu Sans",
            )
            if font in installed_fonts
        ),
        "DejaVu Sans",
    )


def apply_allen_style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": ALLEN["page1"],
            "savefig.facecolor": ALLEN["page1"],
            "axes.facecolor": ALLEN["white"],
            "axes.edgecolor": ALLEN["black"],
            "axes.labelcolor": ALLEN["black"],
            "axes.axisbelow": True,
            "axes.grid": True,
            "axes.prop_cycle": cycler(color=ALLEN_SERIES),
            "grid.color": ALLEN["page2"],
            "grid.linewidth": 0.85,
            "text.color": ALLEN["black"],
            "xtick.color": ALLEN["gray2"],
            "ytick.color": ALLEN["gray2"],
            "font.family": resolve_allen_font(),
            "font.size": 9.5,
            "axes.titlesize": 11,
            "axes.titleweight": "bold",
            "axes.labelsize": 9.5,
            "xtick.labelsize": 8.5,
            "ytick.labelsize": 8.5,
        }
    )


def clean_values(values: list[float | None], *, fallback: float) -> list[float]:
    cleaned = []
    for value in values:
        number = fallback if value is None else float(value)
        if not math.isfinite(number):
            number = fallback
        cleaned.append(number)
    return cleaned


def style_axis(ax: plt.Axes, metric: str, values: list[float], errors: list[float]) -> None:
    style = PANEL_STYLES[metric]
    ax.set_title(f"{style['title']}/", loc="left", pad=12)
    ax.set_ylabel(style["ylabel"], labelpad=8)
    ax.grid(axis="x", visible=False)
    ax.grid(axis="y", color=ALLEN["page2"], linewidth=0.85)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(ALLEN["black"])
    ax.spines["bottom"].set_color(ALLEN["black"])
    ax.spines["left"].set_linewidth(1.0)
    ax.spines["bottom"].set_linewidth(1.0)
    ax.tick_params(axis="both", length=0, pad=5)

    finite_bounds = [
        (value - error, value + error)
        for value, error in zip(values, errors, strict=True)
        if math.isfinite(value)
    ]
    if metric.endswith("_rate"):
        ax.set_ylim(0, 1)
        ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
        ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
        return
    if not finite_bounds:
        return

    lower = min(0.0, *(bound[0] for bound in finite_bounds))
    upper = max(0.0, *(bound[1] for bound in finite_bounds))
    span = upper - lower
    padding = span * 0.12 if span else 0.5
    ax.set_ylim(lower - padding, upper + padding)


def add_header(fig: plt.Figure, summary: pl.DataFrame) -> None:
    total_sessions = int(summary["n_sessions"].sum() or 0) if summary.height else 0
    fig.suptitle(
        "allen institute/mindscope/dynamic routing",
        x=0.085,
        y=0.965,
        ha="left",
        va="top",
        fontsize=18,
        fontweight="bold",
    )
    fig.text(
        0.085,
        0.918,
        "weekday session performance, mean +/- SEM across sessions",
        ha="left",
        va="top",
        fontsize=10.5,
        color=ALLEN["gray2"],
    )
    fig.text(
        0.975,
        0.964,
        "/",
        ha="right",
        va="top",
        fontsize=28,
        fontweight="bold",
        color=ALLEN["orange"],
    )
    fig.add_artist(
        Line2D(
            [0.085, 0.975],
            [0.865, 0.865],
            transform=fig.transFigure,
            color=ALLEN["page2"],
            linewidth=1.4,
        )
    )
    fig.text(
        0.085,
        0.035,
        f"n = {total_sessions:,} sessions; x-axis grouped by weekday of session date",
        ha="left",
        va="bottom",
        fontsize=8.5,
        color=ALLEN["gray2"],
    )


def make_plot(summary: pl.DataFrame) -> None:
    apply_allen_style()

    x = list(range(summary.height))
    weekdays = summary["weekday"].to_list()
    fig, axes = plt.subplots(2, 2, figsize=(9.6, 7.2), sharex=True)
    fig.subplots_adjust(
        left=0.085,
        right=0.975,
        bottom=0.105,
        top=0.82,
        hspace=0.48,
        wspace=0.34,
    )
    add_header(fig, summary)

    for ax, (metric, plot_type) in zip(axes.flat, PLOTS, strict=True):
        style = PANEL_STYLES[metric]
        values = clean_values(summary[f"{metric}_mean"].to_list(), fallback=math.nan)
        errors = clean_values(summary[f"{metric}_sem"].to_list(), fallback=0.0)
        color = style["color"]

        if plot_type == "line":
            ax.errorbar(
                x,
                values,
                yerr=errors,
                color=color,
                ecolor=ALLEN["gray2"],
                linewidth=2.3,
                elinewidth=1.1,
                capsize=3.5,
                marker="o",
                markersize=5.5,
                markerfacecolor=color,
                markeredgecolor=ALLEN["white"],
                markeredgewidth=1.1,
                zorder=3,
            )
        else:
            ax.bar(
                x,
                values,
                yerr=errors,
                width=0.62,
                color=color,
                edgecolor=ALLEN["black"],
                linewidth=0.75,
                error_kw={
                    "ecolor": ALLEN["gray2"],
                    "elinewidth": 1.1,
                    "capsize": 3.5,
                    "capthick": 1.1,
                },
                zorder=3,
            )

        ax.set_xticks(x, weekdays)
        style_axis(ax, metric, values, errors)

    for ax in axes[0, :]:
        ax.tick_params(axis="x", labelbottom=False)
    for ax in axes[1, :]:
        ax.set_xlabel("weekday", labelpad=8)

    fig.savefig(FIGURE_PATH, dpi=180, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    sessions = load_session_summary()
    summary = summarize_by_weekday(sessions)
    make_plot(summary)
    print(f"wrote {FIGURE_PATH}")


if __name__ == "__main__":
    main()
