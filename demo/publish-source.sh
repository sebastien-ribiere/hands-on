#!/usr/bin/env bash
#
# Publish the corporate Golden Thread as a tagged Git repository.
#
# In a real organisation this repository already exists on your forge and is
# tagged by whoever owns the golden path. For the hands-on we build it locally
# from golden-thread-source/, so the demo is reproducible from a fresh clone.
#
# Three tags, and the differences between them are the whole point:
#
#   v0.1.0   the academy-spells profile: one architecture rule, ARCH-001
#   v0.2.0   adds a rubric, a DOR-001 rule and an academy-spells-ready profile
#   v0.3.0   adds the Definition of Done: TEST-001, SEC-001, DOC-001,
#            COOKIE-001, and an academy-spells-done profile
#
# Growing a golden path is a policy change published under a new tag. No
# version of the CLI changed between v0.1.0 and v0.2.0, and only v0.3.0 needed
# new engines -- which is the honest boundary: a new *kind* of check is a tool
# change, a new *requirement* is not. A team adopts either by moving the ref
# they pin.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_dir="${root}/golden-thread-source"
published="${root}/.demo/golden-thread-source"

# Everything the Definition of Ready adds. Held out of the v0.1.0 commit so
# that tag really is the golden path before the DoR existed.
DOR_PATHS=(
  "rubrics"
  "rules/DOR-001.toml"
  "profiles/academy-spells-ready.toml"
)

# And everything the Definition of Done adds, held out of both earlier tags.
DOD_PATHS=(
  "rules/TEST-001.toml"
  "rules/SEC-001.toml"
  "rules/DOC-001.toml"
  "rules/COOKIE-001.toml"
  "profiles/academy-spells-done.toml"
)

rm -rf "${published}"
mkdir -p "$(dirname "${published}")"
cp -R "${source_dir}" "${published}"

git -C "${published}" init -q -b main
git -C "${published}" config commit.gpgsign false
git -C "${published}" config tag.gpgsign false
git -C "${published}" config user.name "Golden Thread"
git -C "${published}" config user.email "golden-thread@example.invalid"

held="$(mktemp -d)"
trap 'rm -rf "${held}"' EXIT

# Move a set of paths out of the repository entirely, so they are absent from
# the commit rather than merely renamed inside it.
hold() {
  for path in "$@"; do
    if [ -e "${published}/${path}" ]; then
      mkdir -p "${held}/$(dirname "${path}")"
      mv "${published}/${path}" "${held}/${path}"
    fi
  done
}

restore() {
  for path in "$@"; do
    if [ -e "${held}/${path}" ]; then
      mkdir -p "${published}/$(dirname "${path}")"
      mv "${held}/${path}" "${published}/${path}"
    fi
  done
}

commit_tag() {
  local tag="$1" message="$2" date="$3"
  # Fixed dates so the same content always yields the same commits: the demo
  # output is then byte-for-byte reproducible.
  GIT_AUTHOR_DATE="${date}" GIT_COMMITTER_DATE="${date}" \
    git -C "${published}" add -A
  GIT_AUTHOR_DATE="${date}" GIT_COMMITTER_DATE="${date}" \
    git -C "${published}" commit -q -m "${message}"
  GIT_AUTHOR_DATE="${date}" GIT_COMMITTER_DATE="${date}" \
    git -C "${published}" tag -a "${tag}" -m "Golden Thread ${tag}"
}

# v0.1.0 -- before the Definition of Ready, and long before the DoD.
hold "${DOR_PATHS[@]}" "${DOD_PATHS[@]}"
commit_tag v0.1.0 \
  "Golden Thread v0.1.0: academy-spells, with ARCH-001" \
  "2026-01-01T00:00:00+00:00"

# v0.2.0 -- the Academy publishes a Definition of Ready.
restore "${DOR_PATHS[@]}"
commit_tag v0.2.0 \
  "Golden Thread v0.2.0: academy-spells-ready, with DOR-001 and spec-readiness 1.0.0" \
  "2026-02-01T00:00:00+00:00"

# v0.3.0 -- and a Definition of Done, including one requirement no tool can
# check.
restore "${DOD_PATHS[@]}"
commit_tag v0.3.0 \
  "Golden Thread v0.3.0: academy-spells-done, with TEST-001, SEC-001, DOC-001, COOKIE-001" \
  "2026-03-01T00:00:00+00:00"

echo "Published ${published}"
for tag in v0.1.0 v0.2.0 v0.3.0; do
  echo "${tag}    $(git -C "${published}" rev-parse --short "${tag}^{commit}")"
done
