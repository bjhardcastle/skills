# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "matplotlib>=3.10.0",
#     "polars>=1.26.0",
# ]
# ///
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import polars as pl
from cycler import cycler


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
    ALLEN["blue"],
    ALLEN["orange"],
    ALLEN["teal"],
    ALLEN["violet"],
    ALLEN["green"],
    ALLEN["rose"],
    ALLEN["maroon"],
    ALLEN["ochre"],
    ALLEN["yellow"],
]
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


def apply_allen_style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": ALLEN["page1"],
            "axes.facecolor": ALLEN["white"],
            "axes.edgecolor": ALLEN["black"],
            "axes.labelcolor": ALLEN["black"],
            "axes.prop_cycle": cycler(color=ALLEN_SERIES),
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.titlelocation": "left",
            "font.family": [
                "Allen Institute Text",
                "Helvetica Neue",
                "Arial",
                "sans-serif",
            ],
            "grid.color": ALLEN["page2"],
            "grid.linewidth": 0.9,
            "savefig.facecolor": ALLEN["page1"],
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


def format_axis(ax: plt.Axes, x: list[int], weekdays: list[str]) -> None:
    ax.set_xticks(x)
    ax.set_xticklabels([day.lower() for day in weekdays], fontsize=9)
    ax.tick_params(axis="both", which="major", labelsize=9, length=0, pad=5)
    ax.grid(axis="y")
    ax.set_axisbelow(True)
    ax.spines["bottom"].set_color(ALLEN["black"])
    ax.spines["left"].set_color(ALLEN["black"])


def add_line_plot(
    ax: plt.Axes,
    x: list[int],
    mean: list[float],
    sem: list[float],
    color: str,
    label: str,
) -> None:
    ax.errorbar(
        x,
        mean,
        yerr=sem,
        color=color,
        ecolor=ALLEN["gray1"],
        elinewidth=1.1,
        capsize=3,
        linewidth=2.4,
        marker="o",
        markersize=5.5,
        markerfacecolor=ALLEN["white"],
        markeredgecolor=color,
        markeredgewidth=1.8,
    )
    ax.annotate(
        label,
        xy=(x[-1], mean[-1]),
        xytext=(8, 0),
        textcoords="offset points",
        ha="left",
        va="center",
        fontsize=9.5,
        fontweight="bold",
        color=color,
        clip_on=False,
    )
    ax.margins(x=0.16, y=0.18)


def add_bar_plot(
    ax: plt.Axes,
    x: list[int],
    mean: list[float],
    sem: list[float],
    color: str,
) -> None:
    ax.bar(
        x,
        mean,
        yerr=sem,
        color=color,
        edgecolor=ALLEN["black"],
        linewidth=0.7,
        error_kw={
            "ecolor": ALLEN["gray2"],
            "elinewidth": 1.1,
            "capsize": 3,
            "capthick": 1.1,
        },
        width=0.68,
        alpha=0.92,
    )
    ax.margins(x=0.08, y=0.18)


def make_plot(summary: pl.DataFrame) -> None:
    apply_allen_style()

    x = list(range(summary.height))
    weekdays = summary["weekday"].to_list()
    n_sessions = int(summary["n_sessions"].sum())

    fig, axes = plt.subplots(2, 2, figsize=(9.8, 7.2))
    fig.subplots_adjust(
        left=0.085,
        right=0.95,
        bottom=0.1,
        top=0.81,
        hspace=0.48,
        wspace=0.32,
    )
    fig.suptitle(
        "allen institute/dynamic routing behavior",
        x=0.085,
        y=0.965,
        ha="left",
        fontsize=20,
        fontweight="bold",
    )
    fig.text(
        0.085,
        0.916,
        f"weekday performance summary across {n_sessions:,} sessions",
        ha="left",
        fontsize=10.5,
        color=ALLEN["gray2"],
    )

    for ax, (metric, plot_type) in zip(axes.flat, PLOTS, strict=True):
        mean = summary[f"{metric}_mean"].to_list()
        sem = summary[f"{metric}_sem"].fill_null(0).to_list()
        color = METRIC_COLORS[metric]
        label = METRIC_LABELS[metric]

        if plot_type == "line":
            add_line_plot(ax, x, mean, sem, color, label)
        else:
            add_bar_plot(ax, x, mean, sem, color)

        format_axis(ax, x, weekdays)
        ax.set_title(f"{label}/", fontsize=12, fontweight="bold", pad=12)
        ax.set_ylabel("mean +/- SEM", fontsize=9.5)

    fig.text(
        0.085,
        0.035,
        "source: dynamic routing performance parquet",
        ha="left",
        fontsize=8.5,
        color=ALLEN["gray2"],
    )
    fig.savefig(FIGURE_PATH, dpi=180, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    sessions = load_session_summary()
    summary = summarize_by_weekday(sessions)
    make_plot(summary)
    print(f"wrote {FIGURE_PATH}")


if __name__ == "__main__":
    main()
