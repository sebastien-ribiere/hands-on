"""The versioned rubric an assessment is made against.

A rubric is policy, so it lives in the corporate source tree next to the rules,
and it is pinned by the same Git tag. It is versioned *twice over*, on purpose:

  - by file name -- `rubrics/spec-readiness-1.0.0.toml`, so publishing a new
    rubric is an added file and a one-line rule change, both visible in a diff;
  - by the `version` field inside it, which is what every assessment records.

That second half is what makes the score auditable. An assessment carries the
exact rubric ref it was produced under (`spec-readiness@1.0.0`). When the
profile later pins `1.1.0`, the recorded assessment is not silently re-read as
if it had been made against the new rubric -- it stops applying, and says so.

The rubric declares what is looked at and what each dimension is worth. It does
not make the score reproducible, and says so in `caveat`, which the CLI prints
verbatim rather than paraphrasing.
"""

import tomllib
from dataclasses import dataclass
from pathlib import Path

from .errors import GoldenThreadError

RUBRIC_DIR = "rubrics"


@dataclass(frozen=True)
class Dimension:
    id: str
    title: str
    points: int
    asks: str


@dataclass(frozen=True)
class Rubric:
    id: str
    version: str
    title: str
    scale_max: int
    caveat: str
    dimensions: list[Dimension]

    @property
    def ref(self) -> str:
        """How an assessment names the rubric it was made under."""
        return f"{self.id}@{self.version}"

    @property
    def dimension_ids(self) -> set[str]:
        return {d.id for d in self.dimensions}

    @property
    def declared_points(self) -> int:
        return sum(d.points for d in self.dimensions)


def load(source_root: Path, rubric_id: str, version: str) -> Rubric:
    path = source_root / RUBRIC_DIR / f"{rubric_id}-{version}.toml"
    if not path.exists():
        available = sorted(
            p.stem for p in (source_root / RUBRIC_DIR).glob("*.toml")
        ) if (source_root / RUBRIC_DIR).is_dir() else []
        raise GoldenThreadError(
            f"this profile pins rubric {rubric_id}@{version}, which this Golden "
            f"Thread version does not publish. Available: "
            f"{', '.join(available) or 'none'}"
        )
    try:
        with path.open("rb") as handle:
            data = tomllib.load(handle)
    except tomllib.TOMLDecodeError as exc:
        raise GoldenThreadError(f"{path} is not valid TOML: {exc}") from exc

    # The file name and the fields must agree, or the ref recorded in evidence
    # would name a rubric other than the one actually read.
    if data.get("id") != rubric_id or str(data.get("version")) != version:
        raise GoldenThreadError(
            f"{path} declares {data.get('id')}@{data.get('version')} but is "
            f"filed as {rubric_id}@{version}"
        )

    dimensions = [
        Dimension(
            id=d["id"],
            title=d.get("title", d["id"]),
            points=int(d["points"]),
            asks=d.get("asks", "").strip(),
        )
        for d in data.get("dimensions", [])
    ]
    if not dimensions:
        raise GoldenThreadError(f"{path} declares no dimensions")

    rubric = Rubric(
        id=data["id"],
        version=str(data["version"]),
        title=data.get("title", rubric_id),
        scale_max=int(data.get("scale_max", 10)),
        caveat=data.get("caveat", "").strip(),
        dimensions=dimensions,
    )
    if rubric.declared_points != rubric.scale_max:
        raise GoldenThreadError(
            f"{path}: dimensions are worth {rubric.declared_points} point(s) "
            f"but the scale is out of {rubric.scale_max}"
        )
    return rubric
