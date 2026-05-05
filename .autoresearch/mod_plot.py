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

import matplotlib

matplotlib.use("Agg")

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
    for key in ("blue", "orange", "teal", "violet", "green", "rose", "maroon")
]

PLOTS = (
    ("hit_rate", "line"),
    ("false_alarm_rate", "line"),
    ("vis_dprime", "bar"),
    ("aud_dprime", "bar"),
)
METRICS = tuple(metric for metric, _ in PLOTS)
PLOT_META = {
    "hit_rate": {
        "title": "hit rate/",
        "ylabel": "mean rate",
        "color": ALLEN["blue"],
        "percent": True,
        "higher_is_better": True,
    },
    "false_alarm_rate": {
        "title": "false alarm rate/",
        "ylabel": "mean rate",
        "color": ALLEN["orange"],
        "percent": True,
        "higher_is_better": False,
    },
    "vis_dprime": {
        "title": "visual d-prime/",
        "ylabel": "d-prime",
        "color": ALLEN["teal"],
        "percent": False,
        "higher_is_better": True,
    },
    "aud_dprime": {
        "title": "auditory d-prime/",
        "ylabel": "d-prime",
        "color": ALLEN["violet"],
        "percent": False,
        "higher_is_better": True,
    },
}


def allen_font_family() -> str:
    available = {font.name for font in font_manager.fontManager.ttflist}
    for candidate in ("Allen Institute Text", "Helvetica Neue", "Arial"):
        if candidate in available:
            return candidate
    return "sans-serif"


plt.rcParams.update(
    {
        "figure.facecolor": ALLEN["white"],
        "axes.facecolor": ALLEN["white"],
        "axes.edgecolor": ALLEN["black"],
        "axes.labelcolor": ALLEN["black"],
        "axes.prop_cycle": cycler(color=ALLEN_SERIES),
        "font.family": allen_font_family(),
        "font.size": 10,
        "grid.color": ALLEN["page2"],
        "savefig.facecolor": ALLEN["white"],
        "savefig.edgecolor": ALLEN["white"],
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


def finite_or_nan(value: object) -> float:
    if value is None:
        return math.nan
    number = float(value)
    return number if math.isfinite(number) else math.nan


def sem_or_zero(value: object) -> float:
    if value is None:
        return 0.0
    number = float(value)
    return number if math.isfinite(number) else 0.0


def metric_series(summary: pl.DataFrame, metric: str) -> tuple[list[float], list[float]]:
    means = [finite_or_nan(value) for value in summary[f"{metric}_mean"].to_list()]
    sems = [sem_or_zero(value) for value in summary[f"{metric}_sem"].to_list()]
    return means, sems


def style_panel(ax: plt.Axes, metric: str, x: list[int], labels: list[str]) -> None:
    meta = PLOT_META[metric]
    ax.set_title(
        str(meta["title"]),
        loc="left",
        fontsize=13,
        fontweight="bold",
        color=ALLEN["black"],
        pad=12,
    )
    ax.set_ylabel(str(meta["ylabel"]), fontsize=10, color=ALLEN["black"])
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.grid(axis="y", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.yaxis.set_major_locator(MaxNLocator(nbins=4))

    if meta["percent"]:
        ax.set_ylim(0, 1)
        ax.yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))

    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(ALLEN["black"])
        ax.spines[side].set_linewidth(1.0)

    ax.tick_params(axis="x", labelsize=9, colors=ALLEN["gray2"], length=3)
    ax.tick_params(axis="y", labelsize=9, colors=ALLEN["gray2"], length=3)


def set_dprime_limits(ax: plt.Axes, means: list[float], sems: list[float]) -> None:
    intervals = [
        (mean - sem, mean + sem)
        for mean, sem in zip(means, sems, strict=True)
        if math.isfinite(mean)
    ]
    if not intervals:
        return

    low = min(interval[0] for interval in intervals)
    high = max(interval[1] for interval in intervals)
    span = high - low
    pad = max(span * 0.16, 0.2)
    bottom = min(0.0, low - pad)
    top = high + pad
    if math.isclose(bottom, top):
        top = bottom + 1
    ax.set_ylim(bottom, top)


def annotate_best_day(
    ax: plt.Axes,
    x: list[int],
    labels: list[str],
    means: list[float],
    sems: list[float],
    metric: str,
) -> None:
    finite_points = [
        (idx, value)
        for idx, value in enumerate(means)
        if math.isfinite(value)
    ]
    if not finite_points:
        return

    meta = PLOT_META[metric]
    point_idx, point_value = (
        max(finite_points, key=lambda item: item[1])
        if meta["higher_is_better"]
        else min(finite_points, key=lambda item: item[1])
    )
    label_value = f"{point_value:.0%}" if meta["percent"] else f"{point_value:.2f}"
    vertical_shift = sems[point_idx] if point_idx < len(sems) else 0

    ax.scatter(
        [x[point_idx]],
        [point_value],
        s=46,
        color=ALLEN["green"],
        edgecolor=ALLEN["black"],
        linewidth=0.8,
        zorder=4,
    )
    ax.annotate(
        f"{labels[point_idx]} {label_value}",
        xy=(x[point_idx], point_value),
        xytext=(10, 18 if meta["higher_is_better"] else -24),
        textcoords="offset points",
        fontsize=9,
        fontweight="bold",
        color=ALLEN["black"],
        arrowprops={
            "arrowstyle": "-",
            "color": ALLEN["black"],
            "lw": 0.9,
            "shrinkA": 0,
            "shrinkB": 5,
        },
        va="bottom" if meta["higher_is_better"] else "top",
    )

    if not meta["percent"] and vertical_shift:
        y_bottom, y_top = ax.get_ylim()
        ax.set_ylim(y_bottom, max(y_top, point_value + vertical_shift + 0.35))


def draw_metric(
    ax: plt.Axes,
    metric: str,
    plot_type: str,
    x: list[int],
    labels: list[str],
    means: list[float],
    sems: list[float],
) -> None:
    meta = PLOT_META[metric]
    color = str(meta["color"])

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
            markeredgewidth=1.6,
            linewidth=2.4,
            capsize=3,
            elinewidth=1.1,
            capthick=1.1,
            zorder=3,
        )
    else:
        ax.bar(
            x,
            means,
            yerr=sems,
            color=color,
            edgecolor=ALLEN["black"],
            linewidth=0.8,
            width=0.68,
            error_kw={
                "ecolor": ALLEN["black"],
                "elinewidth": 1.0,
                "capsize": 3,
                "capthick": 1.0,
            },
            zorder=3,
        )
        ax.axhline(0, color=ALLEN["black"], linewidth=1.0, zorder=2)
        set_dprime_limits(ax, means, sems)

    style_panel(ax, metric, x, labels)
    annotate_best_day(ax, x, labels, means, sems, metric)


def make_plot(summary: pl.DataFrame) -> None:
    x = list(range(summary.height))
    labels = [str(label).lower() for label in summary["weekday"].to_list()]
    total_sessions = int(summary["n_sessions"].sum())

    fig = plt.figure(figsize=(10.8, 7.2), facecolor=ALLEN["white"])
    gs = fig.add_gridspec(
        2,
        2,
        height_ratios=[0.23, 1.0],
        width_ratios=[0.035, 1.0],
        left=0.06,
        right=0.97,
        bottom=0.08,
        top=0.95,
        hspace=0.06,
        wspace=0.05,
    )

    rail_ax = fig.add_subplot(gs[:, 0])
    title_ax = fig.add_subplot(gs[0, 1])
    panel_grid = gs[1, 1].subgridspec(2, 2, hspace=0.52, wspace=0.32)
    axes = [fig.add_subplot(panel_grid[row, col]) for row in range(2) for col in range(2)]

    rail_ax.set_facecolor(ALLEN["blue"])
    rail_ax.set_xticks([])
    rail_ax.set_yticks([])
    for spine in rail_ax.spines.values():
        spine.set_visible(False)

    title_ax.axis("off")
    title_ax.text(
        0.0,
        0.72,
        "allen institute/dynamic routing",
        ha="left",
        va="center",
        fontsize=21,
        fontweight="bold",
        transform=title_ax.transAxes,
    )
    title_ax.text(
        0.0,
        0.36,
        "weekday behavioral performance summary",
        ha="left",
        va="center",
        fontsize=11,
        color=ALLEN["gray2"],
        transform=title_ax.transAxes,
    )
    title_ax.text(
        1.0,
        0.36,
        f"n={total_sessions} sessions",
        ha="right",
        va="center",
        fontsize=10,
        color=ALLEN["gray2"],
        transform=title_ax.transAxes,
    )
    title_ax.plot(
        [0.0, 0.16],
        [0.08, 0.08],
        color=ALLEN["orange"],
        linewidth=5,
        solid_capstyle="butt",
        transform=title_ax.transAxes,
        clip_on=False,
    )

    for ax, (metric, plot_type) in zip(axes, PLOTS, strict=True):
        means, sems = metric_series(summary, metric)
        draw_metric(ax, metric, plot_type, x, labels, means, sems)

    FIGURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE_PATH, dpi=180)
    plt.close(fig)


def main() -> None:
    sessions = load_session_summary()
    summary = summarize_by_weekday(sessions)
    make_plot(summary)
    print(f"wrote {FIGURE_PATH}")


if __name__ == "__main__":
    main()
