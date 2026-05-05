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
    ALLEN[k]
    for k in ("blue", "orange", "teal", "violet", "green", "rose", "maroon")
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
            "axes.titleweight": "bold",
            "xtick.color": ALLEN["gray2"],
            "ytick.color": ALLEN["gray2"],
            "grid.color": ALLEN["page2"],
            "grid.linewidth": 0.9,
            "text.color": ALLEN["black"],
            "axes.prop_cycle": cycler(color=ALLEN_SERIES),
            "font.family": resolve_font(),
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
            pl.col("session_date").dt.strftime("%a").str.to_lowercase().alias("weekday"),
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
        .with_columns(
            *[pl.col(f"{metric}_sem").fill_null(0.0) for metric in METRICS]
        )
        .sort("weekday_num")
    )
    return summary


def style_axis(ax: plt.Axes, *, show_bottom_labels: bool) -> None:
    ax.grid(True, axis="y")
    ax.grid(False, axis="x")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(ALLEN["black"])
    ax.spines["bottom"].set_color(ALLEN["black"])
    ax.tick_params(axis="both", length=0, labelsize=8.5)
    ax.tick_params(axis="x", labelbottom=show_bottom_labels)


def metric_extent(summary: pl.DataFrame, metrics: tuple[str, ...]) -> tuple[float, float]:
    lows: list[float] = []
    highs: list[float] = []
    for metric in metrics:
        values = summary[f"{metric}_mean"].to_list()
        errors = summary[f"{metric}_sem"].to_list()
        lows.extend(value - error for value, error in zip(values, errors, strict=True))
        highs.extend(value + error for value, error in zip(values, errors, strict=True))

    return min(lows), max(highs)


def make_plot(summary: pl.DataFrame) -> None:
    apply_allen_style()

    x = list(range(summary.height))
    weekdays = summary["weekday"].to_list()
    fig, axes = plt.subplots(2, 2, figsize=(8.8, 6.3), sharey="row")
    fig.subplots_adjust(
        left=0.11,
        right=0.98,
        bottom=0.14,
        top=0.78,
        hspace=0.48,
        wspace=0.28,
    )

    for index, (ax, (metric, plot_type)) in enumerate(
        zip(axes.flat, PLOTS, strict=True)
    ):
        values = summary[f"{metric}_mean"].to_list()
        errors = summary[f"{metric}_sem"].to_list()
        color = PLOT_COLORS[metric]

        if plot_type == "line":
            ax.errorbar(
                x,
                values,
                yerr=errors,
                color=color,
                ecolor=ALLEN["gray1"],
                marker="o",
                markersize=5.5,
                markerfacecolor=ALLEN["white"],
                markeredgewidth=1.6,
                linewidth=2.2,
                elinewidth=1.15,
                capsize=3,
                zorder=3,
            )
        else:
            ax.bar(
                x,
                values,
                yerr=errors,
                color=color,
                edgecolor=ALLEN["black"],
                linewidth=0.7,
                error_kw={
                    "ecolor": ALLEN["gray2"],
                    "elinewidth": 1.05,
                    "capsize": 3,
                    "capthick": 1.05,
                },
                zorder=3,
            )

        ax.set_title(PLOT_TITLES[metric], loc="left", fontsize=11, pad=12)
        ax.set_xticks(x, weekdays)
        style_axis(ax, show_bottom_labels=index >= 2)

    axes[0, 0].set_ylim(0, 1.02)
    axes[0, 1].set_ylim(0, 1.02)
    dprime_low, dprime_high = metric_extent(summary, ("vis_dprime", "aud_dprime"))
    dprime_upper = dprime_high * 1.14 if dprime_high > 0 else 1
    axes[1, 0].set_ylim(min(0, dprime_low * 1.08), dprime_upper)
    axes[1, 1].set_ylim(min(0, dprime_low * 1.08), dprime_upper)

    axes[0, 0].set_ylabel("rate (mean +/- SEM)", labelpad=8)
    axes[1, 0].set_ylabel("d-prime (mean +/- SEM)", labelpad=8)
    for ax in axes[:, 1]:
        ax.tick_params(axis="y", labelleft=False)

    total_sessions = int(summary["n_sessions"].sum())
    fig.suptitle(
        "allen institute/dynamic routing/performance by weekday",
        x=0.11,
        y=0.965,
        ha="left",
        fontsize=18,
        fontweight="bold",
    )
    fig.text(
        0.11,
        0.915,
        f"weekday means from {total_sessions:,} behavior sessions / error bars = SEM",
        ha="left",
        fontsize=10.5,
        color=ALLEN["gray2"],
    )
    fig.text(
        0.11,
        0.055,
        "source: mindscope dynamic routing behavior tables",
        ha="left",
        fontsize=8.5,
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
