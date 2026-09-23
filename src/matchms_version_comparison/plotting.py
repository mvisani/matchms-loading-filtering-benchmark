"""Render the load/filter-stage timing comparison plot."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

FILTER_STAGE_ORDER = [
    "make_charge_int",
    "add_compound_name",
    "derive_adduct_from_name",
    "derive_formula_from_name",
    "clean_compound_name",
    "interpret_pepmass",
    "add_precursor_mz",
    "derive_ionmode",
    "correct_charge",
]


def summarize_times(times: list[float]) -> tuple[float, float]:
    arr = np.array(times, dtype=float)
    return float(arr.mean()), float(arr.std())


def plot_comparison(stable: dict, dev: dict, output_path: Path) -> None:
    version_labels = [
        f"matchms {stable['matchms_version']} (stable)",
        f"matchms {dev['matchms_version']} (development)",
    ]
    colors = ["#4C72B0", "#DD8452"]

    fig, (ax_load, ax_filters) = plt.subplots(
        2, 1, figsize=(12, 9), gridspec_kw={"height_ratios": [1, 2]}
    )

    load_stats = [summarize_times(r["load_times_seconds"]) for r in (stable, dev)]
    means = [m for m, _ in load_stats]
    stds = [s for _, s in load_stats]
    bars = ax_load.bar(version_labels, means, yerr=stds, capsize=6, color=colors)
    ax_load.set_ylabel("Time (seconds)")
    ax_load.set_title("Loading time")
    for bar, mean in zip(bars, means):
        ax_load.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{mean:.2f}s",
            ha="center",
            va="bottom",
        )

    categories = [*FILTER_STAGE_ORDER, "default_filters (combined)"]
    x = np.arange(len(categories))
    width = 0.35

    for offset, (res, color, label) in enumerate(
        zip((stable, dev), colors, version_labels)
    ):
        means = [
            summarize_times(res["filter_stage_times_seconds"][name])[0]
            for name in FILTER_STAGE_ORDER
        ] + [summarize_times(res["default_filters_combined_times_seconds"])[0]]
        stds = [
            summarize_times(res["filter_stage_times_seconds"][name])[1]
            for name in FILTER_STAGE_ORDER
        ] + [summarize_times(res["default_filters_combined_times_seconds"])[1]]
        ax_filters.bar(
            x + (offset - 0.5) * width,
            means,
            width,
            yerr=stds,
            capsize=4,
            color=color,
            label=label,
        )

    ax_filters.set_xticks(x)
    ax_filters.set_xticklabels(categories, rotation=45, ha="right")
    ax_filters.set_ylabel("Time (seconds)")
    ax_filters.set_title("default_filters: 9 individual stages + combined")
    ax_filters.legend()

    n_spectra = stable["n_spectra_loaded"][0]
    mgf_name = Path(stable["mgf_file"]).name
    fig.suptitle(
        f"matchms loading & filtering speed — {n_spectra} spectra from {mgf_name}"
    )
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    print(f"Saved plot to {output_path}")
