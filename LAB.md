# Golden Thread — démarrer le lab

Une fois connecté, poursuivez avec le [guide participant](GUIDE-PARTICIPANT.md) :
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

Le conteneur est jetable, mais le workspace est volontairement persistant. Pour
rejouer le hands-on depuis l'état initial :

```bash
docker volume rm golden-thread-workspace
```

La connexion Claude peut rester dans son volume séparé.

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
