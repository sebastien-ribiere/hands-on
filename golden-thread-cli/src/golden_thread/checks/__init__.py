"""Check engines.

Rules in the corporate source name a check by string. The engine lives here,
in the CLI, so policy stays declarative and versionable on its own.

An engine exposes two entry points:

    run(rule, project)      produce a result -- this is what verification does
    subject(rule, project)  identify what it would read, without reading it as
                            a check -- this is how `status` decides whether an
                            existing record still applies
"""

from dataclasses import dataclass
from typing import Callable

from ..errors import GoldenThreadError
from . import layered_dependencies


@dataclass(frozen=True)
class Engine:
    name: str
    run: Callable
    subject: Callable


_ENGINES = {
    layered_dependencies.NAME: Engine(
        name=layered_dependencies.NAME,
        run=layered_dependencies.run,
        subject=layered_dependencies.subject,
    ),
}


def get(name: str) -> Engine:
    engine = _ENGINES.get(name)
    if engine is None:
        raise GoldenThreadError(
            f"unknown check engine {name!r}. This CLI provides: "
            f"{', '.join(sorted(_ENGINES))}"
        )
    return engine
