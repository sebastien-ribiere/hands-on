"""Check engines.

Rules in the corporate source name a check by string. The engine lives here,
in the CLI, so policy stays declarative and versionable on its own.

An engine exposes two entry points:

    run(rule, project)      produce a result -- this is what verification does
    subject(rule, project)  identify what it would read, without reading it as
                            a check -- this is how `status` decides whether an
                            existing record still applies

and declares one thing about itself: its `kind`.

    CODE       the engine examines the project's code and reaches its own
               verdict. A failure is a defect in what was built.
    READINESS  the engine examines claims made *about* the work before it
               started, and can never reach a verdict alone. A failure means
               the work was not agreed, not that it is broken.
    ATTESTED   the engine reaches no verdict either: it reports whether a named
               person made a claim about this version of the work. A failure
               means a piece of the Definition of Done has not been done --
               ordinary OFF PATH, unlike READINESS.

The distinction is the engine's to make, not the policy's: whether a check can
conclude on its own is a property of how it is implemented, and a rule author
must not be able to claim otherwise in a TOML file. `status` uses it to say
NOT READY where it would otherwise have said OFF PATH -- two different
problems that deserve two different sentences. The commands use it too: `attest`
asks the pinned policy which of its rules are attestable rather than knowing
any requirement id itself.
"""

from dataclasses import dataclass
from typing import Callable

from ..errors import GoldenThreadError
from . import (
    doc_stamp,
    external_command,
    human_attestation,
    layered_dependencies,
    security_scan,
    spec_readiness,
)

CODE = "code"
READINESS = "readiness"
ATTESTED = "attested"


@dataclass(frozen=True)
class Engine:
    name: str
    run: Callable
    subject: Callable
    kind: str = CODE


def _engine(module, kind: str = CODE) -> Engine:
    return Engine(name=module.NAME, run=module.run, subject=module.subject, kind=kind)


_ENGINES = {
    layered_dependencies.NAME: _engine(layered_dependencies, CODE),
    external_command.NAME: _engine(external_command, CODE),
    security_scan.NAME: _engine(security_scan, CODE),
    doc_stamp.NAME: _engine(doc_stamp, CODE),
    spec_readiness.NAME: _engine(spec_readiness, READINESS),
    human_attestation.NAME: _engine(human_attestation, ATTESTED),
}


def get(name: str) -> Engine:
    engine = _ENGINES.get(name)
    if engine is None:
        raise GoldenThreadError(
            f"unknown check engine {name!r}. This CLI provides: "
            f"{', '.join(sorted(_ENGINES))}"
        )
    return engine


def kind_of(name: str) -> str:
    """The kind of an engine named in a record, tolerating an unknown name.

    A record may name an engine this CLI no longer provides. That is a reason
    to fall back to the ordinary kind, not to crash while reporting status.
    """
    engine = _ENGINES.get(name)
    return engine.kind if engine else CODE
