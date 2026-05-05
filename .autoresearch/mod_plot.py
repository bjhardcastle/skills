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
from matplotlib import font_manager
from matplotlib.lines import Line2D


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
    for key in (
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


def apply_allen_style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": ALLEN["white"],
            "axes.facecolor": ALLEN["white"],
            "axes.edgecolor": ALLEN["black"],
            "axes.labelcolor": ALLEN["black"],
            "axes.linewidth": 0.9,
            "axes.prop_cycle": cycler(color=ALLEN_SERIES),
            "font.family": resolve_font(),
            "font.size": 10,
            "grid.color": ALLEN["page2"],
            "grid.linewidth": 0.8,
            "legend.frameon": False,
            "savefig.facecolor": ALLEN["white"],
            "savefig.bbox": "tight",
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


def style_axis(ax: plt.Axes, metric: str, weekdays: list[str]) -> None:
    ax.set_title(
        f"{METRIC_LABELS[metric]}/",
        loc="left",
        fontsize=11,
        fontweight="bold",
        pad=12,
    )
    ax.set_xticks(range(len(weekdays)))
    ax.set_xticklabels([weekday.lower() for weekday in weekdays])
    ax.set_ylabel("mean +/- SEM", fontsize=9.5)
    ax.grid(axis="y")
    ax.grid(axis="x", visible=False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(ALLEN["gray1"])
    ax.spines["bottom"].set_color(ALLEN["gray1"])
    ax.tick_params(axis="both", length=3, width=0.8, labelsize=8.5)


def make_plot(summary: pl.DataFrame) -> None:
    apply_allen_style()

    x = list(range(summary.height))
    weekdays = summary["weekday"].to_list()
    fig, axes = plt.subplots(2, 2, figsize=(8, 6), sharex=True)
    fig.subplots_adjust(
        left=0.11,
        right=0.98,
        bottom=0.13,
        top=0.81,
        hspace=0.42,
        wspace=0.30,
    )

    fig.suptitle(
        "allen institute/dynamic routing",
        x=0.11,
        y=0.97,
        ha="left",
        fontsize=18,
        fontweight="bold",
    )
    fig.text(
        0.11,
        0.925,
        "behavior performance by weekday",
        ha="left",
        fontsize=10.5,
        color=ALLEN["gray2"],
    )
    fig.text(
        0.98,
        0.925,
        f"{int(summary['n_sessions'].sum())} sessions",
        ha="right",
        fontsize=10.5,
        color=ALLEN["gray2"],
    )
    fig.supxlabel("weekday", x=0.545, y=0.045, fontsize=10.5)

    for ax, (metric, plot_type) in zip(axes.flat, PLOTS, strict=True):
        means = summary[f"{metric}_mean"].to_list()
        sems = summary[f"{metric}_sem"].fill_null(0).to_list()
        color = METRIC_COLORS[metric]

        if plot_type == "line":
            ax.errorbar(
                x,
                means,
                yerr=sems,
                color=color,
                ecolor=ALLEN["gray1"],
                elinewidth=1.0,
                capsize=3,
                linewidth=2.1,
                marker="o",
                markersize=5.5,
                markerfacecolor=ALLEN["white"],
                markeredgecolor=color,
                markeredgewidth=1.5,
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
                    "elinewidth": 1.0,
                    "capsize": 3,
                    "capthick": 1.0,
                },
                width=0.64,
            )

        style_axis(ax, metric, weekdays)

    fig.add_artist(
        Line2D(
            [0.11, 0.98],
            [0.475, 0.475],
            transform=fig.transFigure,
            color=ALLEN["page2"],
            lw=0.8,
        )
    )
    fig.add_artist(
        Line2D(
            [0.545, 0.545],
            [0.13, 0.81],
            transform=fig.transFigure,
            color=ALLEN["page2"],
            lw=0.8,
        )
    )

    fig.savefig(FIGURE_PATH, dpi=200)
    plt.close(fig)


def main() -> None:
    sessions = load_session_summary()
    summary = summarize_by_weekday(sessions)
    make_plot(summary)
    print(f"wrote {FIGURE_PATH}")


if __name__ == "__main__":
    main()
