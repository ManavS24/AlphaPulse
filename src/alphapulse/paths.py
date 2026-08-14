"""Project path resolution.

The bundled sample data, the trained model, and the SQLite trade log live in the project
directory rather than inside the installed package. Resolving them by a fixed number of
parent hops breaks as soon as the package is installed non-editably (``pip install .``),
where the module sits in ``site-packages``. Walking up to a marker file works in both
layouts, and an environment variable allows an explicit override.
"""

import os
from pathlib import Path

_MARKERS = ("pyproject.toml", ".git")


def project_root() -> Path:
    """Return the project root.

    Uses ``ALPHAPULSE_ROOT`` when set, otherwise walks up from this file looking for a
    project marker, and finally falls back to the current working directory.
    """
    override = os.environ.get("ALPHAPULSE_ROOT")
    if override:
        return Path(override).expanduser().resolve()

    for candidate in Path(__file__).resolve().parents:
        if any((candidate / marker).exists() for marker in _MARKERS):
            return candidate

    return Path.cwd()


def data_dir() -> Path:
    return project_root() / "data"


def models_dir() -> Path:
    return project_root() / "models"
