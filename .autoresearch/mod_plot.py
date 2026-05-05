# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "matplotlib>=3.10.0",
#     "polars>=1.26.0",
# ]
# ///
from __future__ import annotations

from math import isfinite
from pathlib import Path

import matplotlib.pyplot as plt
import polars as pl
from cycler import cycler
from matplotlib import font_manager
from matplotlib.lines import Line2D


SOURCE = Path(
    r"\\allen\programs\mindscope\workgroups\dynamicrouting\ben\behavior_tables\performance.parquet"
)
OUT_DIR = Path(__file__).resolve().parent
FIGURE_PATH = OUT_DIR / "plot.png"

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

PLOTS = (
    ("hit_rate", "line"),
    ("false_alarm_rate", "line"),
    ("vis_dprime", "bar"),
    ("aud_dprime", "bar"),
)
METRICS = tuple(metric for metric, _ in PLOTS)
METRIC_LABELS = {
    "hit_rate": "hit rate",
    "false_alarm_rate": "false alarm rate",
    "vis_dprime": "visual d-prime",
    "aud_dprime": "auditory d-prime",
}
METRIC_COLORS = {
    "hit_rate": ALLEN["blue"],
    "false_alarm_rate": ALLEN["orange"],
    "vis_dprime": ALLEN["teal"],
    "aud_dprime": ALLEN["violet"],
}


def resolve_font() -> str:
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


plt.rcParams.update(
    {
        "figure.facecolor": ALLEN["white"],
        "axes.facecolor": ALLEN["white"],
        "axes.edgecolor": ALLEN["black"],
        "axes.labelcolor": ALLEN["black"],
        "axes.prop_cycle": cycler(color=ALLEN_SERIES),
        "font.family": resolve_font(),
        "grid.color": ALLEN["page2"],
        "grid.linewidth": 0.9,
        "savefig.facecolor": ALLEN["white"],
        "text.color": ALLEN["black"],
        "xtick.color": ALLEN["gray2"],
        "ytick.color": ALLEN["gray2"],
    }
)


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
                (pl.col(f"{metric}_sd") / pl.col(f"{metric}_n").sqrt()).alias(
                    f"{metric}_sem"
                )
                for metric in METRICS
            ]
        )
        .sort("weekday_num")
    )
    return summary


def clean_values(values: list[float | None], *, null_value: float) -> list[float]:
    return [null_value if value is None else float(value) for value in values]


def set_metric_limits(ax: plt.Axes, metric: str, means: list[float], sems: list[float]) -> None:
    if metric in {"hit_rate", "false_alarm_rate"}:
        ax.set_ylim(0, 1)
        return

    lows = [mean - sem for mean, sem in zip(means, sems, strict=True)]
    highs = [mean + sem for mean, sem in zip(means, sems, strict=True)]
    finite_lows = [value for value in lows if isfinite(value)]
    finite_highs = [value for value in highs if isfinite(value)]
    if not finite_lows or not finite_highs:
        return

    lower = min(0, min(finite_lows))
    upper = max(finite_highs)
    pad = max((upper - lower) * 0.15, 0.2)
    ax.set_ylim(lower - pad, upper + pad)


def style_axis(ax: plt.Axes, metric: str, x: list[int], weekdays: list[str]) -> None:
    ax.set_title(METRIC_LABELS[metric], loc="left", fontsize=12, fontweight="bold", pad=12)
    ax.set_ylabel("session mean", fontsize=9.5, labelpad=8)
    ax.set_xticks(x, weekdays)
    ax.grid(axis="y")
    ax.grid(axis="x", visible=False)
    ax.tick_params(axis="both", labelsize=9, length=0)

    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(ALLEN["black"])
    ax.spines["bottom"].set_color(ALLEN["black"])


def make_plot(summary: pl.DataFrame) -> None:
    x = list(range(summary.height))
    weekdays = [weekday.lower() for weekday in summary["weekday"].to_list()]
    fig, axes = plt.subplots(2, 2, figsize=(9.4, 6.8), sharex=True)
    fig.subplots_adjust(
        left=0.10,
        right=0.98,
        bottom=0.12,
        top=0.78,
        hspace=0.48,
        wspace=0.32,
    )
    fig.suptitle(
        "dynamic routing/weekday behavior",
        x=0.10,
        y=0.96,
        ha="left",
        fontsize=20,
        fontweight="bold",
    )
    fig.text(
        0.10,
        0.905,
        "session mean +/- SEM across behavior sessions",
        ha="left",
        fontsize=10.5,
        color=ALLEN["gray2"],
    )
    fig.add_artist(
        Line2D(
            [0.10, 0.98],
            [0.835, 0.835],
            transform=fig.transFigure,
            color=ALLEN["blue"],
            linewidth=2.5,
            solid_capstyle="butt",
        )
    )

    for ax, (metric, plot_type) in zip(axes.flat, PLOTS, strict=True):
        means = clean_values(summary[f"{metric}_mean"].to_list(), null_value=float("nan"))
        sems = clean_values(summary[f"{metric}_sem"].to_list(), null_value=0)
        color = METRIC_COLORS[metric]

        if plot_type == "line":
            ax.errorbar(
                x,
                means,
                yerr=sems,
                color=color,
                marker="o",
                markersize=5.5,
                markerfacecolor=ALLEN["white"],
                markeredgecolor=color,
                markeredgewidth=1.5,
                linewidth=2.4,
                elinewidth=1.3,
                capsize=3,
            )
        else:
            ax.bar(
                x,
                means,
                yerr=sems,
                color=color,
                edgecolor=ALLEN["black"],
                linewidth=0.8,
                error_kw={
                    "ecolor": ALLEN["black"],
                    "elinewidth": 1.2,
                    "capsize": 3,
                    "capthick": 1.2,
                },
            )

        set_metric_limits(ax, metric, means, sems)
        style_axis(ax, metric, x, weekdays)

    for ax in axes[0, :]:
        ax.tick_params(axis="x", labelbottom=False)
    for ax in axes[1, :]:
        ax.set_xlabel("weekday", fontsize=9.5, labelpad=8)

    fig.savefig(FIGURE_PATH, dpi=180, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    sessions = load_session_summary()
    summary = summarize_by_weekday(sessions)
    make_plot(summary)
    print(f"wrote {FIGURE_PATH}")


if __name__ == "__main__":
    main()
