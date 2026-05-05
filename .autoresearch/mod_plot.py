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
import polars as pl
from cycler import cycler
from matplotlib import font_manager
from matplotlib.ticker import MaxNLocator, PercentFormatter


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
INSTALLED_FONTS = {font.name for font in font_manager.fontManager.ttflist}
ALLEN_FONT = next(
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
        if font in INSTALLED_FONTS
    ),
    "DejaVu Sans",
)

PLOTS = (
    ("hit_rate", "line", ALLEN["blue"]),
    ("false_alarm_rate", "line", ALLEN["orange"]),
    ("vis_dprime", "bar", ALLEN["teal"]),
    ("aud_dprime", "bar", ALLEN["violet"]),
)
METRICS = tuple(metric for metric, _, _ in PLOTS)
METRIC_LABELS = {
    "hit_rate": "hit rate",
    "false_alarm_rate": "false alarm rate",
    "vis_dprime": "visual d-prime",
    "aud_dprime": "auditory d-prime",
}


def apply_allen_style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": ALLEN["white"],
            "axes.facecolor": ALLEN["white"],
            "axes.edgecolor": ALLEN["black"],
            "axes.labelcolor": ALLEN["black"],
            "xtick.color": ALLEN["gray2"],
            "ytick.color": ALLEN["gray2"],
            "grid.color": ALLEN["page2"],
            "text.color": ALLEN["black"],
            "axes.prop_cycle": cycler(color=ALLEN_SERIES),
            "font.family": ALLEN_FONT,
            "font.size": 9.5,
            "savefig.facecolor": ALLEN["white"],
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


def clean_values(values: list[float | None]) -> list[float]:
    cleaned = []
    for value in values:
        if value is None:
            cleaned.append(0.0)
            continue

        number = float(value)
        cleaned.append(number if math.isfinite(number) else 0.0)
    return cleaned


def style_axis(ax: plt.Axes, plot_type: str) -> None:
    ax.set_axisbelow(True)
    ax.grid(axis="y", color=ALLEN["page2"], linewidth=0.8)
    ax.grid(axis="x", visible=False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(ALLEN["black"])
    ax.spines["bottom"].set_color(ALLEN["black"])
    ax.tick_params(axis="both", colors=ALLEN["gray2"], labelsize=8.5, length=0, pad=5)

    if plot_type == "line":
        ax.set_ylim(0, 1)
        ax.yaxis.set_major_formatter(PercentFormatter(xmax=1.0, decimals=0))
        ax.set_ylabel("mean rate", fontsize=8.5, color=ALLEN["black"])
    else:
        ax.yaxis.set_major_locator(MaxNLocator(nbins=4))
        ax.set_ylabel("mean d-prime", fontsize=8.5, color=ALLEN["black"])


def make_plot(summary: pl.DataFrame) -> None:
    apply_allen_style()

    x = list(range(summary.height))
    weekdays = [str(day).lower() for day in summary["weekday"].to_list()]
    total_sessions = int(summary["n_sessions"].sum())

    fig, axes = plt.subplots(2, 2, figsize=(8.5, 6.2), constrained_layout=False)
    fig.subplots_adjust(
        left=0.10,
        right=0.98,
        bottom=0.14,
        top=0.80,
        hspace=0.56,
        wspace=0.34,
    )
    fig.suptitle(
        "dynamic routing/weekday performance",
        x=0.10,
        y=0.96,
        ha="left",
        fontsize=18,
        fontweight="bold",
    )
    fig.text(
        0.10,
        0.915,
        f"mean session metrics by weekday; error bars show standard error of the mean; n={total_sessions} sessions",
        ha="left",
        fontsize=10,
        color=ALLEN["gray2"],
    )

    for ax, (metric, plot_type, color) in zip(axes.flat, PLOTS, strict=True):
        y = clean_values(summary[f"{metric}_mean"].to_list())
        yerr = clean_values(summary[f"{metric}_sem"].to_list())

        if plot_type == "line":
            ax.errorbar(
                x,
                y,
                yerr=yerr,
                color=color,
                ecolor=ALLEN["gray2"],
                elinewidth=1.1,
                capsize=3,
                capthick=1.1,
                linewidth=2.2,
                marker="o",
                markersize=5.2,
                markerfacecolor=ALLEN["white"],
                markeredgecolor=color,
                markeredgewidth=1.5,
                zorder=3,
            )
        else:
            ax.bar(
                x,
                y,
                yerr=yerr,
                color=color,
                edgecolor=ALLEN["black"],
                error_kw={
                    "ecolor": ALLEN["gray2"],
                    "elinewidth": 1.1,
                    "capsize": 3,
                    "capthick": 1.1,
                },
                linewidth=0.7,
                alpha=0.90,
                width=0.68,
                zorder=3,
            )
            upper = max((value + error for value, error in zip(y, yerr, strict=True)), default=1)
            lower = min((value - error for value, error in zip(y, yerr, strict=True)), default=0)
            ax.set_ylim(min(0, lower * 1.10), max(1, upper * 1.18))

        ax.set_title(
            f"{METRIC_LABELS[metric]}/",
            loc="left",
            fontsize=11,
            fontweight="bold",
            pad=12,
        )
        ax.set_xticks(x, weekdays)
        style_axis(ax, plot_type)

    fig.text(
        0.10,
        0.045,
        "source: allen institute/dynamic routing/behavior_tables/performance.parquet",
        ha="left",
        fontsize=8,
        color=ALLEN["gray2"],
    )
    fig.savefig(FIGURE_PATH, dpi=220, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    sessions = load_session_summary()
    summary = summarize_by_weekday(sessions)
    make_plot(summary)
    print(f"wrote {FIGURE_PATH}")


if __name__ == "__main__":
    main()
