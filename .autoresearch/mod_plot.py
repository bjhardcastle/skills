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
from matplotlib.lines import Line2D
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

PLOTS = (
    ("hit_rate", "line", "hit rate", "rate", "blue"),
    ("false_alarm_rate", "line", "false alarm rate", "rate", "orange"),
    ("vis_dprime", "bar", "visual d-prime", "d-prime", "teal"),
    ("aud_dprime", "bar", "auditory d-prime", "d-prime", "violet"),
)
METRICS = tuple(metric for metric, *_ in PLOTS)


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
            "figure.facecolor": ALLEN["page1"],
            "savefig.facecolor": ALLEN["page1"],
            "savefig.edgecolor": ALLEN["page1"],
            "axes.facecolor": ALLEN["white"],
            "axes.edgecolor": ALLEN["black"],
            "axes.labelcolor": ALLEN["black"],
            "axes.linewidth": 0.9,
            "axes.prop_cycle": cycler(color=ALLEN_SERIES),
            "axes.titlelocation": "left",
            "font.family": resolve_font(),
            "font.size": 9.5,
            "grid.color": ALLEN["page2"],
            "grid.linewidth": 0.8,
            "legend.frameon": False,
            "text.color": ALLEN["black"],
            "xtick.color": ALLEN["gray2"],
            "xtick.labelsize": 8.5,
            "ytick.color": ALLEN["gray2"],
            "ytick.labelsize": 8.5,
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
                (
                    pl.when(pl.col(f"{metric}_n") > 1)
                    .then(pl.col(f"{metric}_sd") / pl.col(f"{metric}_n").sqrt())
                    .otherwise(0.0)
                    .fill_nan(0.0)
                    .fill_null(0.0)
                    .alias(f"{metric}_sem")
                )
                for metric in METRICS
            ]
        )
        .sort("weekday_num")
    )
    return summary


def numeric_column(summary: pl.DataFrame, column: str, null_value: float) -> list[float]:
    values = []
    for value in summary[column].to_list():
        values.append(null_value if value is None else float(value))
    return values


def metric_extent(summary: pl.DataFrame, metric: str) -> tuple[float, float] | None:
    means = numeric_column(summary, f"{metric}_mean", float("nan"))
    errors = numeric_column(summary, f"{metric}_sem", 0.0)
    lows: list[float] = []
    highs: list[float] = []
    for mean, error in zip(means, errors, strict=True):
        if math.isfinite(mean):
            error = error if math.isfinite(error) else 0.0
            lows.append(mean - error)
            highs.append(mean + error)
    if not lows:
        return None
    return min(lows), max(highs)


def shared_limits(
    summary: pl.DataFrame, metrics: tuple[str, ...], *, include_zero: bool
) -> tuple[float, float]:
    extents = [extent for metric in metrics if (extent := metric_extent(summary, metric))]
    if not extents:
        return (0.0, 1.0)

    lower = min(extent[0] for extent in extents)
    upper = max(extent[1] for extent in extents)
    if include_zero:
        lower = min(0.0, lower)
        upper = max(0.0, upper)

    span = upper - lower
    if span <= 0:
        span = 1.0
    padding = span * 0.12
    return lower - padding, upper + padding


def style_axis(
    ax: plt.Axes,
    *,
    title: str,
    show_x_labels: bool,
    show_y_labels: bool,
    y_label: str,
) -> None:
    ax.set_title(title, loc="left", fontsize=11, fontweight="bold", pad=12)
    ax.set_axisbelow(True)
    ax.grid(axis="y")
    ax.grid(axis="x", visible=False)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_color(ALLEN["black"])
    ax.spines["left"].set_color(ALLEN["black"])

    ax.tick_params(axis="x", length=0, pad=7, labelbottom=show_x_labels)
    ax.tick_params(
        axis="y",
        color=ALLEN["gray1"],
        labelleft=show_y_labels,
        left=show_y_labels,
        length=3,
        width=0.8,
    )
    if show_y_labels:
        ax.set_ylabel(y_label, fontsize=9.5, fontweight="bold", labelpad=9)
    else:
        ax.set_ylabel("")
        ax.spines["left"].set_visible(False)


def add_structure(fig: plt.Figure, axes: plt.Axes) -> None:
    fig.add_artist(
        Line2D(
            [0.09, 0.98],
            [0.88, 0.88],
            transform=fig.transFigure,
            color=ALLEN["blue"],
            linewidth=2.0,
            solid_capstyle="butt",
            clip_on=False,
        )
    )

    left_col = axes[0, 0].get_position()
    right_col = axes[0, 1].get_position()
    top_row = axes[0, 0].get_position()
    bottom_row = axes[1, 0].get_position()
    x_mid = (left_col.x1 + right_col.x0) / 2
    y_mid = (bottom_row.y1 + top_row.y0) / 2

    fig.add_artist(
        Line2D(
            [x_mid, x_mid],
            [0.14, 0.80],
            transform=fig.transFigure,
            color=ALLEN["page2"],
            linewidth=0.8,
            clip_on=False,
        )
    )
    fig.add_artist(
        Line2D(
            [0.09, 0.98],
            [y_mid, y_mid],
            transform=fig.transFigure,
            color=ALLEN["page2"],
            linewidth=0.8,
            clip_on=False,
        )
    )


def make_plot(summary: pl.DataFrame) -> None:
    apply_allen_style()

    x = list(range(summary.height))
    weekdays = [str(day).lower() for day in summary["weekday"].to_list()]
    rate_upper = max(1.0, shared_limits(summary, ("hit_rate", "false_alarm_rate"), include_zero=True)[1])
    rate_limits = (0.0, min(rate_upper, 1.12))
    dprime_limits = shared_limits(summary, ("vis_dprime", "aud_dprime"), include_zero=True)

    fig, axes = plt.subplots(2, 2, figsize=(9.2, 6.4), dpi=180)
    fig.subplots_adjust(
        left=0.09,
        right=0.98,
        bottom=0.14,
        top=0.80,
        hspace=0.52,
        wspace=0.34,
    )

    session_count = int(summary["n_sessions"].sum()) if summary.height else 0
    fig.suptitle(
        "allen institute/dynamic routing",
        x=0.09,
        y=0.965,
        ha="left",
        fontsize=20,
        fontweight="bold",
    )
    fig.text(
        0.09,
        0.92,
        f"weekday behavior performance; mean +/- SEM across {session_count} sessions",
        ha="left",
        fontsize=10.5,
        color=ALLEN["gray2"],
    )

    for index, (ax, (metric, plot_type, title, y_label, color_key)) in enumerate(
        zip(axes.flat, PLOTS, strict=True)
    ):
        row, col = divmod(index, 2)
        means = numeric_column(summary, f"{metric}_mean", float("nan"))
        errors = numeric_column(summary, f"{metric}_sem", 0.0)
        color = ALLEN[color_key]

        if plot_type == "line":
            ax.errorbar(
                x,
                means,
                yerr=errors,
                color=color,
                linewidth=2.2,
                marker="o",
                markersize=5.2,
                markerfacecolor=ALLEN["white"],
                markeredgecolor=color,
                markeredgewidth=1.4,
                capsize=4,
                capthick=1.1,
                elinewidth=1.1,
                zorder=3,
            )
            ax.set_ylim(*rate_limits)
            ax.yaxis.set_major_formatter(PercentFormatter(xmax=1.0, decimals=0))
        else:
            ax.bar(
                x,
                means,
                yerr=errors,
                color=color,
                alpha=0.88,
                edgecolor=ALLEN["black"],
                linewidth=0.8,
                width=0.62,
                capsize=4,
                error_kw={
                    "ecolor": ALLEN["black"],
                    "elinewidth": 1.0,
                    "capthick": 1.0,
                },
                zorder=3,
            )
            ax.axhline(0, color=ALLEN["page2"], linewidth=1.0, zorder=1)
            ax.set_ylim(*dprime_limits)
            ax.yaxis.set_major_locator(MaxNLocator(nbins=5))

        ax.set_xticks(x)
        ax.set_xticklabels(weekdays if row == 1 else [])
        style_axis(
            ax,
            title=title,
            show_x_labels=row == 1,
            show_y_labels=col == 0,
            y_label=y_label,
        )

    fig.supxlabel("weekday", x=0.535, y=0.07, fontsize=10, fontweight="bold")
    fig.text(
        0.09,
        0.035,
        "whiskers show SEM; weekdays are ordered by the session date.",
        ha="left",
        fontsize=8.5,
        color=ALLEN["gray2"],
    )
    add_structure(fig, axes)

    fig.savefig(FIGURE_PATH)
    plt.close(fig)


def main() -> None:
    sessions = load_session_summary()
    summary = summarize_by_weekday(sessions)
    make_plot(summary)
    print(f"wrote {FIGURE_PATH}")


if __name__ == "__main__":
    main()
