# Golden Thread — démarrer le lab

Une fois connecté, ouvrez le [README participant](demo-spellbook/README.md),
puis le [guide participant](GUIDE-PARTICIPANT.md) :
parcours, prompts, résultats attendus et points de reprise.

Le parcours officiel s'exécute dans un conteneur. Le poste du participant n'a
pas besoin de Python, de `golden-thread`, de Bandit, de pytest ni de scripts de
setup locaux.

## Prérequis

- Docker Desktop / Docker Engine ;
- un compte permettant d'utiliser Claude Code ;
- un accès réseau pour télécharger l'image et pour Claude.

## Démarrer

```bash
docker run --rm -it \
  -v golden-thread-workspace:/workspace \
  -v golden-thread-claude:/home/apprentice/.claude \
  ghcr.io/sebastien-ribiere/hands-on:lab
```

Le terminal s'ouvre directement dans :

```text
/workspace/demo-spellbook
```

Le volume `golden-thread-workspace` conserve le travail du hands-on entre deux
conteneurs. Le volume `golden-thread-claude` conserve la connexion et les
réglages Claude Code.

Au premier lancement de Claude Code :

```bash
claude
```

Dans un conteneur, le retour OAuth du navigateur peut ne pas rejoindre le CLI.
Claude affiche alors un code de connexion à recopier dans le terminal ; c'est le
comportement prévu par Claude Code pour les environnements conteneurisés.

## Ce qui est déjà prêt

Dans le conteneur :

```bash
command -v golden-thread
command -v claude
bandit --version
pytest --version
```

Le Golden Thread corporate de démonstration est déjà publié avec ses tags
`v0.1.0`, `v0.2.0` et `v0.3.0` dans :

```text
/workspace/.demo/golden-thread-source
```

Comme on se trouve déjà dans `demo-spellbook`, l'attachement ne mélange plus
un projet ciblé avec un chemin relatif calculé depuis un autre répertoire :

```bash
golden-thread init \
  --source ../.demo/golden-thread-source \
  --ref v0.1.0
```

## Repartir de zéro

Pour une nouvelle répétition, le script [demo/reset-lab.sh](demo/reset-lab.sh)
remet le workspace à l’état initial de l’image. Il archive d’abord votre travail
(code, mission, historique Git, preuves et attestations) dans un volume Docker
séparé et vérifie cette archive avant de remplacer le workspace.

**Sur votre poste, depuis le dépôt téléchargé :** quittez Claude avec `/exit`,
puis le shell du lab avec `exit`. Si le conteneur n’a pas été lancé avec `--rm`,
retirez vous-même ce conteneur arrêté ; le script refuse tout volume encore référencé.

```bash
docker pull ghcr.io/sebastien-ribiere/hands-on:lab
bash demo/reset-lab.sh
```

Relisez le nom du volume affiché, puis saisissez `reset golden-thread-workspace`
pour confirmer. Le script conserve le volume de connexion Claude, ne monte ni
le home ni le socket Docker dans ses conteneurs et ne lance pas Claude.
Il requiert uniquement Bash et Docker sur le poste (Linux ou macOS).
Ce script local est une option pour les répétitions ; il n’est pas un prérequis
participant. Vous pouvez aussi conserver l’ancien workspace et choisir un
nouveau nom de volume dans les commandes de lancement et de replay.

Pour un volume de répétition ou une image figée :

```bash
bash demo/reset-lab.sh --workspace golden-thread-workspace-repetition --image ghcr.io/sebastien-ribiere/hands-on:lab
```

L’image doit déjà être disponible localement ; le script affiche son SHA et
utilise cette version durant le reset. Les noms de workspace acceptés commencent
par `golden-thread-workspace`. Aucun volume n’est supprimé automatiquement après
un échec de sauvegarde. Si la restauration initiale échoue après la suppression
du workspace, l’archive reste disponible.

Après succès, relancez la commande Docker de démarrage avec le même nom de
workspace et votre volume Claude habituel. Lancez **`claude` pour une nouvelle
conversation**, sans `--continue` : l’historique Claude a été conservé et pourrait
encore décrire la répétition précédente.

### Récupérer une sauvegarde de reset

Le script affiche un nom tel que `golden-thread-workspace-backup-…`. Ce volume
contient `workspace.tar`. Pour récupérer le travail dans un **nouveau** volume,
remplacez la valeur de `backup_volume` par le nom affiché et choisissez un nom
inutilisé pour `restore_volume` :

```bash
backup_volume='golden-thread-workspace-backup-REMPLACER'
restore_volume='golden-thread-workspace-restaure'
# Ces vérifications évitent de créer une fausse sauvegarde ou d’écraser un volume.
docker volume inspect "$backup_volume" >/dev/null && \
  ! docker volume inspect "$restore_volume" >/dev/null 2>&1 && \
  docker volume create "$restore_volume" && \
  docker run --rm --network none --user 0 --workdir / --entrypoint bash \
    --mount "type=volume,source=$backup_volume,target=/backup,readonly,volume-nocopy" \
    --mount "type=volume,source=$restore_volume,target=/restore,volume-nocopy" \
    ghcr.io/sebastien-ribiere/hands-on:lab \
    -c 'tar -xpf /backup/workspace.tar -C /restore'
```

Relancez le lab en utilisant ce volume restauré pour `/workspace`.
Les sauvegardes occupent de l’espace Docker et restent jusqu’à leur suppression
manuelle, après vérification que vous n’en avez plus besoin.

## Rejouer le job GitLab sans donner accès au Docker du poste au lab

Le conteneur du lab **ne monte pas** `/var/run/docker.sock` et n'est pas lancé
en mode privilégié. Pour la dernière étape, un second conteneur prend une copie
en lecture seule du workspace et exécute les lignes assemblées depuis le vrai
`.gitlab-ci.yml` dans l'image déclarée par la pipeline :

```bash
docker run --rm -it \
  -v golden-thread-workspace:/source:ro \
  -w /builds/hands-on \
  python:3.12-slim \
  bash -lc 'cp -a /source/. . && \
    rm -rf .demo && \
    python3 -m pip install --quiet PyYAML==6.0.2 && \
    python3 demo/gitlab_job.py .gitlab-ci.yml golden-thread --script > /tmp/ci-job.sh && \
    bash -e /tmp/ci-job.sh'
```

Cette commande s'exécute elle-même dans Docker : aucun `.sh` du dépôt n'est
lancé directement sur le poste. `demo/publish-source.sh`, utilisé par le vrai
job GitLab de démonstration, s'exécute à l'intérieur de ce conteneur éphémère.

## Modèle de confiance

Le lab est volontairement plus restrictif qu'un montage de repository classique :

- pas de `--privileged` ;
- pas de socket Docker de l'hôte ;
- pas de montage de `~/.ssh`, de credentials cloud ou du home utilisateur ;
- seulement deux volumes Docker nommés et dédiés au lab ;
- Dockerfile public et reproductible ;
- Claude Code installé depuis le dépôt `apt` signé d'Anthropic, avec contrôle du
  fingerprint de la clé pendant le build.

Pour une répétition ou une conférence, utiliser de préférence un tag d'image
immuable (`lab-<sha>`) plutôt que le tag mobile `lab`.

## Lisibilité en salle

Le shell du lab affiche un prompt sans couleur et désactive la coloration de
`ls` pour éviter les répertoires bleu sombre sur fond noir. Cela ne change pas
le thème de votre terminal ni celui de Claude Code.

Dans Claude, utilisez `/theme` et choisissez un thème adapté au fond de votre
terminal, éventuellement une variante accessible ([référence Claude Code](https://code.claude.com/docs/en/interactive-mode#theme-and-display)). Agrandissez le texte pour
la projection. Les verdicts Golden Thread sont des libellés explicites
(`PASS`, `FAIL`, `STALE`, `NOT READY`) : leur lecture ne dépend pas d’une couleur.

Après mise à jour de l’image, un volume existant conserve son ancien workspace.
Pour essayer la nouvelle version sans perdre votre travail, lancez-la avec un
nouveau nom de volume workspace ; vous pouvez garder le volume Claude.

## Langue des retours Golden Thread

L’image du lab et le job CI activent `GOLDEN_THREAD_LANG=fr`. Les messages du
parcours, les intitulés des exigences connues, la grille affichée et le résumé
CI sont présentés en français. Les statuts (`PASS`, `FAIL`, `NOT READY`…), les
commandes et les phrases de confirmation restent identiques.

Les preuves et les rapports `--json` conservent leurs données originales,
y compris les textes de la policy. Les diagnostics bruts de Bandit et des tests
restent ceux de leurs outils ; B307 est accompagné d’une explication française.
Un texte de policy inconnu du catalogue de traduction est affiché tel quel.
La langue ne modifie ni les règles, ni leurs digests, ni les verdicts.

Hors du conteneur, avec cette version de la CLI :

```bash
GOLDEN_THREAD_LANG=fr golden-thread verify
```

`GOLDEN_THREAD_LANG=en` retrouve l’affichage anglais de la CLI.

**Après une mise à jour de l’image :** un volume workspace déjà utilisé garde
l’ancienne copie du dépôt, dont `.gitlab-ci.yml` et la CLI utilisée par le replay.
Un simple `docker pull` ne met pas ce volume à jour. Conservez-le pour votre
travail ; pour une nouvelle répétition, choisissez un nouveau nom de volume
workspace et utilisez ce même nom dans le lancement et dans le replay.
