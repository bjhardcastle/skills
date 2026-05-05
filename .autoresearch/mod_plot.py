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
METRIC_STYLES = {
    "hit_rate": {
        "title": "hit rate/",
        "ylabel": "rate",
        "color": ALLEN["blue"],
        "ylim": (0, 1),
    },
    "false_alarm_rate": {
        "title": "false alarm rate/",
        "ylabel": "rate",
        "color": ALLEN["orange"],
        "ylim": (0, 1),
    },
    "vis_dprime": {
        "title": "visual d-prime/",
        "ylabel": "d-prime",
        "color": ALLEN["teal"],
        "ylim": None,
    },
    "aud_dprime": {
        "title": "auditory d-prime/",
        "ylabel": "d-prime",
        "color": ALLEN["violet"],
        "ylim": None,
    },
}


def resolve_font(candidates: list[str]) -> str:
    installed_fonts = {font.name for font in font_manager.fontManager.ttflist}
    return next((font for font in candidates if font in installed_fonts), "DejaVu Sans")


TITLE_FONT = resolve_font(
    [
        "Allen Institute Headline",
        "Allen Institute",
        "Bahnschrift",
        "Segoe UI",
        "Arial",
        "Calibri",
        "DejaVu Sans",
    ]
)
TEXT_FONT = resolve_font(
    [
        "Allen Institute Text",
        "Allen Institute",
        "Arial",
        "Segoe UI",
        "Calibri",
        "DejaVu Sans",
    ]
)


plt.rcParams.update(
    {
        "figure.facecolor": ALLEN["white"],
        "axes.facecolor": ALLEN["white"],
        "axes.edgecolor": ALLEN["black"],
        "axes.labelcolor": ALLEN["black"],
        "axes.linewidth": 0.9,
        "xtick.color": ALLEN["gray2"],
        "ytick.color": ALLEN["gray2"],
        "grid.color": ALLEN["page2"],
        "grid.linewidth": 0.8,
        "text.color": ALLEN["black"],
        "font.family": TEXT_FONT,
        "axes.prop_cycle": cycler(color=ALLEN_SERIES),
        "savefig.facecolor": ALLEN["white"],
        "savefig.bbox": "tight",
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


def format_metric_label(metric: str) -> str:
    return metric.replace("_", " ")


def add_header(fig: plt.Figure, summary: pl.DataFrame) -> None:
    session_total = int(summary["n_sessions"].sum())
    weekday_total = summary.height
    fig.suptitle(
        "allen institute/dynamic routing",
        x=0.08,
        y=0.975,
        ha="left",
        va="top",
        fontsize=20,
        fontweight="bold",
        fontfamily=TITLE_FONT,
    )
    fig.text(
        0.08,
        0.925,
        f"weekday performance summary / {weekday_total} weekdays / {session_total:,} sessions",
        ha="left",
        va="top",
        fontsize=10.5,
        color=ALLEN["gray2"],
        fontfamily=TEXT_FONT,
    )


def style_axis(ax: plt.Axes, metric: str, weekdays: list[str]) -> None:
    style = METRIC_STYLES[metric]
    ax.set_title(
        style["title"],
        loc="left",
        fontsize=12,
        fontweight="bold",
        pad=12,
        fontfamily=TITLE_FONT,
    )
    ax.set_ylabel(style["ylabel"], fontsize=9.5, labelpad=7)
    ax.set_xticks(range(len(weekdays)), weekdays)
    ax.tick_params(axis="x", labelsize=8.5, length=0, pad=6)
    ax.tick_params(axis="y", labelsize=8.5, length=0)
    ax.grid(axis="y", alpha=1.0)
    ax.grid(axis="x", visible=False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(ALLEN["black"])
    ax.spines["bottom"].set_color(ALLEN["black"])
    if style["ylim"] is not None:
        ax.set_ylim(style["ylim"])
    else:
        ax.margins(y=0.18)


def add_weekday_counts(fig: plt.Figure, summary: pl.DataFrame) -> None:
    counts = " / ".join(
        f"{weekday.lower()} {n_sessions}"
        for weekday, n_sessions in zip(
            summary["weekday"].to_list(),
            summary["n_sessions"].to_list(),
            strict=True,
        )
    )
    fig.text(
        0.08,
        0.035,
        f"sessions per weekday / {counts}",
        ha="left",
        va="bottom",
        fontsize=8.5,
        color=ALLEN["gray2"],
        fontfamily=TEXT_FONT,
    )


def make_plot(summary: pl.DataFrame) -> None:
    x = list(range(summary.height))
    weekdays = [weekday.lower() for weekday in summary["weekday"].to_list()]
    fig, axes = plt.subplots(2, 2, figsize=(9.2, 6.8), dpi=180)
    fig.subplots_adjust(
        left=0.08,
        right=0.985,
        bottom=0.13,
        top=0.82,
        hspace=0.55,
        wspace=0.34,
    )
    add_header(fig, summary)

    for ax, (metric, plot_type) in zip(axes.flat, PLOTS, strict=True):
        style = METRIC_STYLES[metric]
        color = style["color"]
        means = summary[f"{metric}_mean"].to_list()
        sems = summary[f"{metric}_sem"].fill_null(0).to_list()
        if plot_type == "line":
            ax.errorbar(
                x,
                means,
                yerr=sems,
                color=color,
                linewidth=2.25,
                marker="o",
                markersize=5,
                markerfacecolor=ALLEN["white"],
                markeredgecolor=color,
                markeredgewidth=1.5,
                ecolor=ALLEN["gray1"],
                elinewidth=1,
                capsize=3,
                zorder=3,
            )
        else:
            ax.bar(
                x,
                means,
                yerr=sems,
                color=color,
                edgecolor=ALLEN["black"],
                linewidth=0.6,
                error_kw={
                    "ecolor": ALLEN["gray2"],
                    "elinewidth": 1,
                    "capsize": 3,
                    "capthick": 1,
                },
                zorder=3,
            )
        style_axis(ax, metric, weekdays)

    axes[0, 1].tick_params(axis="y", labelleft=False)
    axes[0, 1].set_ylabel("")
    axes[1, 1].tick_params(axis="y", labelleft=False)
    axes[1, 1].set_ylabel("")
    add_weekday_counts(fig, summary)
    fig.savefig(FIGURE_PATH)
    plt.close(fig)


def main() -> None:
    sessions = load_session_summary()
    summary = summarize_by_weekday(sessions)
    make_plot(summary)
    print(f"wrote {FIGURE_PATH}")


if __name__ == "__main__":
    main()
