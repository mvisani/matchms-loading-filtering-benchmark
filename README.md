# matchms-version-comparison

Benchmarks spectra **loading** and **filtering** speed of [matchms](https://github.com/matchms/matchms)
0.33.1 (the current PyPI release) against the `development` branch, using a real ~16k-spectrum
GNPS reference library. Produces a plot comparing the two versions.

## Dataset

[`GNPS-LIBRARY.mgf`](https://external.gnps2.org/gnpslibrary/GNPS-LIBRARY.mgf) (~136 MiB, ~16,100
parsed spectra), downloaded once and cached under `data/` (gitignored).

## What's measured

For each matchms version: the time to load the whole file, the time to run each of the 9 functions
inside `matchms.filtering.default_filters` individually (in their canonical order), and the time to
run the combined `default_filters` call — each repeated (default 3x) from a fresh copy of the
originally loaded spectra.

```
make_charge_int, add_compound_name, derive_adduct_from_name, derive_formula_from_name,
clean_compound_name, interpret_pepmass, add_precursor_mz, derive_ionmode, correct_charge
```

## Usage

```sh
uv run matchms-version-comparison [OPTIONS]
```

| Option          | Default              | Description                                 |
| --------------- | -------------------- | ------------------------------------------- |
| `--mgf-url`     | GNPS-LIBRARY.mgf URL | Source MGF to download                      |
| `--data-dir`    | `data`               | Where the MGF is cached                     |
| `--envs-dir`    | `.benchmark-envs`    | Where the two isolated sub-projects live    |
| `--results-dir` | `results`            | Where JSON results and the plot are written |
| `--repeats`     | `5`                  | Timing repeats per stage                    |
| `--limit`       | none (full file)     | Cap spectra loaded, for a fast dry run      |
| `--python`      | `3.12`               | Python version for both sub-projects        |

Re-running is idempotent: the dataset download, sub-project creation, and `uv add` installs are all
skipped once already present/satisfied — only the two benchmarks and the plot regenerate.

## Output

- `results/stable_results.json`, `results/dev_results.json` — raw timings per version (gitignored).
- `results/comparison.png` — the comparison plot (committed): a loading-time bar chart plus a
  grouped bar chart of the 9 individual filter stages and the combined `default_filters` call.

## Results (full library, 16,107 spectra, 5 repeats)

|                              | matchms 0.33.1 (stable) | matchms development |
| ---------------------------- | ----------------------- | ------------------- |
| Load                         | 5.47s ± 0.10s           | 4.61s ± 0.08s       |
| `default_filters` (combined) | 8.62s ± 0.02s           | 3.50s ± 0.01s       |

The `development` branch's vectorized `SpectraCollection` filtering is roughly 2.5x faster on the
combined `default_filters` call than 0.33.1's per-`Spectrum` Python loop. See
`results/comparison.png` for the per-filter-stage breakdown.

## Layout

```
src/matchms_version_comparison/
  __init__.py   # click CLI orchestrator: download, provision envs, run both benchmarks, plot
  data.py       # dataset download/caching
  envs.py       # isolated uv sub-project creation/querying
  plotting.py   # comparison plot rendering
scripts/
  benchmark_stable.py  # runs inside the 0.33.1 sub-project
  benchmark_dev.py     # runs inside the development sub-project
```
