#!/usr/bin/env bash
# Reset volontaire du workspace Docker ; aucune opération sur le volume Claude.
set -euo pipefail

image=ghcr.io/sebastien-ribiere/hands-on:lab
workspace=golden-thread-workspace
usage() {
  cat <<'HELP'
Usage : bash demo/reset-lab.sh [--image IMAGE] [--workspace VOLUME]
À lancer sur votre poste, après avoir quitté le conteneur du lab.
Sauvegarde le workspace dans un volume Docker, puis restaure l’état de l’image.
Le volume Claude reste intact. Confirmation interactive obligatoire.
L’image locale est utilisée ; faites docker pull au préalable pour la mettre à jour.
HELP
}
fail() { printf 'Erreur : %s\n' "$*" >&2; exit 1; }
while [ "$#" -gt 0 ]; do
  case "$1" in
    --image|--workspace)
      [ "$#" -ge 2 ] && [ -n "$2" ] || fail "Valeur manquante pour $1"
      case "$1" in --image) image=$2;; --workspace) workspace=$2;; esac
      shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) fail "Option inconnue : $1" ;;
  esac
done
# Limite les erreurs de cible, notamment la sélection du volume d’authentification.
[[ "$workspace" =~ ^golden-thread-workspace(-[a-zA-Z0-9][a-zA-Z0-9_.-]*)?$ ]] ||
  fail 'Le nom doit être golden-thread-workspace ou golden-thread-workspace-<suffixe>.'
[ "${GOLDEN_THREAD_LAB:-0}" != 1 ] || fail 'Exécutez ce script sur le poste, hors du lab.'
command -v docker >/dev/null || fail 'Docker est nécessaire sur le poste.'
docker info >/dev/null 2>&1 || fail 'Docker ne répond pas.'
image_id=$(docker image inspect --format '{{.Id}}' "$image") ||
  fail "Image absente. Téléchargez-la d’abord : docker pull $image"

# Vérifie l’image avant de toucher au volume ; fige sa résolution pour ce reset.
docker run --rm --network none --entrypoint bash "$image_id" -c '
  set -e
  test -f /workspace/demo-spellbook/MISSION.md
  test ! -e /workspace/demo-spellbook/golden-thread.json
  test ! -e /workspace/demo-spellbook/.golden-thread/evidence.json
  git -C /workspace/.demo/golden-thread-source rev-parse --verify v0.3.0^{commit} >/dev/null
' || fail 'Cette image ne contient pas un lab initial valide.'

assert_unused() {
  local users
  users=$(docker ps -aq --filter "volume=$workspace") || fail 'Impossible de vérifier les conteneurs.'
  [ -z "$users" ] || fail "Le volume est référencé par un conteneur : $users. Quittez le lab ; retirez vous-même tout conteneur arrêté qui le conserve."
}
assert_unused
volumes=$(docker volume ls --format '{{.Name}}')
exists=false
while IFS= read -r name; do
  [ "$name" != "$workspace" ] || exists=true
done <<< "$volumes"
if "$exists"; then
  kind=$(docker volume inspect --format '{{.Driver}} {{json .Options}}' "$workspace")
  [[ "$kind" == 'local null' || "$kind" == 'local {}' ]] || fail 'Seuls les volumes locaux standards sont acceptés.'
fi
printf 'Workspace : %s\nImage : %s\nSHA image : %s\n' "$workspace" "$image" "$image_id"
printf 'Le code, la mission, les preuves et les décisions repartiront de zéro.\n'
printf 'Le travail existant sera archivé dans un volume séparé. La connexion Claude sera conservée.\n'
printf 'Saisissez « reset %s » pour continuer : ' "$workspace"
IFS= read -r answer || fail 'Aucune confirmation reçue ; reset annulé.'
[ "$answer" = "reset $workspace" ] || fail 'Confirmation différente ; reset annulé.'
assert_unused

backup=''
trap 'printf "Reset interrompu. Sauvegarde éventuelle : %s. Consultez LAB.md avant de reprendre.\n" "${backup:-aucune}" >&2' ERR
if "$exists"; then
  backup="${workspace}-backup-$(date -u +%Y%m%dT%H%M%SZ)-$$-${RANDOM}"
  if docker volume inspect "$backup" >/dev/null 2>&1; then
    fail "Le volume de sauvegarde existe déjà : $backup"
  fi
  docker volume create --label golden-thread.role=reset-backup "$backup" >/dev/null
  printf 'Sauvegarde : %s\n' "$backup"
  # L’archive conserve les fichiers cachés, les liens, les permissions et les UID.
  # tar compare l’archive au workspace avant toute suppression du volume original.
  docker run --rm --network none --user 0 --workdir / --entrypoint bash \
    --mount "type=volume,source=$workspace,target=/source,readonly,volume-nocopy" \
    --mount "type=volume,source=$backup,target=/backup,volume-nocopy" \
    "$image_id" -c 'set -e; tar -cpf /backup/workspace.tar -C /source .; tar -df /backup/workspace.tar -C /source'
  assert_unused
  docker volume rm "$workspace" >/dev/null
fi
# Docker peuple le volume vide depuis /workspace dans l’image.
docker volume create "$workspace" >/dev/null
docker run --rm --network none --entrypoint bash \
  --mount "type=volume,source=$workspace,target=/workspace" \
  "$image_id" -c 'set -e; test -f MISSION.md; test ! -e golden-thread.json; test ! -e .golden-thread/evidence.json; test -z "$(git -C /workspace status --porcelain)"'
trap - ERR
printf '\nReset terminé. Workspace prêt : %s\n' "$workspace"
[ -z "$backup" ] || printf 'Sauvegarde conservée : %s (workspace.tar)\n' "$backup"
printf 'Relancez le lab avec ce workspace et votre volume Claude habituel.\n'
printf 'Utilisez claude pour une nouvelle conversation, plutôt que claude --continue.\n'
