#!/usr/bin/env bash
#
# The Definition of Done, end to end.
#
# Spike 5: five requirements, five different kinds of evidence, and one of them
# deliberately unverifiable.
#
#   TEST-001    a deterministic command, and its exit code
#   ARCH-001    the real import graph            (Spike 1)
#   SEC-001     a real security analyser, bandit, and its own findings
#   DOC-001     a document that says which code it describes
#   COOKIE-001  a person's word, and nothing else
#
# The demonstration walks the project through: green, an architecture
# violation, a security defect, a missing attestation, repair, and finally the
# GitLab pipeline replaying the whole thing with no agent involved.
#
# No AI agent is involved at any point in this script either.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
gt="${root}/golden-thread-cli/bin/golden-thread"
project="${root}/demo-spellbook"
source_repo="../.demo/golden-thread-source"
ward="${project}/src/spells/protection/ward.py"
mission="${project}/MISSION.md"
architecture="${project}/docs/ARCHITECTURE.md"

# TEST-001 runs pytest and SEC-001 runs bandit. They are the project's
# toolchain, not Golden Thread's: the CLI is stdlib-only and shells out to
# whatever the policy names.
export PATH="${root}/.demo/venv/bin:${PATH}"

step() { printf '\n\033[1m=== %s ===\033[0m\n' "$*"; }
run()  { printf '$ %s\n' "$*"; set +e; "$@"; local rc=$?; set -e; printf '[exit %s]\n' "${rc}"; return 0; }

cleanup() {
  for file in "${ward}" "${mission}" "${architecture}"; do
    [ -f "${file}.orig" ] && mv "${file}.orig" "${file}"
  done
  return 0
}
trap cleanup EXIT

# The confirmation phrases are derived from the subject digest, so a script
# cannot hardcode them: they change with the work. These read them back from
# the CLI, exactly as a human would read them off the screen.
approval_phrase() {
  "${gt}" -C "${project}" readiness rubric --json \
    | python3 -c 'import json,sys; print("approve " + json.load(sys.stdin)["subject"]["digest"][7:19])'
}
attest_phrase() {
  "${gt}" -C "${project}" attest COOKIE-001 --show \
    | sed -n "s/.*--confirm '\(.*\)'/\1/p"
}

step "0. Publish the corporate golden path, and install the project toolchain"
# v0.3.0 adds the Definition of Done: four new rules and a profile. Two of the
# four needed a new check engine in the CLI, which is the honest boundary --
# a new *kind* of check is a tool change, a new *requirement* is not.
rm -rf "${project}/.golden-thread" "${project}/golden-thread-attestations.json"
"${root}/demo/publish-source.sh"
"${root}/demo/install-toolchain.sh"

step "1. Attach the project to the profile that carries the whole contract"
# The documentation starts unstamped, which is the honest starting state for a
# team the day they adopt a requirement that did not exist yesterday: the file
# is there, it has simply never made a claim about which code it describes.
cp "${architecture}" "${architecture}.orig"
grep -v "golden-thread: describes" "${architecture}.orig" > "${architecture}"
run "${gt}" -C "${project}" init --source "${source_repo}" --ref v0.3.0 \
    --profile academy-spells-done

step "2. The manifest is committed, and pins a commit rather than a tag"
# This is what CI reads. The source is relative to the project, so the file
# means the same thing on every machine -- including one with no developer on
# it to run `init`.
cat "${project}/golden-thread.json"

step "3. Nothing done, nothing agreed"
# Six requirements. The headline is NOT READY rather than OFF PATH because a
# readiness requirement is a precondition on the work: saying "your tests fail"
# to someone whose mission was never agreed answers the second question first.
run "${gt}" -C "${project}" verify

step "4. Satisfy the Definition of Ready first (Spike 4, unchanged)"
cp "${mission}" "${mission}.orig"
cp "${root}/demo/mission-clarified.md" "${mission}"
run "${gt}" -C "${project}" readiness assess \
    --input "${root}/demo/assessment-clarified.json"
run "${gt}" -C "${project}" readiness approve \
    --attestor "mission-owner@academy.invalid" \
    --note "Both decisions answered; Water satisfies ARCH-001." \
    --confirm "$(approval_phrase)"

step "5. Ready. Now what is left is the Definition of Done"
# The headline flips from NOT READY to OFF PATH, and that is the point of
# ranking them: the question has changed from "was this agreed?" to "is this
# finished?".
run "${gt}" -C "${project}" verify

step "6. The documentation says which code it describes"
# DOC-001 is not "a doc exists" and not "the docs changed in the same commit".
# The document carries the digest of the code it describes, and that claim is
# checked. It proves somebody re-stamped it against this code -- not that the
# prose is right, and the CLI says so every time.
run "${gt}" -C "${project}" docs stamp

step "7. And somebody has to have made the cookies"
run "${gt}" -C "${project}" attest COOKIE-001 --show
run "${gt}" -C "${project}" attest COOKIE-001 \
    --attestor "seb@academy.invalid" \
    --note "Chocolate chip. 24 of them. Shared at the Tuesday review." \
    --confirm "$(attest_phrase)"

step "8. GREEN: every requirement, with the evidence each one came from"
run "${gt}" -C "${project}" verify

step "9. DEVIATION 1 -- a protection spell reaches into Fire"
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
run "${gt}" -C "${project}" verify

step "10. One edit, and three requirements lost their basis"
printf 'ARCH-001 failed on the import graph. But COOKIE-001 and DOC-001 also\n'
printf 'stopped applying: the attestation was made about a different version of\n'
printf 'src/, and the stamp describes code that is no longer there. A claim is\n'
printf 'tied to what it was made about -- for a person exactly as for a rule.\n'

step "11. REPAIR -- and the recorded FAIL is not silently kept either"
mv "${ward}.orig" "${ward}"
run "${gt}" -C "${project}" status
run "${gt}" -C "${project}" docs stamp
run "${gt}" -C "${project}" attest COOKIE-001 \
    --attestor "seb@academy.invalid" --note "Fresh batch." \
    --confirm "$(attest_phrase)"
run "${gt}" -C "${project}" verify

step "12. DEVIATION 2 -- a real security defect, found by a real analyser"
# A ward that evaluates whatever incantation the caster hands it. bandit finds
# this on its own: Golden Thread does not know what eval() is.
cp "${ward}" "${ward}.orig"
cat >> "${ward}" <<'PY'


def improvise(incantation: str) -> str:
    """Let the caster supply their own incantation."""
    return f"ward improvised: {eval(incantation)}"
PY
run "${gt}" -C "${project}" verify

step "13. The finding is the analyser's, word for word"
printf 'B307, MEDIUM, and a link to bandit'"'"'s own documentation. Golden Thread\n'
printf 'copied it out and applied one thing of its own: the threshold this\n'
printf 'profile sets, which is policy the Academy versioned and not a default\n'
printf 'the tool picked.\n'

step "14. REPAIR"
mv "${ward}.orig" "${ward}"
run "${gt}" -C "${project}" docs stamp
run "${gt}" -C "${project}" attest COOKIE-001 \
    --attestor "seb@academy.invalid" --note "Fresh batch, again." \
    --confirm "$(attest_phrase)"
run "${gt}" -C "${project}" verify

step "15. DEVIATION 3 -- nobody made the cookies"
# Nothing wrong with the code at all. Every mechanical check passes. The
# project is still not done, and the report says so without inventing a defect
# to point at.
rm -f "${project}/golden-thread-attestations.json.bak"
cp "${project}/golden-thread-attestations.json" \
   "${project}/golden-thread-attestations.json.bak"
python3 - "${project}/golden-thread-attestations.json" <<'PY'
import json, sys
from pathlib import Path

path = Path(sys.argv[1])
data = json.loads(path.read_text())
data["attestations"] = [
    a for a in data["attestations"] if a["requirement"] != "COOKIE-001"
]
path.write_text(json.dumps(data, indent=2) + "\n")
PY
run "${gt}" -C "${project}" verify

step "16. REPAIR -- and this one cannot be automated, by construction"
mv "${project}/golden-thread-attestations.json.bak" \
   "${project}/golden-thread-attestations.json"
run "${gt}" -C "${project}" verify

step "17. The machine-readable report -- this is the CI artifact"
run "${gt}" -C "${project}" status --json

step "18. And the GitLab pipeline replays all of it, with no agent"
printf 'The pipeline reads the committed manifest, restores the pinned policy,\n'
printf 'installs pytest and bandit, and runs the same verification. Nothing in\n'
printf 'it has heard of an AI harness.\n\n'
run "${root}/demo/run-ci-locally.sh"

printf '\nDemo complete.\n'
