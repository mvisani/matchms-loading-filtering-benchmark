"""Benchmark spectra loading and per-filter processing with the matchms development branch."""

import json
import sys
import time
from pathlib import Path

import click

FILTER_NAMES = [
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


@click.command()
@click.option("--mgf", required=True, type=click.Path(exists=True, dir_okay=False))
@click.option("--output", required=True, type=click.Path(dir_okay=False))
@click.option("--repeats", type=int, default=3, show_default=True)
@click.option("--install-spec", default="")
@click.option("--limit", type=int, default=None)
def main(mgf: str, output: str, repeats: int, install_spec: str, limit):
    import matchms
    from matchms.filtering import (
        add_compound_name,
        add_precursor_mz,
        clean_compound_name,
        correct_charge,
        default_filters,
        derive_adduct_from_name,
        derive_formula_from_name,
        derive_ionmode,
        interpret_pepmass,
        make_charge_int,
    )
    from matchms.importing import load_ms2_dataset

    filter_functions = [
        make_charge_int,
        add_compound_name,
        derive_adduct_from_name,
        derive_formula_from_name,
        clean_compound_name,
        interpret_pepmass,
        add_precursor_mz,
        derive_ionmode,
        correct_charge,
    ]

    load_times = []
    n_loaded = []
    filter_stage_times = {name: [] for name in FILTER_NAMES}
    combined_times = []

    for _ in range(repeats):
        t0 = time.perf_counter()
        collection = load_ms2_dataset(mgf)
        t1 = time.perf_counter()
        if limit is not None:
            collection = collection[:limit]
        load_times.append(t1 - t0)
        n_loaded.append(len(collection))

        working = collection.copy()
        for name, fn in zip(FILTER_NAMES, filter_functions):
            ts0 = time.perf_counter()
            working = fn(working)
            ts1 = time.perf_counter()
            filter_stage_times[name].append(ts1 - ts0)

        fresh = collection.copy()
        tc0 = time.perf_counter()
        processed = default_filters(fresh)
        tc1 = time.perf_counter()
        combined_times.append(tc1 - tc0)
        assert len(processed) == len(collection)

    result = {
        "matchms_version": matchms.__version__,
        "install_spec": install_spec,
        "mgf_file": str(Path(mgf).resolve()),
        "repeats": repeats,
        "limit": limit,
        "n_spectra_loaded": n_loaded,
        "load_times_seconds": load_times,
        "filter_stage_times_seconds": filter_stage_times,
        "default_filters_combined_times_seconds": combined_times,
        "python_version": sys.version,
    }
    Path(output).write_text(json.dumps(result, indent=2))
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
