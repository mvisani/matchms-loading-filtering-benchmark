"""Download and cache the GNPS spectral library used for benchmarking."""

from __future__ import annotations

from pathlib import Path

from downloaders import BaseDownloader

GNPS_LIBRARY_URL = "https://external.gnps2.org/gnpslibrary/GNPS-LIBRARY.mgf"


def ensure_dataset(target: Path, url: str = GNPS_LIBRARY_URL) -> Path:
    """Download `url` to `target` if not already cached, returning `target`."""
    downloader = BaseDownloader(
        auto_extract=False,
        cache=True,
        target_directory=str(target.parent),
        verbose=2,
    )
    downloader.download(url, str(target))
    return target
