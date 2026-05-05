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
PLOT_COLORS = {
    "hit_rate": ALLEN["blue"],
    "false_alarm_rate": ALLEN["orange"],
    "vis_dprime": ALLEN["teal"],
    "aud_dprime": ALLEN["violet"],
}
PLOT_TITLES = {
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
FONT_CANDIDATES = (
    "Allen Institute Text",
    "Allen Institute",
    "Helvetica Neue",
    "Arial",
    "DejaVu Sans",
)


def resolve_font_family() -> list[str]:
    available = {font.name for font in font_manager.fontManager.ttflist}
    for font_name in FONT_CANDIDATES:
        if font_name in available:
            return [font_name, "sans-serif"]
    return ["sans-serif"]


plt.rcParams.update(
    {
        "figure.facecolor": ALLEN["page1"],
        "axes.facecolor": ALLEN["white"],
        "axes.edgecolor": ALLEN["black"],
        "axes.labelcolor": ALLEN["black"],
        "axes.prop_cycle": cycler(color=ALLEN_SERIES),
        "axes.titlecolor": ALLEN["black"],
        "font.family": resolve_font_family(),
        "grid.color": ALLEN["page2"],
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


def format_axis(ax: plt.Axes, metric: str, labels: list[str], show_weekdays: bool) -> None:
    ax.set_title(PLOT_TITLES[metric], loc="left", fontsize=12, fontweight="bold", pad=10)
    ax.set_ylabel(Y_LABELS[metric], fontsize=9, labelpad=8)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels if show_weekdays else [])
    ax.tick_params(axis="both", length=0, labelsize=9, pad=6)
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, linewidth=0.9)
    ax.xaxis.grid(False)
    ax.margins(x=0.08)

    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(ALLEN["black"])
        ax.spines[side].set_linewidth(1.2)

    if metric.endswith("_rate"):
        ax.set_ylim(0, 1.05)
    else:
        ax.axhline(0, color=ALLEN["black"], linewidth=1.0)


def make_plot(summary: pl.DataFrame) -> None:
    x = list(range(summary.height))
    labels = [weekday.lower() for weekday in summary["weekday"].to_list()]
    fig, axes = plt.subplots(2, 2, figsize=(9.2, 6.4), constrained_layout=True)
    fig.patch.set_facecolor(ALLEN["page1"])

    fig.suptitle(
        "dynamic routing/performance by weekday",
        x=0.02,
        y=0.995,
        ha="left",
        fontsize=20,
        fontweight="bold",
    )
    fig.text(
        0.02,
        0.94,
        "mean +/- sem across sessions",
        color=ALLEN["gray2"],
        fontsize=10,
        ha="left",
    )

    for index, (ax, (metric, plot_type)) in enumerate(
        zip(axes.flat, PLOTS, strict=True)
    ):
        values = summary[f"{metric}_mean"].to_list()
        errors = summary[f"{metric}_sem"].fill_null(0).to_list()
        color = PLOT_COLORS[metric]

        if plot_type == "line":
            ax.errorbar(
                x,
                values,
                yerr=errors,
                color=color,
                ecolor=ALLEN["gray2"],
                elinewidth=1.0,
                linewidth=2.4,
                marker="o",
                markeredgecolor=ALLEN["black"],
                markeredgewidth=0.7,
                markersize=5.5,
                capsize=3,
            )
        else:
            ax.bar(
                x,
                values,
                yerr=errors,
                color=color,
                edgecolor=ALLEN["black"],
                error_kw={
                    "ecolor": ALLEN["black"],
                    "elinewidth": 1.0,
                    "capsize": 3,
                },
                linewidth=0.8,
                width=0.68,
            )

        format_axis(ax, metric, labels, show_weekdays=index >= 2)

    fig.savefig(FIGURE_PATH, dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def main() -> None:
    sessions = load_session_summary()
    summary = summarize_by_weekday(sessions)
    make_plot(summary)
    print(f"wrote {FIGURE_PATH}")


if __name__ == "__main__":
    main()
