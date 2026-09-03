#!/usr/bin/env bash
#
# Publish the corporate Golden Thread as a tagged Git repository.
#
# In a real organisation this repository already exists on your forge and is
# tagged by whoever owns the golden path. For the hands-on we build it locally
# from golden-thread-source/, so the demo is reproducible from a fresh clone.
#
# Two tags, and the difference between them is the whole point:
#
#   v0.1.0   the academy-spells profile: one architecture rule, ARCH-001
#   v0.2.0   adds a rubric, a DOR-001 rule and an academy-spells-ready profile
#
# Adding a Definition of Ready to a golden path is a policy change published
# under a new tag. No version of the CLI changed between these two tags, and a
# team adopts the DoR by moving the ref they pin -- which is why these are
# genuinely two commits here rather than one commit with two labels on it.
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

rm -rf "${published}"
mkdir -p "$(dirname "${published}")"
cp -R "${source_dir}" "${published}"

git -C "${published}" init -q -b main
git -C "${published}" config commit.gpgsign false
git -C "${published}" config tag.gpgsign false
git -C "${published}" config user.name "Golden Thread"
git -C "${published}" config user.email "golden-thread@example.invalid"

# Fixed dates so the same content always yields the same commits: the demo
# output is then byte-for-byte reproducible.
export GIT_AUTHOR_DATE="2026-01-01T00:00:00+00:00"
export GIT_COMMITTER_DATE="2026-01-01T00:00:00+00:00"

# v0.1.0 -- before the Definition of Ready. The held-back paths go outside
# the repository entirely, so they are absent from this commit rather than
# merely renamed inside it.
held="$(mktemp -d)"
trap 'rm -rf "${held}"' EXIT
staged=()
for path in "${DOR_PATHS[@]}"; do
  if [ -e "${published}/${path}" ]; then
    mkdir -p "${held}/$(dirname "${path}")"
    mv "${published}/${path}" "${held}/${path}"
    staged+=("${path}")
  fi
done
git -C "${published}" add -A
git -C "${published}" commit -q -m "Golden Thread v0.1.0: academy-spells, with ARCH-001"
git -C "${published}" tag -a v0.1.0 -m "Golden Thread v0.1.0"

# v0.2.0 -- the Academy publishes a Definition of Ready.
export GIT_AUTHOR_DATE="2026-02-01T00:00:00+00:00"
export GIT_COMMITTER_DATE="2026-02-01T00:00:00+00:00"
for path in "${staged[@]}"; do
  mkdir -p "${published}/$(dirname "${path}")"
  mv "${held}/${path}" "${published}/${path}"
done
git -C "${published}" add -A
git -C "${published}" commit -q -m \
  "Golden Thread v0.2.0: academy-spells-ready, with DOR-001 and spec-readiness 1.0.0"
git -C "${published}" tag -a v0.2.0 -m "Golden Thread v0.2.0"

echo "Published ${published}"
echo "v0.1.0    $(git -C "${published}" rev-parse --short 'v0.1.0^{commit}')  academy-spells"
echo "v0.2.0    $(git -C "${published}" rev-parse --short 'v0.2.0^{commit}')  academy-spells-ready (+ DOR-001)"
