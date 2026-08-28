"""Check engines.

Rules in the corporate source name a check by string. The engine lives here,
in the CLI, so policy stays declarative and versionable on its own.
"""

from ..errors import GoldenThreadError
from . import layered_dependencies

_ENGINES = {
    layered_dependencies.NAME: layered_dependencies.run,
}


def get(name: str):
    engine = _ENGINES.get(name)
    if engine is None:
        raise GoldenThreadError(
            f"unknown check engine {name!r}. This CLI provides: "
            f"{', '.join(sorted(_ENGINES))}"
        )
    return engine
