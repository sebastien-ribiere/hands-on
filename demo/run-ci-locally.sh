#!/usr/bin/env bash
#
# Run the GitLab pipeline, locally, without GitLab.
#
# This is not a simulation of the pipeline. It reads `.gitlab-ci.yml`, takes
# the `image`, `before_script` and `script` GitLab would run, and runs exactly
# those -- in exactly that image, under Docker. If somebody edits the pipeline
# and breaks it, this script breaks with it. A demo that reimplemented the
# pipeline's steps in bash would keep working after the pipeline stopped, which
# is the failure mode worth spending a bit of parsing on to avoid.
#
# It runs against a clean copy of the repository in .demo/ci-workspace, so the
# job starts from the same state a fresh clone would, and nothing it does
# touches your working tree.
#
# Usage:
#   demo/run-ci-locally.sh              # the job as it stands
#   demo/run-ci-locally.sh --job NAME   # a different job
set -uo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
job="golden-thread"
workspace="${root}/.demo/ci-workspace"
generated="${root}/.demo/ci-job.sh"

while [ $# -gt 0 ]; do
  case "$1" in
    --job) job="$2"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

step() { printf '\n\033[1m=== %s ===\033[0m\n' "$*"; }

if ! command -v docker >/dev/null 2>&1; then
  cat >&2 <<'EOF'
This needs Docker: the point is to run the job in the image the pipeline
declares, not in something that happens to resemble it. Without Docker there
is no honest way to claim the pipeline was reproduced, so this script stops
rather than running something else and calling it the same thing.
EOF
  exit 2
fi

step "1. Read the real .gitlab-ci.yml"
image="$(python3 "${root}/demo/gitlab_job.py" "${root}/.gitlab-ci.yml" "${job}" --image)"
python3 "${root}/demo/gitlab_job.py" "${root}/.gitlab-ci.yml" "${job}" --script > "${generated}"
artifacts="$(python3 "${root}/demo/gitlab_job.py" "${root}/.gitlab-ci.yml" "${job}" --artifacts)"
echo "job       ${job}"
echo "image     ${image}"
echo "artifacts ${artifacts}"

step "2. Stage a clean copy of the repository"
# Excluding everything a fresh clone would not have: the policy cache, the
# recorded evidence, the local toolchain, and this repository's own history.
rm -rf "${workspace}"
mkdir -p "${workspace}"
tar -C "${root}" \
    --exclude=.git \
    --exclude=.demo \
    --exclude=.pytest_cache \
    --exclude=__pycache__ \
    --exclude='*.pyc' \
    --exclude=demo-spellbook/.golden-thread \
    -cf - . | tar -C "${workspace}" -xf -
cp "${generated}" "${workspace}/ci-job.sh"
echo "staged in ${workspace}"
cat <<'EOF'

Note, because it matters for what this proves: GitLab checks out a commit,
this stages your working tree. The difference shows up for exactly one file --
demo-spellbook/golden-thread-attestations.json, which a real project commits
and this demo gitignores because its content is rewritten every run. A real
pipeline sees it because it is in the repository; this one sees it because it
is on disk.
EOF

step "3. Run the job in ${image}"
printf 'These are the pipeline'"'"'s own lines, not a re-implementation of them:\n\n'
sed 's/^/    /' "${generated}"
printf '\n'

docker run --rm \
  -v "${workspace}:/builds/hands-on" \
  -w /builds/hands-on \
  "${image}" \
  bash -e ci-job.sh
status=$?

step "4. The job's outcome"
printf 'job exit code: %s\n' "${status}"
if [ "${status}" -eq 0 ]; then
  printf 'Pipeline green.\n'
else
  printf 'Pipeline red. The job log above says which of the two happened:\n'
  printf '  - golden-thread could not run (exit 2), or\n'
  printf '  - it computed a state, and this project chose to block on it.\n'
fi

step "5. The artifact GitLab would keep"
for path in ${artifacts}; do
  if [ -f "${workspace}/${path}" ]; then
    cp "${workspace}/${path}" "${root}/${path}"
    printf '%s (kept at ./%s)\n\n' "${path}" "${path}"
    python3 - "${root}/${path}" <<'PY'
import json, sys
report = json.load(open(sys.argv[1]))
print(f"  reportVersion  {report['reportVersion']}")
print(f"  pathStatus     {report['pathStatus']}  (exit {report['exitCode']})")
print(f"  policy         {report['goldenThread']['ref']} @ "
      f"{report['goldenThread']['revision'][:12]}")
for requirement in report["requirements"]:
    print(f"  {requirement['reportedStatus']:<7} {requirement['requirement']}")
PY
  else
    printf '%s -- not produced\n' "${path}"
  fi
done

exit "${status}"
