"""Puzzle directory layout and puzzle.toml loading."""
import tomllib
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUZZLES = ROOT / "puzzles"
DOCS = ROOT / "docs"


@dataclass
class Puzzle:
    slug: str
    dir: Path
    meta: dict

    @property
    def work(self) -> Path:
        d = self.dir / "work"
        d.mkdir(exist_ok=True)
        return d

    @property
    def photo(self) -> Path:
        return self.dir / "photo.jpg"

    @property
    def items(self) -> list[dict]:
        return self.meta.get("items", [])


def load(slug: str) -> Puzzle:
    d = PUZZLES / slug
    return Puzzle(slug, d, tomllib.loads((d / "puzzle.toml").read_text()))


def all_puzzles() -> list[Puzzle]:
    ps = [load(p.parent.name) for p in PUZZLES.glob("*/puzzle.toml")]
    return sorted(ps, key=lambda p: str(p.meta.get("date", "")), reverse=True)
