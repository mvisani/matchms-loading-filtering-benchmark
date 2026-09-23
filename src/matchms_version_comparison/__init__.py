"""Compare matchms 0.33.1 vs. the matchms development branch on loading/processing speed."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import click

from matchms_version_comparison.data import GNPS_LIBRARY_URL, ensure_dataset
from matchms_version_comparison.envs import ensure_env, installed_matchms_spec
from matchms_version_comparison.plotting import plot_comparison, summarize_times

REPO_ROOT = Path(__file__).resolve().parents[2]
STABLE_PACKAGE_SPEC = "matchms==0.33.1"
DEV_PACKAGE_SPEC = "matchms @ git+https://github.com/matchms/matchms.git"
# Pinned to the `development` branch's tip commit at the time this was last updated, so the
# benchmark is reproducible instead of silently drifting as the branch moves. Update by taking
# the latest SHA from https://github.com/matchms/matchms/commits/development.
DEV_MATCHMS_COMMIT = "591b1486e6d0fc021348d7535df74ad87449c6d5"


def run_benchmark(
    python_exe: Path,
    script: Path,
    mgf_path: Path,
    output_json: Path,
    repeats: int,
    install_spec: str,
    limit: int | None,
) -> None:
    cmd = [
        str(python_exe),
        str(script),
        "--mgf",
        str(mgf_path),
        "--output",
        str(output_json),
        "--repeats",
        str(repeats),
        "--install-spec",
        install_spec,
    ]
    if limit is not None:
        cmd += ["--limit", str(limit)]
    subprocess.run(cmd, check=True)


def print_summary(stable: dict, dev: dict) -> None:
    for label, res in (
        ("matchms 0.33.1 (stable)", stable),
        ("matchms development", dev),
    ):
        load_mean, load_std = summarize_times(res["load_times_seconds"])
        combined_mean, combined_std = summarize_times(
            res["default_filters_combined_times_seconds"]
        )
        n = res["n_spectra_loaded"][0]
        print(
            f"{label}: {n} spectra | load {load_mean:.2f}s \u00b1 {load_std:.2f}s "
            f"| default_filters {combined_mean:.2f}s \u00b1 {combined_std:.2f}s"
        )


@click.command()
@click.option("--mgf-url", default=GNPS_LIBRARY_URL, show_default=True)
@click.option("--data-dir", default="data", show_default=True)
@click.option("--envs-dir", default=".benchmark-envs", show_default=True)
@click.option("--results-dir", default="results", show_default=True)
@click.option("--repeats", type=int, default=5, show_default=True)
@click.option("--limit", type=int, default=None)
@click.option("--python", "python_version", default="3.12", show_default=True)
def main(
    mgf_url: str,
    data_dir: str,
    envs_dir: str,
    results_dir: str,
    repeats: int,
    limit: int | None,
    python_version: str,
) -> None:
    """Compare matchms 0.33.1 vs. development branch loading/processing speed."""
    data_dir = Path(data_dir)
    envs_dir = Path(envs_dir)
    results_dir = Path(results_dir)
    scripts_dir = REPO_ROOT / "scripts"

    mgf_path = ensure_dataset(data_dir / "GNPS-LIBRARY.mgf", mgf_url)

    stable_python = ensure_env(
        envs_dir / "stable",
        "matchms-bench-stable",
        python_version,
        STABLE_PACKAGE_SPEC,
        extra_packages=("click",),
    )
    dev_python = ensure_env(
        envs_dir / "dev",
        "matchms-bench-dev",
        python_version,
        DEV_PACKAGE_SPEC,
        rev=DEV_MATCHMS_COMMIT,
        extra_packages=("click",),
        override_dependencies=("scipy>=1.16,<1.17",),
    )

    stable_spec = installed_matchms_spec(stable_python)
    dev_spec = installed_matchms_spec(dev_python)

    results_dir.mkdir(parents=True, exist_ok=True)
    stable_json = results_dir / "stable_results.json"
    dev_json = results_dir / "dev_results.json"

    print("Running benchmark on matchms 0.33.1 ...")
    run_benchmark(
        stable_python,
        scripts_dir / "benchmark_stable.py",
        mgf_path,
        stable_json,
        repeats,
        stable_spec,
        limit,
    )

    print("Running benchmark on matchms development branch ...")
    run_benchmark(
        dev_python,
        scripts_dir / "benchmark_dev.py",
        mgf_path,
        dev_json,
        repeats,
        dev_spec,
        limit,
    )

    stable_results = json.loads(stable_json.read_text())
    dev_results = json.loads(dev_json.read_text())

    plot_comparison(stable_results, dev_results, results_dir / "comparison.png")
    print_summary(stable_results, dev_results)


if __name__ == "__main__":
    main()
