"""Where Golden Thread keeps things inside a consumer project."""

from pathlib import Path

# Committed. Minimal. Lockfile semantics: what we asked for, what we got.
MANIFEST_NAME = "golden-thread.json"

# Not committed. Cache + recorded evidence, both reproducible from the manifest.
WORK_DIR_NAME = ".golden-thread"
SOURCE_DIR_NAME = "source"
EVIDENCE_NAME = "evidence.json"

# Committed, and beside the manifest rather than inside the cache. Claims made
# elsewhere -- by a model, by a person -- and handed to Golden Thread.
#
# The split is by what can be rebuilt, and that is the whole reason this file
# is not in .golden-thread/. Everything in there is disposable: `verify`
# reproduces the evidence and the manifest reproduces the policy cache. An
# attestation is the one thing in this system that nothing can regenerate --
# delete it and the only recourse is to go and ask a person again.
#
# It also has to travel. A pipeline that cannot see the approval reports the
# work as un-agreed, which is true of that machine and false of the project.
# Committing an attestation makes it visible to CI and visible in review; it
# does not make it authenticated, and nothing here claims otherwise.
ATTESTATIONS_NAME = "golden-thread-attestations.json"


def manifest_path(project: Path) -> Path:
    return project / MANIFEST_NAME


def work_dir(project: Path) -> Path:
    return project / WORK_DIR_NAME


def source_dir(project: Path) -> Path:
    return work_dir(project) / SOURCE_DIR_NAME


def evidence_path(project: Path) -> Path:
    return work_dir(project) / EVIDENCE_NAME


def attestations_path(project: Path) -> Path:
    return project / ATTESTATIONS_NAME
