"""Tests for project path resolution."""

from pathlib import Path

from alphapulse import paths


def test_project_root_finds_marker():
    root = paths.project_root()
    assert (root / "pyproject.toml").exists() or (root / ".git").exists()


def test_data_and_models_live_under_root():
    root = paths.project_root()
    assert paths.data_dir() == root / "data"
    assert paths.models_dir() == root / "models"


def test_env_override_wins(tmp_path, monkeypatch):
    monkeypatch.setenv("ALPHAPULSE_ROOT", str(tmp_path))
    assert paths.project_root() == Path(tmp_path).resolve()
    assert paths.models_dir() == Path(tmp_path).resolve() / "models"


def test_bundled_assets_resolve():
    """The committed sample data and trained model must be discoverable from the package."""
    assert (paths.data_dir() / "sample" / "banknifty_5m.csv").exists()
    assert (paths.models_dir() / "signal_model.pkl").exists()
