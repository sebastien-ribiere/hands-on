#!/usr/bin/env bash
# Test d’intégration sur des volumes jetables dédiés, après le build CI.
set -euo pipefail
workspace="golden-thread-workspace-ci-${RANDOM}-$$"
restore="${workspace}-restore"
container="gt-reset-ci-$$"
cleanup() {
  docker rm -f "$container" >/dev/null 2>&1 || true
  while IFS= read -r volume; do
    case "$volume" in "$workspace"|"$workspace"-*) docker volume rm "$volume" >/dev/null;; esac
  done < <(docker volume ls --format '{{.Name}}')
}
trap cleanup EXIT
run_reset() { bash demo/reset-lab.sh --workspace "$workspace" --image golden-thread-lab:test; }
docker run --rm --mount "type=volume,source=$workspace,target=/workspace" \
  --entrypoint bash golden-thread-lab:test -c 'printf "travail à conserver\n" > /workspace/demo-spellbook/avant-reset.txt'
# Un conteneur même arrêté empêche le reset.
docker create --name "$container" --mount "type=volume,source=$workspace,target=/workspace" golden-thread-lab:test >/dev/null
if printf 'reset %s\n' "$workspace" | run_reset; then exit 1; fi
docker rm "$container" >/dev/null
# Une mauvaise confirmation ne change rien.
if printf 'non\n' | run_reset; then exit 1; fi
# Un reset confirmé conserve une sauvegarde et restitue l’état initial.
printf 'reset %s\n' "$workspace" | run_reset
backup=$(docker volume ls --format '{{.Name}}' | grep "^${workspace}-backup-")
test -n "$backup"
docker run --rm --mount "type=volume,source=$workspace,target=/workspace" \
  --entrypoint bash golden-thread-lab:test -c 'test ! -e avant-reset.txt; test -f MISSION.md'
# Récupération réelle de l’archive, y compris le fichier non suivi et les liens Git.
docker volume create "$restore" >/dev/null
docker run --rm --user 0 --workdir / --entrypoint bash \
  --mount "type=volume,source=$backup,target=/backup,readonly,volume-nocopy" \
  --mount "type=volume,source=$restore,target=/restore,volume-nocopy" \
  golden-thread-lab:test -c 'set -e; tar -xpf /backup/workspace.tar -C /restore; grep -q "travail à conserver" /restore/demo-spellbook/avant-reset.txt; test -d /restore/.git; test -L /restore/demo-spellbook/.claude/skills/spec-readiness'
