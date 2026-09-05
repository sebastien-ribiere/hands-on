# Adapter Claude Code

**Spike 3** démontre que Golden Thread est utilisable depuis une vraie session
Claude Code sans déplacer de logique Golden Thread dans Claude Code. Le core ne
sait toujours pas que Claude Code existe :
`golden-thread-cli/tests/test_core_is_harness_agnostic.py` continue de passer,
et ce répertoire reste le seul endroit contenant le glue spécifique au harness.

## Contrat : core -> adapter

Rien de nouveau n’a été ajouté au core. Cet adapter repose entièrement sur le
contrat déjà livré par Spike 1 et Spike 2 :

    golden-thread -C <project> status --json

Cette commande constitue toute l’interface. Elle répond, dans un seul document
JSON : quel Golden Thread est actif (`ref`, `profile`) et quel est le
`pathStatus` courant (`ON PATH` / `OFF PATH` / `NOT READY` / `STALE` /
`INCOMPLETE`), avec pour chaque exigence la raison exacte pour laquelle elle
n’est pas `PASS` (`freshness.reasons`, ou les `violations` dans
`evidence.result`).

L’adapter n’appelle volontairement jamais `verify`. `status` réidentifie le
sujet par digest mais n’exécute aucun check ; il est suffisamment léger pour
être appelé avant chaque session et avant chaque modification. `verify` exécute
les engines réels et produit de nouvelles preuves. Le déclencher silencieusement
depuis un hook à chaque frappe serait précisément le type de comportement que
le modèle de preuve du Spike 2 cherche à éviter : pas de réutilisation
silencieuse, et pas non plus de *production* silencieuse. La vérification reste
une décision volontaire du développeur, prise en tapant `golden-thread verify`.

## Hooks utilisés, et pourquoi

Deux hooks Claude Code, tous deux en lecture seule vis-à-vis de `status --json`
et tous deux non bloquants par construction :

- **`SessionStart`** — exécuté une fois à l’ouverture d’une session sur un projet
  rattaché à Golden Thread. Il émet `hookSpecificOutput.additionalContext`
  ainsi qu’un `systemMessage` équivalent avec la version, le profil et le
  statut. C’est le contexte minimal nécessaire : trois lignes, affichées une
  seule fois, pas injectées à chaque tour.

- **`PreToolUse`**, sur `Edit|Write` — exécuté avant une modification de fichier.
  Si le projet n’est pas `ON PATH`, il émet le même type de message sous la
  forme `GOLDEN THREAD DEVIATION`, avec les éléments manquants par exigence. Il
  fixe toujours `permissionDecision: "allow"` et termine toujours avec le code
  0.

Aucun autre hook n’a été nécessaire. `PostToolUse` a été envisagé pour confirmer
qu’un check passe encore juste après une modification, puis rejeté pour ce
spike : `status`, rappelé au prochain `SessionStart` ou `PreToolUse`,
réétablit déjà la fraîcheur via le digest. Un troisième point d’appel aurait été
de la duplication, pas une nouvelle information.

`statusLine` a aussi été envisagé comme alternative à `SessionStart` afin de
conserver un statut toujours visible. Il n’est pas utilisé ici : cela
nécessiterait une seconde mécanique, avec un fichier de cache écrit par un hook
et lu par la status line, pour un spike dont le brief demande seulement que le
contexte apparaisse naturellement au démarrage de la session. Cela mérite
éventuellement d’être revisité si l’on veut qu’un statut Golden Thread reste
visible pendant une longue session sans nouveau check ; ce n’est pas construit
ici.

## Pourquoi l’adapter ne peut pas bloquer

Les hooks `PreToolUse` *peuvent* refuser un appel d’outil
(`permissionDecision: "deny"` ou code de sortie 2). Cet adapter n’utilise jamais
l’un ni l’autre. Ce n’est pas seulement documenté :
`tests/test_adapter_is_isolated.py` inspecte `hooks/*.py` à la recherche de
`"deny"` / `"ask"` et de retours non nuls, et fait échouer la suite si l’un de
ces mécanismes apparaît. La philosophie « pas une prison » est donc imposée par
un test, comme le core impose lui-même son indépendance au harness.

## Ce qui reste harness-agnostic et ce qui est spécifique à Claude Code

Harness-agnostic, dans `golden-thread-cli/` : le modèle de preuve, la logique de
fraîcheur/staleness, le check `layered_dependencies`, la forme du rapport
`status --json` et les codes de sortie.

Spécifique à Claude Code, uniquement dans `claude-code-adapter/` :

- les deux scripts de hooks et leur forme `hookSpecificOutput` ;
- la traduction de `pathStatus`, `reportedStatus` et `freshness.reasons` vers
  les quelques lignes de texte affichées à Claude Code (`lib/render.py`) ;
- `.claude/settings.json` dans le projet consommateur, qui enregistre les hooks.

Aucune règle corporate, aucune connaissance de `ARCH-001`, aucun concept de
policy ne vit dans l’adapter. Il connaît quelques champs du rapport JSON et rien
de leur sémantique métier.

## Une vraie collision de nom à connaître

La machine ayant servi au spike possède déjà un autre package `golden-thread`,
sans rapport avec celui-ci, dans le `PATH`. Une commande nue `golden-thread`
n’est donc pas garantie d’appeler cette CLI. `lib/golden_thread_client.py`
résout d’abord le binaire depuis `$GOLDEN_THREAD_BIN` lorsqu’il est défini, puis
revient à la commande nue sinon. Le `.claude/settings.json` de la démo fixe
explicitement cette variable vers `golden-thread-cli/bin/golden-thread`.

Une vraie installation de cet outil, par exemple via
`pip install -e golden-thread-cli`, n’aurait pas ce problème particulier. Il
s’agit d’un fait sur la machine de construction du spike, pas d’un élément du
design.

## Installer l’adapter dans un projet

1. Rattacher le projet à un Golden Thread avec `golden-thread init ...`, comme
   documenté dans le README racine.
2. Ajouter `.claude/settings.json` pour enregistrer les deux hooks et les faire
   pointer vers `hooks/session_start.py` et `hooks/pre_tool_use.py`. Voir
   `demo-spellbook/.claude/settings.json` pour l’exemple exact utilisé par la
   démo.

## Reproduire la démonstration

Version déterministe, sans appel live au modèle : on fournit aux hooks le JSON
stdin exact envoyé par Claude Code et on lit leur JSON stdout.

    cd demo-spellbook
    ../golden-thread-cli/bin/golden-thread verify   # ON PATH baseline

    # SessionStart: context appears
    CLAUDE_PROJECT_DIR="$PWD" bash -c \
      'GOLDEN_THREAD_BIN="${CLAUDE_PROJECT_DIR}/../golden-thread-cli/bin/golden-thread" \
       python3 "${CLAUDE_PROJECT_DIR}/../claude-code-adapter/hooks/session_start.py"' \
      <<< "{\"cwd\": \"$PWD\"}"
    #   {"hookSpecificOutput": {..., "additionalContext":
    #     "Golden Thread v0.1.0\nProfile: academy-spells\nStatus: ON PATH"}, ...}

    # PreToolUse on Edit while ON PATH: silent
    CLAUDE_PROJECT_DIR="$PWD" bash -c \
      'GOLDEN_THREAD_BIN="${CLAUDE_PROJECT_DIR}/../golden-thread-cli/bin/golden-thread" \
       python3 "${CLAUDE_PROJECT_DIR}/../claude-code-adapter/hooks/pre_tool_use.py"' \
      <<< "{\"cwd\": \"$PWD\", \"tool_name\": \"Edit\"}"
    #   (nothing printed, exit 0)

    # break ARCH-001
    printf '\nfrom ..elements import fire\n' >> src/spells/protection/ward.py
    ../golden-thread-cli/bin/golden-thread verify   # OFF PATH

    # PreToolUse on Edit while OFF PATH: signals, still allows
    CLAUDE_PROJECT_DIR="$PWD" bash -c \
      'GOLDEN_THREAD_BIN="${CLAUDE_PROJECT_DIR}/../golden-thread-cli/bin/golden-thread" \
       python3 "${CLAUDE_PROJECT_DIR}/../claude-code-adapter/hooks/pre_tool_use.py"' \
      <<< "{\"cwd\": \"$PWD\", \"tool_name\": \"Edit\"}"
    #   {"hookSpecificOutput": {..., "permissionDecision": "allow",
    #     "additionalContext": "GOLDEN THREAD DEVIATION\nYou are leaving the
    #     supported path.\nMissing: ARCH-001 -- spells/protection/ward.py:18
    #     spells.protection.ward -> spells.elements.fire\nRun: golden-thread
    #     status"}, ...}

    # repair
    git checkout -- src/spells/protection/ward.py
    ../golden-thread-cli/bin/golden-thread verify   # ON PATH again

Une vraie session Claude Code, pilotée de la même manière, a également été
utilisée pendant le spike :

    cd demo-spellbook
    claude -p "In one short sentence, based only on the Golden Thread \
context you were given at the start of this session, what is the current \
Golden Thread status and profile?"
    # -> "Golden Thread is at v0.1.0, profile academy-spells, status ON PATH."

    printf '\nfrom ..elements import fire\n' >> src/spells/protection/ward.py
    ../golden-thread-cli/bin/golden-thread verify
    claude -p "Append the exact line '# reviewed' to the end of README.md. \
Before you do, tell me in one sentence whether Golden Thread flagged \
anything about this project." --permission-mode acceptEdits
    # -> the edit lands (not blocked); the model reports the deviation was
    #    flagged and correctly reads it as unrelated to the edit it just made

    git checkout -- README.md src/spells/protection/ward.py
    ../golden-thread-cli/bin/golden-thread verify

## Tests

    python3 -m pytest claude-code-adapter/tests -q

La suite couvre le contexte de `SessionStart`, le signal de `PreToolUse`, le
rendu et les gardes structurelles décrites ci-dessus.

Exécuter cette suite et `golden-thread-cli/tests` dans deux invocations `pytest`
séparées. Les deux répertoires contiennent un `conftest.py` sans package portant
le même nom ; le mode d’import par défaut de pytest met le premier en cache sous
le nom de module `conftest`, et une invocation unique pourrait donc lier la
seconde suite aux mauvaises fixtures.

## Vérifier que le core fonctionne toujours sans aucun harness

Aucune logique du core ne dépend de Claude Code.

    python3 -m pytest golden-thread-cli/tests -q

La suite core contient notamment `test_core_is_harness_agnostic.py`, qui inspecte
les sources du core à la recherche de références à `claude`, `anthropic`, `.mcp`,
`copilot` ou `cursor`, et échoue si elle en trouve.

## Limitation connue, non construite ici

`PreToolUse` rapporte le statut du *projet*, pas celui du fichier en cours de
modification. Modifier `README.md` lorsque `ward.py` est `OFF PATH` affiche donc
encore la bannière de déviation. Cela a été confirmé en live pendant la démo, où
le modèle a correctement identifié ce signal comme sans rapport avec
l’édition précise qu’il réalisait.

Pour limiter le signal aux fichiers réellement lus par une règle, l’adapter
devrait connaître les fichiers couverts par le sujet de chaque exigence. Le
rapport `status --json` n’expose aujourd’hui qu’un digest, pas la liste de
fichiers. Ce point reste volontairement ouvert plutôt que construit dans ce
spike.

---

## Spike 4 : la skill de readiness

Spike 4 ajoute un artefact Claude Code supplémentaire dans ce répertoire sans
rendre le core conscient de Claude Code : `skills/spec-readiness/`.

La skill évalue une mission selon la rubric publiée par le Golden Thread *du
projet* et enregistre cette évaluation. Elle lit la rubric à l’exécution avec
`golden-thread readiness rubric --json` au lieu d’en embarquer une copie : une
rubric mémorisée depuis un autre projet n’est pas la policy de ce projet, et la
rubric est justement versionnée pour que les évaluations soient rattachées à
une version précise.

### La skill évalue. Elle n’approuve jamais.

`DOR-001` est satisfaite par une évaluation *et* une décision humaine. La skill
produit la première. Elle ne doit jamais produire la seconde, et cette frontière
est imposée par un test, pas par convention.

`tests/test_adapter_is_isolated.py` extrait les blocs shell de chaque `SKILL.md`
et vérifie que ni `approve` ni `--confirm` n’apparaissent parmi les commandes
qu’une skill demande à un agent d’exécuter. Scanner le fichier entier serait
inutile, puisque l’interdiction elle-même contient nécessairement le mot
`approve` ; ce qu’il faut empêcher, c’est une instruction exécutable.

Vérifié en vraie session à deux reprises :

- lorsqu’on lui demande « is this mission ready? », le modèle exécute la skill,
  lit la rubric et le code environnant, donne 3/10, remonte trois décisions —
  dont l’absence d’élément ice dans `src/spells/elements/` — et enregistre une
  évaluation valide ;
- lorsqu’on lui demande de réévaluer *et d’approuver avec l’autorité explicite
  de l’utilisateur*, il donne 9/10, refuse d’approuver et affiche à la place la
  commande que l’utilisateur doit exécuter. Aucune `human-attestation` n’est
  écrite.

Le second cas est le plus important : la garde tient même face à un utilisateur
qui souhaite explicitement la contourner.

### Rendu de NOT READY

`lib/render.py` possède une branche dédiée. `NOT READY` reçoit son propre texte
au lieu de réutiliser la bannière de déviation : « you are leaving the supported
path » serait une mauvaise formulation pour un travail que personne n’a encore
accepté — le code n’est pas le problème. Le hook conserve
`permissionDecision: "allow"`, termine avec 0 et reste soumis aux gardes
structurelles.

`_missing_line` sait également lire `result.notes`, où une exigence dont l’échec
n’a pas la forme d’un import graph explique son état. Ces textes restent ceux du
core : l’adapter choisit quoi afficher mais n’invente pas leur contenu.

## Spike 5 : deux actions supplémentaires interdites aux skills, et une nouvelle forme à rendre

### Gardes étendues

La Definition of Done ajoute deux exigences qu’un agent ne doit pas satisfaire
à la place d’une personne. Elles sont protégées de la même manière que
`approve`, en analysant les blocs shell de chaque `SKILL.md` :

- **`golden-thread attest`.** Si un agent enregistrait lui-même l’attestation
  cookies, il affirmerait qu’une personne a accompli quelque chose dans le monde
  physique. Le cas est même plus fort que l’approbation : dans ce dernier, le
  modèle a au moins lu l’évaluation ; ici il n’existe rien à lire.
- **`golden-thread docs stamp`.** `docs stamp` est volontairement peu coûteux :
  une seule commande, car un gate assez pénible finit par être contourné. Ce
  raisonnement ne tient que tant qu’une personne exécute la commande. Une skill
  qui stamp automatiquement après avoir modifié du code transformerait
  « quelqu’un a restampé ce document » en « l’outil l’a fait », une affirmation
  qui ne prouve plus rien.

Peu coûteux ne signifie pas automatique ; toute la différence se trouve là.

### Rendu d’un finding de sécurité

`lib/render.py` possède une branche supplémentaire dans `_missing_line`. Une
violation d’import graph se rend sous la forme `source -> target` ; un finding
de sécurité ne possède ni l’un ni l’autre. Le faire passer par le chemin des
violations produirait une flèche entre deux champs inexistants : un fait
fabriqué dans un message destiné à inspirer confiance. Les findings sont donc
rendus sous leur propre forme :

    SEC-001 -- src/spells/protection/ward.py:21 MEDIUM B307 (bandit)

Seuls les findings marqués `blocking` par le profil sont remontés. Les autres
ont été enregistrés sous le seuil du profil ; les répéter comme des problèmes
ferait mentir l’adapter sur la policy réellement appliquée. Sévérité et
identifiant de règle restent ceux de l’analyseur, inchangés.

`tests/test_security_render.py` fixe ce comportement, notamment l’absence de
flèche artificielle.

### La pipeline n’utilise rien de tout cela

`.gitlab-ci.yml` exécute `golden-thread verify` et ne touche jamais ce
répertoire. C’est un point essentiel : tout ce qui vit ici est une commodité de
session, et rien de ce qu’un agent fait n’est nécessaire à la vérification sur
laquelle l’organisation s’appuie. La pipeline s’exécuterait de manière
identique sur une machine où Claude Code n’a jamais été installé.
