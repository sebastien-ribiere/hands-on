"""Where Golden Thread keeps things inside a consumer project."""

from pathlib import Path

# Committed. Minimal. Lockfile semantics: what we asked for, what we got.
MANIFEST_NAME = "golden-thread.json"

# Not committed. Cache + recorded evidence, both reproducible from the manifest.
WORK_DIR_NAME = ".golden-thread"
SOURCE_DIR_NAME = "source"
EVIDENCE_NAME = "evidence.json"

# Not committed either. Claims made elsewhere -- by a model, by a person --
# and handed to Golden Thread. Kept apart from evidence.json because the CLI
# produced one file and merely received the other.
ATTESTATIONS_NAME = "attestations.json"


def manifest_path(project: Path) -> Path:
    return project / MANIFEST_NAME


def work_dir(project: Path) -> Path:
    return project / WORK_DIR_NAME


def source_dir(project: Path) -> Path:
    return work_dir(project) / SOURCE_DIR_NAME


def evidence_path(project: Path) -> Path:
    return work_dir(project) / EVIDENCE_NAME


def attestations_path(project: Path) -> Path:
    return work_dir(project) / ATTESTATIONS_NAME
