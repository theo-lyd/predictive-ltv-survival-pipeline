"""Configuration helpers for the pipeline scaffold."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PipelinePaths:
    """Local path conventions used by the scaffold."""

    repo_root: Path = Path(__file__).resolve().parents[2]

    @property
    def bronze(self) -> Path:
        return self.repo_root / "data" / "bronze"

    @property
    def silver(self) -> Path:
        return self.repo_root / "data" / "silver"

    @property
    def gold(self) -> Path:
        return self.repo_root / "data" / "gold"


DEFAULT_PATHS = PipelinePaths()
