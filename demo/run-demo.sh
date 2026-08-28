#!/usr/bin/env bash
#
# The demonstration, end to end.
#
# Spike 1:  attach -> verify (ON PATH) -> deviate -> verify (OFF PATH) -> repair
# Spike 2:  every verdict now carries the evidence it came from, and evidence
#           that no longer describes the code is reported as STALE rather than
#           quietly reused.
#
# No AI agent is involved at any point.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
gt="${root}/golden-thread-cli/bin/golden-thread"
project="${root}/demo-spellbook"
source_repo="${root}/.demo/golden-thread-source"
ward="${project}/src/spells/protection/ward.py"
shield="${project}/src/spells/protection/shield.py"

step() { printf '\n\033[1m=== %s ===\033[0m\n' "$*"; }
run()  { printf '$ %s\n' "$*"; set +e; "$@"; local rc=$?; set -e; printf '[exit %s]\n' "${rc}"; return 0; }

cleanup() {
  [ -f "${ward}.orig" ] && mv "${ward}.orig" "${ward}"
  [ -f "${shield}.orig" ] && mv "${shield}.orig" "${shield}"
  rm -f "${project}/NOTES.md"
  return 0
}
trap cleanup EXIT

step "0. Publish the corporate Golden Thread and tag it v0.1.0"
# Start from a clean slate: the cache and the recorded evidence are both
# disposable, so the demo runs the same way on a fresh clone.
rm -rf "${project}/.golden-thread"
"${root}/demo/publish-source.sh" v0.1.0

step "1. Attach the project to the Golden Thread"
run "${gt}" -C "${project}" init --source "${source_repo}" --ref v0.1.0

step "2. Nothing has been verified yet -- and that is said, not assumed"
run "${gt}" -C "${project}" status

step "3. The manifest is minimal, and pins the resolved commit"
cat "${project}/golden-thread.json"

step "4. Verify: the architecture rule really runs, and produces evidence"
run "${gt}" -C "${project}" verify

step "5. The evidence on record -- a claim with its provenance attached"
cat "${project}/.golden-thread/evidence.json"

step "6. Edit a verified file, harmlessly, and do NOT re-verify"
cp "${shield}" "${shield}.orig"
printf '\n\n# A later thought. It changes nothing about Fire.\n' >> "${shield}"
printf 'The recorded evidence describes code that no longer exists.\n'
run "${gt}" -C "${project}" status

step "7. Re-verify: a current verdict is restored"
run "${gt}" -C "${project}" verify

step "8. Edit something the rule never read -- no false invalidation"
printf 'Prose, not code.\n' > "${project}/NOTES.md"
run "${gt}" -C "${project}" status

step "9. Introduce a real Fire dependency in a protection spell"
cp "${ward}" "${ward}.orig"
python3 - "${ward}" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
text = path.read_text()
text = text.replace(
    "from ..elements import water\n",
    "from ..elements import water\nfrom ..elements import fire\n",
)
text += '''

def counterattack(target: str) -> str:
    """OFF PATH: a protection spell reaching into Fire."""
    return fire.scorch(target)
'''
path.write_text(text)
PY
git --no-pager diff --no-index -- "${ward}.orig" "${ward}" || true

step "10. Verify again: the deviation is detected and located"
run "${gt}" -C "${project}" verify

step "11. Repair the code -- and do NOT re-verify"
mv "${ward}.orig" "${ward}"
printf 'The recorded FAIL is no longer true, but nothing has proved the fix.\n'
printf 'Golden Thread says STALE: neither ON PATH nor OFF PATH is known.\n'
run "${gt}" -C "${project}" status

step "12. Verify: back ON PATH, on evidence produced from this exact code"
run "${gt}" -C "${project}" verify

step "13. The same report, machine-readable"
run "${gt}" -C "${project}" status --json

printf '\nDemo complete.\n'
