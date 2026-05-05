# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "matplotlib>=3.10.0",
#     "polars>=1.26.0",
# ]
# ///
from __future__ import annotations

from pathlib import Path

import matplotlib.font_manager as font_manager
import matplotlib.pyplot as plt
import polars as pl
from cycler import cycler


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
    ALLEN[color]
    for color in (
        "blue",
        "orange",
        "teal",
        "violet",
        "green",
        "rose",
        "maroon",
        "ochre",
        "yellow",
    )
]

PLOTS = (
    ("hit_rate", "line"),
    ("false_alarm_rate", "line"),
    ("vis_dprime", "bar"),
    ("aud_dprime", "bar"),
)
METRICS = tuple(metric for metric, _ in PLOTS)
PANEL_LABELS = {
    "hit_rate": "hit rate/",
    "false_alarm_rate": "false alarm rate/",
    "vis_dprime": "visual d-prime/",
    "aud_dprime": "auditory d-prime/",
}
Y_LABELS = {
    "hit_rate": "rate",
    "false_alarm_rate": "rate",
    "vis_dprime": "d-prime",
    "aud_dprime": "d-prime",
}
PLOT_COLORS = {
    "hit_rate": ALLEN["blue"],
    "false_alarm_rate": ALLEN["teal"],
    "vis_dprime": ALLEN["orange"],
    "aud_dprime": ALLEN["violet"],
}


def preferred_font() -> str:
    installed = {font.name for font in font_manager.fontManager.ttflist}
    for family in (
        "Allen Institute Text",
        "Allen Institute",
        "Helvetica Neue",
        "Arial",
        "DejaVu Sans",
    ):
        if family in installed:
            return family
    return "sans-serif"


plt.rcParams.update(
    {
        "figure.facecolor": ALLEN["page1"],
        "savefig.facecolor": ALLEN["page1"],
        "axes.facecolor": ALLEN["white"],
        "axes.edgecolor": ALLEN["black"],
        "axes.labelcolor": ALLEN["black"],
        "axes.prop_cycle": cycler(color=ALLEN_SERIES),
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.titleweight": "bold",
        "axes.grid": True,
        "grid.color": ALLEN["page2"],
        "grid.linewidth": 0.9,
        "xtick.color": ALLEN["gray2"],
        "ytick.color": ALLEN["gray2"],
        "text.color": ALLEN["black"],
        "font.family": preferred_font(),
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
                (pl.col(f"{metric}_sd") / pl.col(f"{metric}_n").sqrt())
                .fill_null(0)
                .alias(f"{metric}_sem")
                for metric in METRICS
            ]
        )
        .sort("weekday_num")
    )
    return summary


def float_values(values: list[float | None], default: float) -> list[float]:
    return [default if value is None else float(value) for value in values]


def set_y_limits(
    ax: plt.Axes,
    metric: str,
    means: list[float],
    sems: list[float],
) -> None:
    finite_lows = [
        mean - sem
        for mean, sem in zip(means, sems, strict=True)
        if mean == mean and sem == sem
    ]
    finite_highs = [
        mean + sem
        for mean, sem in zip(means, sems, strict=True)
        if mean == mean and sem == sem
    ]
    if not finite_highs:
        return

    if metric.endswith("_rate"):
        ax.set_ylim(0, min(1.05, max(1.0, max(finite_highs) * 1.08)))
        return

    low = min(0.0, min(finite_lows))
    high = max(finite_highs)
    padding = max((high - low) * 0.16, 0.25)
    ax.set_ylim(low - padding * 0.25, high + padding)


def style_axis(ax: plt.Axes, metric: str, show_x_labels: bool) -> None:
    ax.set_title(PANEL_LABELS[metric], loc="left", fontsize=11, pad=12)
    ax.set_ylabel(Y_LABELS[metric], fontsize=9)
    ax.tick_params(axis="both", labelsize=8, length=0)
    ax.tick_params(axis="x", labelbottom=show_x_labels)
    ax.grid(axis="y")
    ax.grid(axis="x", visible=False)
    ax.spines["left"].set_color(ALLEN["black"])
    ax.spines["bottom"].set_color(ALLEN["black"])
    ax.spines["left"].set_linewidth(0.9)
    ax.spines["bottom"].set_linewidth(0.9)


def make_plot(summary: pl.DataFrame) -> None:
    x = list(range(summary.height))
    weekdays = [str(day).lower() for day in summary["weekday"].to_list()]
    fig, axes = plt.subplots(2, 2, figsize=(9.2, 6.8), constrained_layout=False)
    fig.subplots_adjust(
        left=0.09,
        right=0.91,
        bottom=0.12,
        top=0.78,
        hspace=0.48,
        wspace=0.32,
    )

    fig.suptitle(
        "allen institute/dynamic routing performance",
        x=0.09,
        y=0.965,
        ha="left",
        fontsize=19,
        fontweight="bold",
    )
    fig.text(
        0.09,
        0.91,
        "weekday session summary; markers and bars show mean +/- sem",
        ha="left",
        fontsize=10.5,
        color=ALLEN["gray2"],
    )
    fig.text(
        0.91,
        0.94,
        "behavior tables/",
        ha="right",
        va="top",
        fontsize=9,
        color=ALLEN["gray2"],
        fontweight="bold",
    )
    fig.add_artist(
        plt.Line2D(
            [0.09, 0.91],
            [0.86, 0.86],
            transform=fig.transFigure,
            color=ALLEN["black"],
            linewidth=1.1,
        )
    )
    fig.add_artist(
        plt.Line2D(
            [0.09, 0.30],
            [0.855, 0.855],
            transform=fig.transFigure,
            color=ALLEN["orange"],
            linewidth=4.0,
            solid_capstyle="butt",
        )
    )

    for index, (ax, (metric, plot_type)) in enumerate(
        zip(axes.flat, PLOTS, strict=True)
    ):
        means = float_values(summary[f"{metric}_mean"].to_list(), float("nan"))
        sems = float_values(summary[f"{metric}_sem"].to_list(), 0.0)
        color = PLOT_COLORS[metric]

        if plot_type == "line":
            ax.errorbar(
                x,
                means,
                yerr=sems,
                color=color,
                ecolor=ALLEN["gray2"],
                elinewidth=1,
                capsize=3,
                fmt="-o",
                linewidth=2.4,
                markersize=5,
                markerfacecolor=ALLEN["white"],
                markeredgecolor=color,
                markeredgewidth=1.8,
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
                    "ecolor": ALLEN["gray2"],
                    "elinewidth": 1,
                    "capsize": 3,
                    "capthick": 1,
                },
            )

        ax.set_xticks(x, weekdays)
        style_axis(ax, metric, show_x_labels=index >= 2)
        set_y_limits(ax, metric, means, sems)

    fig.text(
        0.09,
        0.045,
        "source: performance.parquet / grouped by weekday from parsed session dates",
        ha="left",
        fontsize=8.5,
        color=ALLEN["gray2"],
    )
    fig.savefig(FIGURE_PATH, dpi=200, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    sessions = load_session_summary()
    summary = summarize_by_weekday(sessions)
    make_plot(summary)
    print(f"wrote {FIGURE_PATH}")


if __name__ == "__main__":
    main()
