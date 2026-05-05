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
    ("hit_rate", "line", "hit rate/", "rate", ALLEN["blue"]),
    ("false_alarm_rate", "line", "false alarm rate/", "rate", ALLEN["orange"]),
    ("vis_dprime", "bar", "visual d-prime/", "d-prime", ALLEN["teal"]),
    ("aud_dprime", "bar", "auditory d-prime/", "d-prime", ALLEN["violet"]),
)
METRICS = tuple(metric for metric, *_ in PLOTS)


def apply_allen_style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": ALLEN["page1"],
            "axes.facecolor": ALLEN["white"],
            "axes.edgecolor": ALLEN["black"],
            "axes.labelcolor": ALLEN["black"],
            "xtick.color": ALLEN["gray2"],
            "ytick.color": ALLEN["gray2"],
            "grid.color": ALLEN["page2"],
            "text.color": ALLEN["black"],
            "axes.prop_cycle": cycler(color=ALLEN_SERIES),
            "font.family": ALLEN_FONT,
            "axes.titleweight": "bold",
            "axes.titlesize": 11,
            "axes.labelsize": 9.5,
            "xtick.labelsize": 8.5,
            "ytick.labelsize": 8.5,
            "legend.fontsize": 8.5,
            "savefig.facecolor": ALLEN["page1"],
            "savefig.edgecolor": ALLEN["page1"],
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


def padded_limits(values: list[float], errors: list[float], *, zero_floor: bool) -> tuple[float, float]:
    lower = min(value - error for value, error in zip(values, errors, strict=True))
    upper = max(value + error for value, error in zip(values, errors, strict=True))
    if zero_floor:
        lower = min(0.0, lower)
    span = max(upper - lower, 0.25)
    return lower - (span * 0.08), upper + (span * 0.18)


def metric_values(summary: pl.DataFrame, metric: str) -> tuple[list[float], list[float]]:
    values = summary[f"{metric}_mean"].fill_null(0).to_list()
    errors = summary[f"{metric}_sem"].fill_null(0).to_list()
    return values, errors


def style_axis(ax: plt.Axes, title: str, ylabel: str, *, show_x_labels: bool) -> None:
    ax.set_title(title, loc="left", pad=12)
    ax.set_ylabel(ylabel, labelpad=8)
    ax.grid(axis="y", linewidth=0.9)
    ax.grid(axis="x", visible=False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(ALLEN["black"])
    ax.spines["bottom"].set_color(ALLEN["black"])
    ax.tick_params(axis="both", length=0, pad=5)
    ax.tick_params(axis="x", labelbottom=show_x_labels)


def make_plot(summary: pl.DataFrame) -> None:
    apply_allen_style()

    x = list(range(summary.height))
    weekday_labels = [weekday.lower() for weekday in summary["weekday"].to_list()]
    session_counts = summary["n_sessions"].to_list()

    fig, axes = plt.subplots(2, 2, figsize=(8.5, 6.4))
    fig.subplots_adjust(
        left=0.10,
        right=0.98,
        bottom=0.13,
        top=0.80,
        hspace=0.54,
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
        0.91,
        "session means with standard error; weekday groups from performance.parquet",
        ha="left",
        fontsize=10,
        color=ALLEN["gray2"],
    )

    for index, (ax, plot_config) in enumerate(zip(axes.flat, PLOTS, strict=True)):
        metric, plot_type, title, ylabel, color = plot_config
        values, errors = metric_values(summary, metric)
        show_x_labels = index >= 2

        if plot_type == "line":
            ax.errorbar(
                x,
                values,
                yerr=errors,
                color=color,
                ecolor=ALLEN["gray2"],
                elinewidth=1.1,
                capsize=3,
                linewidth=2.5,
                marker="o",
                markersize=5,
                markeredgecolor=ALLEN["black"],
                markeredgewidth=0.6,
                zorder=3,
            )
        else:
            ax.bar(
                x,
                values,
                yerr=errors,
                color=color,
                edgecolor=ALLEN["black"],
                linewidth=0.6,
                width=0.64,
                error_kw={
                    "ecolor": ALLEN["gray2"],
                    "elinewidth": 1.1,
                    "capsize": 3,
                },
                zorder=3,
            )

        ax.set_xticks(x, weekday_labels)
        style_axis(ax, title, ylabel, show_x_labels=show_x_labels)
        ax.set_ylim(*padded_limits(values, errors, zero_floor=plot_type == "bar"))

    count_note = " / ".join(
        f"{day}: n={count}" for day, count in zip(weekday_labels, session_counts, strict=True)
    )
    fig.text(
        0.10,
        0.045,
        f"weekday sample sizes/{count_note}",
        ha="left",
        fontsize=8.5,
        color=ALLEN["gray2"],
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
