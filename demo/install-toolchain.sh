#!/usr/bin/env bash
#
# The tools the golden path expects a project to have.
#
# TEST-001 runs pytest and SEC-001 runs bandit. Neither is a Golden Thread
# dependency: the CLI is stdlib-only and shells out to whatever the policy
# names. They are this *project's* toolchain, and a project that does not have
# them installed gets ERROR -- "this was not checked" -- rather than a pass.
#
# In CI these come from a `pip install` line in .gitlab-ci.yml. Locally they go
# into .demo/venv, which is disposable and gitignored, so nothing is installed
# into the machine running the hands-on.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
venv="${root}/.demo/venv"

# Pinned, because "a real security analyser ran" means little without saying
# which one. The version is recorded in the evidence through the argv, and the
# analyser names itself in every finding.
BANDIT_VERSION="1.9.4"
PYTEST_VERSION="8.3.4"

# Not part of the golden path at all: demo/gitlab_job.py reads .gitlab-ci.yml
# so the local pipeline run executes the pipeline's own lines. bandit happens
# to pull PyYAML in today, and relying on that would leave the demo runner
# breaking for a reason nobody could guess the day it stops.
PYYAML_VERSION="6.0.2"

if [ ! -x "${venv}/bin/python3" ]; then
  python3 -m venv "${venv}"
fi

"${venv}/bin/pip" install --quiet --disable-pip-version-check \
  "bandit==${BANDIT_VERSION}" "pytest==${PYTEST_VERSION}" "PyYAML==${PYYAML_VERSION}"

echo "Toolchain ready in ${venv}"
echo "  $("${venv}/bin/bandit" --version 2>&1 | head -1)"
echo "  pytest $("${venv}/bin/pytest" --version 2>&1 | head -1 | awk '{print $2}')"
echo
echo "Put it on PATH for the demo:"
echo "  export PATH=\"${venv}/bin:\$PATH\""
