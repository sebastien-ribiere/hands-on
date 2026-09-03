#!/usr/bin/env bash
#
# The Definition of Ready, end to end.
#
# Spike 4:  a requirement Golden Thread cannot verify on its own. DOR-001 is
#           satisfied by two claims made elsewhere -- an assessment produced
#           against a versioned rubric, and a decision made by a person -- and
#           by neither of them alone.
#
# The assessments here are canned JSON files so this script is reproducible
# and runs offline. In a real session they come from the spec-readiness skill
# in claude-code-adapter/skills/, which reads the same rubric from the same
# command. Nothing in the CLI knows or cares which produced them: it validates
# the shape, records the provenance, and applies the policy's thresholds.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
gt="${root}/golden-thread-cli/bin/golden-thread"
project="${root}/demo-spellbook"
source_repo="${root}/.demo/golden-thread-source"
mission="${project}/MISSION.md"

step() { printf '\n\033[1m=== %s ===\033[0m\n' "$*"; }
run()  { printf '$ %s\n' "$*"; set +e; "$@"; local rc=$?; set -e; printf '[exit %s]\n' "${rc}"; return 0; }

cleanup() {
  [ -f "${mission}.orig" ] && mv "${mission}.orig" "${mission}"
  return 0
}
trap cleanup EXIT

step "0. Publish the corporate Golden Thread: v0.1.0, then v0.2.0 which adds the DoR"
# v0.2.0 adds the academy-spells-ready profile: the same architecture rule as
# v0.1.0, with the Academy's Definition of Ready in front of it. Adding a DoR
# to a golden path is a policy change and a new tag -- not a new CLI.
rm -rf "${project}/.golden-thread"
"${root}/demo/publish-source.sh"

step "1. Attach the project to the profile that enforces a DoR"
run "${gt}" -C "${project}" init --source "${source_repo}" --ref v0.2.0 \
    --profile academy-spells-ready

step "2. The mission as it arrived"
cat "${mission}"

step "3. Nothing assessed, nobody asked: NOT READY"
# The architecture rule already passes. That is not the headline, because the
# work was never agreed -- answering the second question first would be the
# wrong conversation.
run "${gt}" -C "${project}" verify

step "4. The rubric is policy, versioned and published by the golden path"
run "${gt}" -C "${project}" readiness rubric

step "5. An assessment arrives: 7/10, and two decisions that need a human"
run "${gt}" -C "${project}" readiness assess --input "${root}/demo/assessment-initial.json"

step "6. Still NOT READY -- and the report says which of the two halves is missing"
run "${gt}" -C "${project}" verify

step "7. The human approves anyway. The score is policy; a signature does not move it."
# This is the symmetric proof to the one in step 10. A person saying yes does
# not make a 7 into an 8: the threshold lives in the corporate policy, and
# approving is not the same act as changing it.
run "${gt}" -C "${project}" readiness approve \
    --attestor "mission-owner@academy.invalid" \
    --note "Looks fine to me." \
    --confirm "approve $("${gt}" -C "${project}" readiness rubric --json \
              | python3 -c 'import json,sys; print(json.load(sys.stdin)["subject"]["digest"][7:19])')"
run "${gt}" -C "${project}" verify

step "8. So the developer answers the two decisions, in the mission itself"
cp "${mission}" "${mission}.orig"
cp "${root}/demo/mission-clarified.md" "${mission}"
git --no-pager diff --no-index -- "${mission}.orig" "${mission}" || true

step "9. Both recorded claims were about the OLD text, and neither carries over"
# The assessment and the approval each recorded the digest of the document
# they were made about. An approval is given to a text, not to a file name.
run "${gt}" -C "${project}" verify

step "10. Re-assess the answered mission: 9/10, no blockers, no open decisions"
run "${gt}" -C "${project}" readiness assess --input "${root}/demo/assessment-clarified.json"

step "11. 9/10 and STILL not ready. The score never approves itself."
run "${gt}" -C "${project}" verify

step "12. A human decides, having been shown exactly what they are deciding"
# Interactive by default. --confirm exists for scripts like this one, and
# records the approval as the named attestor's own -- it does not pretend to
# prove that a person typed it. Nothing on a developer machine can.
run "${gt}" -C "${project}" readiness approve \
    --attestor "mission-owner@academy.invalid" \
    --note "Both decisions answered; Water satisfies ARCH-001." \
    --confirm "approve $("${gt}" -C "${project}" readiness rubric --json \
              | python3 -c 'import json,sys; print(json.load(sys.stdin)["subject"]["digest"][7:19])')"

step "13. DOR-READY satisfied, and never as a bare verdict"
run "${gt}" -C "${project}" verify

step "14. The claims on record, with their provenance"
cat "${project}/.golden-thread/attestations.json"

step "15. The same report, machine-readable -- this is what the adapter reads"
run "${gt}" -C "${project}" status --json

printf '\nDemo complete.\n'
