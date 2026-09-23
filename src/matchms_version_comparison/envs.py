"""Create and query isolated uv sub-projects, one per matchms version under test."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def venv_python(env_dir: Path) -> Path:
    return env_dir / ".venv" / "bin" / "python"


def ensure_project(env_dir: Path, name: str, python_version: str) -> None:
    """Create a minimal standalone uv project at `env_dir` if it doesn't exist yet."""
    if (env_dir / "pyproject.toml").exists():
        return
    subprocess.run(
        [
            "uv",
            "init",
            "--bare",
            "--no-workspace",
            "--no-readme",
            "--no-pin-python",
            "--python",
            python_version,
            "--name",
            name,
            str(env_dir),
        ],
        check=True,
    )


def apply_dependency_override(env_dir: Path, override: str) -> None:
    """Force a specific resolved dependency version via `[tool.uv] override-dependencies`.

    Needed because matchms' own upper bound on `scipy` can resolve to a build whose
    `_propack` extension fails to `dlopen` on this host; a newer scipy within a range
    matchms itself declares elsewhere fixes it. Must be applied before `uv add`.
    """
    pyproject = env_dir / "pyproject.toml"
    text = pyproject.read_text()
    if "override-dependencies" in text:
        return
    pyproject.write_text(
        text + f'\n[tool.uv]\noverride-dependencies = ["{override}"]\n'
    )


def ensure_env(
    env_dir: Path,
    name: str,
    python_version: str,
    package_spec: str,
    branch: str | None = None,
    extra_packages: tuple[str, ...] = (),
    override_dependencies: tuple[str, ...] = (),
) -> Path:
    """Create/update the isolated sub-project at `env_dir` and return its venv python."""
    if shutil.which("uv") is None:
        raise RuntimeError("uv is required but was not found on PATH")

    ensure_project(env_dir, name, python_version)
    for override in override_dependencies:
        apply_dependency_override(env_dir, override)

    add_cmd = ["uv", "add", "--project", str(env_dir), package_spec]
    if branch is not None:
        add_cmd += ["--branch", branch]
    subprocess.run(add_cmd, check=True)

    if extra_packages:
        subprocess.run(
            ["uv", "add", "--project", str(env_dir), *extra_packages],
            check=True,
        )

    return venv_python(env_dir)


def installed_matchms_spec(python_exe: Path) -> str:
    """Return the `uv pip freeze` line describing the installed matchms package
    (a read-only query, not an install -- `uv pip freeze` remains valid to inspect
    an existing environment)."""
    result = subprocess.run(
        ["uv", "pip", "freeze", "--python", str(python_exe)],
        check=True,
        capture_output=True,
        text=True,
    )
    for line in result.stdout.splitlines():
        if line.lower().startswith("matchms"):
            return line.strip()
    return ""
