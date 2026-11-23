"""Load settings from config.yaml (next to the app) and the API key from .env."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class Config:
    inbox: Path
    output_root: Path
    review_folder: Path
    duplicates_folder: Path
    data_folder: Path  # customers.json, log.csv, state.db live here
    poll_seconds: int = 10
    stable_seconds: int = 5  # file size must not change for this long
    year_folder_format: str = "{year}"
    month_folder_format: str = "{month:02d} {month_name} {year}"
    file_name_format: str = "{date} {dn_number}"
    date_order: str = "DMY"  # how dates like 01/02/2027 are printed
    max_days_in_future: int = 7
    max_years_in_past: int = 3
    own_company_names: list[str] = field(default_factory=list)
    customer_match_review: int = 80  # new name this similar to a known one = ask a person
    engine: str = "local"  # local = BHPetrol layout rules (offline); claude = any layout via the API
    model: str = "claude-opus-5-5"
    max_attempts: int = 5  # API failures before a file goes to review

    @property
    def customers_file(self) -> Path:
        return self.data_folder / "customers.json"

    @property
    def log_file(self) -> Path:
        return self.data_folder / "log.csv"

    @property
    def state_db(self) -> Path:
        return self.data_folder / "state.db"


def _load_env_file(path: Path) -> None:
    """Read KEY=value lines into the environment (only keys not already set)."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def load_config(path: Path) -> Config:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    _load_env_file(path.parent / ".env")

    def p(key: str, default: str | None = None) -> Path:
        value = raw.get(key, default)
        if value is None:
            raise ValueError(f"config.yaml is missing '{key}'")
        return Path(value)

    output_root = p("output_root")
    cfg = Config(
        inbox=p("inbox"),
        output_root=output_root,
        review_folder=p("review_folder", str(output_root / "_Needs Review")),
        duplicates_folder=p("duplicates_folder", str(output_root / "_Duplicates")),
        data_folder=p("data_folder", str(path.parent / "data")),
    )
    simple = [
        "poll_seconds", "stable_seconds", "year_folder_format", "month_folder_format",
        "file_name_format", "date_order", "max_days_in_future", "max_years_in_past",
        "own_company_names", "customer_match_review", "engine", "model", "max_attempts",
    ]
    for key in simple:
        if key in raw and raw[key] is not None:
            setattr(cfg, key, raw[key])
    for folder in (cfg.inbox, cfg.output_root, cfg.review_folder, cfg.duplicates_folder, cfg.data_folder):
        folder.mkdir(parents=True, exist_ok=True)
    return cfg
