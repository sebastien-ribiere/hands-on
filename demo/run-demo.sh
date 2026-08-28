#!/usr/bin/env bash
#
# The Spike 1 demonstration, end to end:
#   attach -> verify (ON PATH) -> deviate -> verify (OFF PATH) -> repair
#
# No AI agent is involved at any point.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
gt="${root}/golden-thread-cli/bin/golden-thread"
project="${root}/demo-spellbook"
source_repo="${root}/.demo/golden-thread-source"
ward="${project}/src/spells/protection/ward.py"

step() { printf '\n\033[1m=== %s ===\033[0m\n' "$*"; }
run()  { printf '$ %s\n' "$*"; set +e; "$@"; local rc=$?; set -e; printf '[exit %s]\n' "${rc}"; return 0; }

step "0. Publish the corporate Golden Thread and tag it v0.1.0"
"${root}/demo/publish-source.sh" v0.1.0

step "1. Attach the project to the Golden Thread"
run "${gt}" -C "${project}" init --source "${source_repo}" --ref v0.1.0

step "2. The project knows its version and profile -- nothing verified yet"
run "${gt}" -C "${project}" status

step "3. The manifest is minimal, and pins the resolved commit"
cat "${project}/golden-thread.json"

step "4. Verify: the architecture rule really runs"
run "${gt}" -C "${project}" verify

step "5. Introduce a real Fire dependency in a protection spell"
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

step "6. Verify again: the deviation is detected"
run "${gt}" -C "${project}" verify

step "7. Status now reports OFF PATH"
run "${gt}" -C "${project}" status

step "8. Remove the deviation"
mv "${ward}.orig" "${ward}"
run "${gt}" -C "${project}" verify

step "9. Back ON PATH"
run "${gt}" -C "${project}" status

printf '\nDemo complete.\n'
