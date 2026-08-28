#!/usr/bin/env bash
#
# Publish the corporate Golden Thread as a tagged Git repository.
#
# In a real organisation this repository already exists on your forge and is
# tagged by whoever owns the golden path. For the hands-on we build it locally
# from golden-thread-source/, so the demo is reproducible from a fresh clone.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
published="${root}/.demo/golden-thread-source"
version="${1:-v0.1.0}"

rm -rf "${published}"
mkdir -p "$(dirname "${published}")"
cp -R "${root}/golden-thread-source" "${published}"

git -C "${published}" init -q -b main
git -C "${published}" config commit.gpgsign false
git -C "${published}" config tag.gpgsign false
git -C "${published}" config user.name "Golden Thread"
git -C "${published}" config user.email "golden-thread@example.invalid"
git -C "${published}" add -A
# Fixed dates so the same content always yields the same commit: the
# demo output is then byte-for-byte reproducible.
export GIT_AUTHOR_DATE="2026-01-01T00:00:00+00:00"
export GIT_COMMITTER_DATE="2026-01-01T00:00:00+00:00"
git -C "${published}" commit -q -m "Golden Thread ${version}: academy-spells profile with ARCH-001"
git -C "${published}" tag -a "${version}" -m "Golden Thread ${version}"

echo "Published ${published}"
echo "Tag       ${version}"
echo "Commit    $(git -C "${published}" rev-parse "${version}^{commit}")"
