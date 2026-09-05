# Golden Thread

Un golden path qu’une organisation peut distribuer, versionner et vérifier.

**Spike 1** a validé la vertical slice : un projet se rattache à une version
explicite de Golden Thread, sait sur quelle version et quel profil il se trouve,
exécute une vraie règle d’architecture et passe **OFF PATH** lorsqu’il la viole.

**Spike 2** rend chaque verdict traçable. Il n’existe aucun `architecture: true`
nulle part. Un statut n’est rapporté qu’avec les *preuves* dont il provient — et
une preuve qui ne décrit plus le travail ou l’exigence courante est marquée
**STALE** au lieu d’être silencieusement réutilisée.

**Spike 3** ajoute un adapter Claude Code minimal, démontrant que le core est
utilisable depuis une vraie session Claude Code sans déplacer de logique Golden
Thread dans Claude Code. Voir [`claude-code-adapter/README.md`](claude-code-adapter/README.md).

**Spike 4** ajoute une **Definition of Ready** — la première exigence que Golden
Thread ne peut pas vérifier seul. `DOR-001` est satisfaite par deux affirmations
produites ailleurs : une évaluation effectuée selon une rubric versionnée, et une
décision prise par une personne. Aucune des deux ne suffit seule, et la CLI ne
produit ni l’une ni l’autre.

**Spike 5** complète le fil : une **Definition of Done** avec cinq exigences et
cinq formes de preuves réellement différentes, un **vrai analyseur de sécurité**,
et une **pipeline GitLab qui rejoue toute la vérification sans aucun agent**.

Le core reste en Python stdlib uniquement, sans dépendance envers un harness IA.
L’évaluation arrive de l’extérieur ; la rubric est une donnée de la policy
corporate ; l’analyseur est un sous-processus nommé par cette policy.

## La règle testée

    ARCH-001
    Protection spells may depend on the Air and Water elements.
    They may not depend on Fire.

Il s’agit d’une vraie règle de dépendances, pas d’une recherche de chaîne. Elle
est vérifiée sur le graphe d’import réel du projet, construit avec le module
Python `ast`, imports relatifs compris. `demo-spellbook/src/spells/offense/flame_lance.py`
dépend de Fire et reste conforme, car la règle est limitée à la couche de
protection.

## La Definition of Ready

    DOR-001
    A mission is Ready before implementation starts.

Elle n’est satisfaite que lorsque **ces deux conditions** sont remplies :

    an assessment scoring >= 8/10 against spec-readiness@1.0.0, with no blockers
      +
    a human attestation recording a person's decision

### Le score est une évaluation, pas une mesure

Deux évaluateurs lisant la même mission avec la même rubric peuvent être en
désaccord. Ce n’est pas une réserve ajoutée par l’outil : c’est écrit dans la
rubric elle-même, dans `caveat`, et affiché textuellement par
`golden-thread readiness rubric`.

Cela a aussi été observé, pas simplement supposé. Sur la mission de la démo,
avec `spec-readiness@1.0.0`, l’évaluation reproductible de
`demo/assessment-initial.json` donne **7/10**, alors qu’une session live d’un
modèle a donné **3/10** sur le même document, en soulevant une décision que ni
la mission ni l’évaluation préparée n’avaient détectée : il n’existe pas
d’élément ice dans `src/spells/elements/`. Même rubric, même texte, lecteurs
différents, scores différents. C’est le cas normal.

Un score n’est donc jamais traité comme un fait. Il est enregistré comme
l’opinion d’un acteur nommé, avec la version de rubric utilisée, et rend la
mission *éligible à une décision humaine* — rien de plus.

### Aucune moitié ne peut remplacer l’autre

- **Aucun score ne satisfait DOR-001 à lui seul**, même 10/10. Avec
  `requires_human_approval = true`, l’engine n’a aucun chemin qui valide une
  évaluation seule.
- **Une approbation ne déplace pas le seuil.** `min_score` appartient à la
  policy corporate. Une personne qui approuve un 7/10 enregistre son
  approbation, mais l’exigence continue de signaler 7 comme inférieur à 8.
- **Un blocker l’emporte sur n’importe quel score.** `max_blockers = 0`
  signifie qu’un seul blocker ouvert rend la mission non prête, même à 10/10.

### La rubric est versionnée deux fois

Par son nom de fichier — `rubrics/spec-readiness-1.0.0.toml` — afin qu’une
nouvelle version soit un nouveau fichier et une modification d’une ligne dans
la règle, tous deux visibles dans un diff. Et par le champ `version` à
l’intérieur du fichier, que chaque évaluation enregistre sous la forme
`spec-readiness@1.0.0`. Si un profil référence ensuite `1.1.0`, une ancienne
évaluation n’est pas silencieusement réinterprétée selon la nouvelle rubric :
elle cesse de s’appliquer et indique la version sous laquelle elle a été faite.

### Les deux affirmations sont liées au texte qu’elles concernent

Une évaluation et une approbation enregistrent chacune le digest du sujet du
document de mission. Modifiez la mission après approbation et aucune des deux
affirmations ne subsiste : une approbation est donnée à un texte, pas à un nom
de fichier. C’est exactement le mécanisme construit au Spike 2 pour le code,
appliqué tel quel à un fichier Markdown.

### La frontière d’approbation, formulée honnêtement

`golden-thread readiness approve` affiche l’évaluation, nomme l’attestateur et
demande une phrase de confirmation dérivée du digest du sujet. Sans terminal,
la commande refuse de supposer quoi que ce soit et renvoie l’appelant vers
`--confirm`.

**Cela rend l’approbation délibérée. Cela ne prouve pas qu’un humain l’a
réalisée**, et rien sur une machine de développeur ne le peut. Le mécanisme
apporte attribution et intention : une approbation ne peut pas être enregistrée
par accident, sans nommer qui approuve, ni rejouée sur un texte différent.

La frontière côté agent est imposée séparément et structurellement : la skill
`spec-readiness` n’exécute jamais d’approbation, et
`claude-code-adapter/tests/test_adapter_is_isolated.py` analyse les blocs shell
de chaque `SKILL.md` et échoue si `approve` apparaît dans les commandes qu’une
skill demande à un agent d’exécuter. Vérifié en live : lorsqu’on lui a demandé
d’approuver avec l’autorité explicite de l’utilisateur, la session a réévalué à
9/10 puis refusé d’approuver, et aucune `human-attestation` n’a été écrite.

## La Definition of Done

Cinq exigences, avec cinq types de preuves volontairement différents. Le point
important n’est pas qu’il y en ait cinq : une Definition of Done contient des
éléments qu’une machine peut trancher, d’autres qu’elle peut seulement rapporter,
et au moins un qu’elle ne pourra jamais vérifier ; les trois conservent le même
statut dans le contrat.

| Exigence | Fournisseur de preuve | Ce que cela établit réellement |
|---|---|---|
| `TEST-001` | une commande déterministe | un argv nommé a été exécuté sur des fichiers nommés et a terminé avec le code zéro |
| `ARCH-001` | le vrai graphe d’import | aucun module de protection n’importe Fire |
| `SEC-001` | **bandit**, un vrai analyseur | cet analyseur n’a rien détecté qu’il classe MEDIUM ou plus |
| `DOC-001` | un stamp de digest dans le document | quelqu’un a de nouveau stampé le document par rapport à ce code exact |
| `COOKIE-001` | la parole d’une personne | quelqu’un l’a affirmé, avec son identité déclarée |

Il n’existe pas d’objet « Definition of Done » séparé dans le modèle, et il
n’en faut pas : le profil `academy-spells-done` est le contrat, lu à deux
moments. `DOR-001` rapporte `NOT READY` lorsque le travail n’a jamais été
accepté ; les cinq autres rapportent `OFF PATH` lorsqu’un élément du travail
n’est pas terminé.

### Tests : un code de sortie, et rien de plus

`TEST-001` utilise l’engine `external_command`. La policy corporate déclare une
**liste argv**, jamais une chaîne : aucun shell n’intervient, donc rien ne peut
être quoté, expansé ou découpé autrement, et le code de sortie constitue le
verdict.

    command = ["python3", "-m", "pytest", "-q", "tests"]

L’argv est enregistré dans `method` de la preuve, car `external_command` ne
décrit pas à lui seul une méthode : exécuter la suite de tests et exécuter autre
chose utilisent le même engine mais constituent des méthodes différentes.

La portée de l’affirmation est volontairement étroite, et la règle le précise
dans sa rationale : une commande nommée a été exécutée contre des fichiers
nommés et a terminé avec le code zéro. **Une suite vide renvoie elle aussi zéro.**
Exiger des tests pertinents serait une autre exigence, qui demanderait un autre
engine plutôt qu’une interprétation plus ambitieuse de celui-ci.

Une commande impossible à lancer — binaire manquant, timeout — produit `ERROR`,
jamais `FAIL` ni `PASS`. Une commande qui renvoie zéro sur un sujet ne contenant
aucun fichier produit également `ERROR` : un PASS sur rien est exactement le
type de faux signal que ce projet cherche à éliminer.

### Sécurité : un vrai analyseur, avec le seuil de la policy par-dessus

`SEC-001` exécute **bandit**, fixé en version 1.9.4. Golden Thread ne le
réimplémente pas, ne reformule pas ses findings et ne les adoucit pas :

    src/spells/protection/ward.py:21
      MEDIUM B307 (bandit): Use of possibly insecure function - consider using safer ast.literal_eval.
      https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_calls.html#b307-eval

L’identifiant de règle, la sévérité, le texte et la référence proviennent de
l’analyseur et sont recopiés sans modification. Un seul champ appartient à
Golden Thread : `blocking`. Il ne donne pas un avis sur le finding ; il indique
si le seuil de *ce profil* transforme ce finding en échec :

    fail_on_severity = "MEDIUM"
    min_confidence   = "MEDIUM"

Les deux valeurs vivent dans la policy corporate. « MEDIUM et au-dessus échoue
ici » est donc une décision organisationnelle versionnée. **Les findings sous
le seuil sont tout de même enregistrés**, avec `blocking: false`, accompagnés
d’une note précisant combien ont été écartés et selon quel seuil. Filtrer les
résultats d’un scanner avant que quiconque puisse les voir est une bonne manière
de transformer une exigence de sécurité en décoration.

Le code de sortie n’est volontairement *pas* le verdict ici : un scanner qui a
trouvé quelque chose et un scanner qui a crashé peuvent tous deux retourner un
code non nul. Tout état autre que « s’est exécuté proprement » ou « s’est
exécuté et a trouvé des éléments » produit `ERROR`, tout comme un rapport
illisible ou un rapport listant des fichiers que l’analyseur n’a pas réussi à
parser. Un `PASS` sur du code que personne n’a pu analyser est une affirmation
sur du code non examiné.

`security_scan` sait actuellement lire un seul format de rapport
(`format = "bandit"`). Un format inconnu produit un `ERROR` qui nomme ce qui est
supporté. C’est une branche de code, pas un système de plugins.

### Documentation : le mécanisme, choisi explicitement

« La documentation est à jour » est facile à ajouter dans une Definition of
Done et difficile à définir. Trois interprétations ont été étudiées :

- **le document existe / chaque fonction possède une docstring.** Vérifiable,
  mais cela mesure la présence, pas l’actualité. Une docstring écrite il y a
  deux ans reste toujours verte.
- **la documentation a changé dans le même commit que le code.** Cela fait de
  Git le mécanisme, alors que ce projet refuse ce raccourci depuis Spike 2 : un
  worktree avec des modifications non commitées n’est pas identifié par son
  HEAD.
- **le document déclare quel code il décrit, et cette déclaration est
  vérifiée.** C’est la solution retenue.

`docs/ARCHITECTURE.md` contient une ligne :

    <!-- golden-thread: describes src/ sha256:cdd324e7312c… -->

L’engine recalcule le digest de `src/**/*.py` et compare. En cas d’écart, il
affiche les deux digests :

    FAIL   DOC-001  The documentation describes the code that ships
           - docs/ARCHITECTURE.md describes src/ at cdd324e7312c
           - src/ is now at 17f84e2b32c7
           - the code moved and the documentation did not say so

C’est le mécanisme du Spike 2 appliqué vers l’extérieur. Le sujet couvre à la
fois **le document et le code** ; une modification de l’un ou de l’autre rend le
verdict enregistré stale.

**Ce que cela prouve, précisément :** quelqu’un a restampé le document par
rapport à ce code exact. Pas que la personne l’a lu, ni que la prose est juste.
`golden-thread docs stamp` prend une seconde et est volontairement peu coûteux :
un gate suffisamment pénible finit par être contourné. L’exigence élimine le
cas *silencieux*, où du code part alors que personne n’a même affirmé avoir
regardé la documentation depuis. La CLI le dit explicitement à chaque stamp, et
l’engine le répète dans les notes d’un `PASS`.

### Cookies : l’exigence que rien ne peut vérifier

`COOKIE-001` exige que des cookies aient été préparés et partagés avec l’équipe.
C’est volontairement une règle maison inattendue, et elle remplit un vrai rôle.

Toutes les organisations ont dans leur Definition of Done au moins un élément
qu’aucun scanner, aucune suite de tests et aucun modèle ne peut établir : la
démo a été présentée aux bonnes personnes, l’astreinte a été informée avant le
déploiement, le client a été prévenu de la fenêtre de migration. Ces éléments
sont invérifiables exactement comme les cookies. Un langage de policy capable
de représenter uniquement ce qui est calculable les sortirait silencieusement
de la Definition of Done, simplement parce qu’il n’aurait aucun endroit où les
exprimer.

L’exigence reste donc dans le profil avec le même statut que la règle
d’architecture et est satisfaite par `golden-thread attest COOKIE-001` :

    COOKIE-001  Cookies were prepared and shared with the team
    Claim         Cookies have been prepared and shared with the team for this delivery.
    Subject       10 file(s) sha256:cdd324e7312c
    Attestor      seb@academy.invalid

    This records that YOU attested this, on your own account.
    Nothing here checked it. Nothing here can: that is why this
    requirement is satisfied by a name rather than by a verdict.

    Type the phrase to confirm: attest cdd324e7312c

Même discipline de confirmation que pour l’approbation du Spike 4, en partageant
le même chemin de code afin qu’aucune des deux opérations ne puisse devenir la
version laxiste. Même limite honnête également : le mécanisme rend l’affirmation
délibérée et la lie à cette version exacte du travail. **Il ne prouve pas qu’un
humain l’a formulée.** L’attestation expire lorsque `src/` change : nouveau
travail, nouveaux cookies.

Spike 4 avait choisi `readiness approve` plutôt qu’un `attest` générique, en
considérant qu’une occurrence ne constituait pas encore un pattern. Voici la
deuxième occurrence, et il s’agit d’un acte différent : `attest` existe donc
maintenant, tandis que `readiness` reste inchangé. Une Definition of Ready a
toujours besoin de sa rubric, de son score et de son évaluation ; rien de cela
n’appartient ici.

Deux gardes structurelles, dans le même esprit que celle du Spike 4 : aucun
`SKILL.md` ne peut exécuter `golden-thread attest`, et aucun ne peut exécuter
`golden-thread docs stamp`. Un test analyse les blocs shell de chaque skill pour
faire respecter ces deux règles.

## Preuves

Un enregistrement par exigence répond à six questions, et rien de plus :

| Champ | Question | Exemple |
|---|---|---|
| `requirement` | quelle exigence ? | `ARCH-001` |
| `subject` | vérifiée sur quoi ? | `src/`, 10 fichiers, `sha256:cdd324e7312c…` |
| `producer` | par quel producteur ? | `golden-thread 0.2.0` |
| `method` | avec quelle méthode ? | `layered_dependencies`, profil `academy-spells`, policy `v0.1.0 @ 651f644a18bf` |
| `result` | avec quel résultat ? | `PASS`, ou `FAIL` avec les violations exactes |
| `timestamp` | quand ? | `2026-08-28T07:53:51+00:00` |

Exigence et règle sont en relation un-à-un : une règle rend une exigence
vérifiable. Il n’existe ni score de confiance, ni signature, ni stockage central,
ni taxonomie de preuves.

Les enregistrements vivent dans `.golden-thread/evidence.json`, qui conserve le
**dernier** enregistrement par exigence. C’est un fichier d’état courant, pas un
journal d’audit, et il est jetable : `verify` le reconstruit.

### Où vit chaque artefact, et pourquoi

    golden-thread.json                  committed    which policy this project is on
    golden-thread-attestations.json     committed    what we were told, and by whom
    .golden-thread/source/              disposable   the policy cache
    .golden-thread/evidence.json        disposable   what the tool proved

La séparation repose sur **ce qui peut être reconstruit**. `verify` reproduit
les preuves et le manifest reproduit le cache. Une attestation est le seul
artefact de ce système que rien ne peut régénérer : si vous la supprimez, il
faut retourner demander à une personne.

Elle doit aussi *voyager*. Spike 4 conservait les attestations dans
`.golden-thread/`, et la pipeline GitLab a révélé le problème : un runner qui ne
voit pas l’approbation signale comme non accepté un travail pourtant accepté,
ce qui est vrai pour cette machine mais faux pour le projet. Le contraste est
apparu dans une seule exécution de pipeline : `DOC-001` passait parce que son
affirmation vit dans un fichier Markdown commité, tandis que `DOR-001` et
`COOKIE-001` échouaient parce que les leurs n’y figuraient pas.

Commiter une attestation la rend visible à la CI et pendant la review. Cela ne
la rend **pas authentifiée**, et rien ici ne prétend le contraire.

### Fraîcheur : le travail et l’exigence, indépendamment

La fraîcheur possède deux axes indépendants. Un enregistrement reste courant
uniquement tant que le sujet qu’il décrit et l’exigence à laquelle il répond
restent tous deux inchangés.

Le **digest du sujet** est un `sha256` calculé sur les paires triées
`(chemin relatif, sha256(contenu))` des fichiers exacts lus par l’engine de
vérification. `status` réidentifie ce sujet. Modifier, ajouter ou supprimer l’un
de ces fichiers rend la preuve STALE ; modifier un fichier sans rapport ne
l’invalide pas.

Le **requirement fingerprint** identifie la sémantique de l’exigence
individuelle : les données de sa règle ainsi que les artefacts de policy qu’elle
référence explicitement, par exemple une readiness rubric. Passer de `v0.2.0` à
`v0.3.0`, ou d’un profil à un autre, n’invalide pas une preuve simplement parce
que son conteneur a changé. Si `DOR-001` et sa rubric sont identiques, sa preuve
peut rester valable pendant que le nouveau profil ajoute `TEST-001`, `SEC-001`,
`DOC-001` et `COOKIE-001`.

La ref Git, la revision résolue et le profil restent enregistrés comme
provenance. Ils ne constituent pas l’identité d’une exigence. Pour les preuves
écrites avant l’existence de `requirementFingerprint`, Golden Thread conserve
le comportement conservateur historique : un changement de profil ou de
revision de policy rend cet ancien enregistrement STALE, car l’équivalence
sémantique ne peut plus être établie après coup.

Une revision Git enregistrée sur le sujet est uniquement descriptive. Un
worktree avec des modifications non commitées n’est pas identifié par son HEAD,
et un projet n’est pas nécessairement son propre dépôt.

## Statut du chemin

| Statut | Signification | Sortie |
|---|---|---|
| `INCOMPLETE` | rien n’a encore été vérifié | 0 |
| `ON PATH` | chaque exigence possède une preuve courante et passante | 0 |
| `OFF PATH` | une exigence a échoué sur une preuve encore applicable | 1 |
| `NOT READY` | une exigence de readiness n’est pas satisfaite | 4 |
| `STALE` | une preuve existe mais ne décrit plus le sujet ou l’exigence courante | 3 |

`NOT READY` l’emporte sur `OFF PATH`. Une exigence de readiness est une
précondition du travail lui-même ; annoncer « le code que vous avez écrit viole
une règle d’architecture » alors que la mission n’a jamais été acceptée répond
à la seconde question avant la première. Les deux exigences restent détaillées
individuellement : seul le statut global change.

Ensuite, la règle originale demeure : un échec confirmé l’emporte sur la
staleness ; l’inconnu l’emporte sur une hypothèse rassurante. `ON PATH` n’est
affirmé que lorsque chaque exigence est à la fois courante et passante.

`NOT READY` n’est pas non plus un gate. Une Definition of Ready bloquante serait
un autre outil : rien ici n’empêche un développeur d’écrire du code sur une
mission non acceptée. Golden Thread empêche simplement que cet état reste
*implicite*.

`OFF PATH` est un signal, pas un gate. `verify` renvoie un code non nul et le dit
explicitement, mais rien ici ne bloque un commit, un build ou un développeur.
Quitter le golden path reste possible ; Golden Thread garantit que la déviation
est explicite plutôt que silencieuse. `STALE` n’utilise volontairement *pas* le
code de sortie 1 : « une règle a échoué » et « nous ne savons pas » sont deux
faits différents, et les confondre serait exactement le type de mensonge que ce
spike cherche à éliminer.

## GitLab CI : la vérification rejouée par quelque chose qui ne pense pas

    .gitlab-ci.yml

Un seul job. Il installe la toolchain du projet, restaure la policy **pinnée** à
partir du manifest commité, exécute `golden-thread verify` et conserve le rapport
machine-readable comme artefact.

**Aucun agent n’intervient.** Pas de Claude Code, pas de modèle, aucun appel
réseau vers quoi que ce soit qui pense. Cette indépendance est le point central :
une preuve produite à l’intérieur de la session d’un agent est une preuve sur
cette session. La pipeline n’importe pas l’adapter, ne lit aucune skill et
s’exécuterait de manière identique sur une machine où Claude Code n’a jamais été
installé.

**Elle n’exécute jamais `init`.** `init` résout de nouveau une ref, et un tag peut
bouger. Le job lit le commit enregistré dans `golden-thread.json` et restaure
exactement celui-ci, en l’affichant pour que le log indique clairement à quelle
policy l’exécution est tenue.

**L’artefact est conservé avec `when: always`.** L’exécution qui échoue est
précisément celle dont quelqu’un voudra consulter le rapport.

### Calculer l’état et décider de bloquer sont deux choses différentes

La pipeline les garde visiblement séparées dans un même job :

    # 1. compute the state. Never fails the job on a verdict.
    - |
      set +e
      $GT -C "$GT_PROJECT" verify --json > golden-thread-report.json
      gt_exit=$?
      set -e

    # 3. this project's policy. THIS is the line that blocks a merge.
    - exit $gt_exit

Golden Thread calcule `OFF PATH`. Il ne demande pas une pipeline rouge. La ligne
`exit` le fait, et il s’agit d’une seule ligne modifiable avec un commentaire
qui le précise. Un projet qui pinne le même golden path peut choisir autre chose :
c’est ce que « pas une prison » signifie une fois arrivé dans la pipeline.

Un job en échec indique lequel des deux événements s’est produit :

    PIPELINE FAILED BY THIS PROJECT'S POLICY.
    Golden Thread computed a state and did not ask for this.
    The line in .gitlab-ci.yml that propagates its exit code did.
    A project pinning the same golden path may choose otherwise.

et, séparément, pour le code de sortie 2 :

    PIPELINE FAILED: golden-thread could not run at all.
    This is not a verdict about the code. Nothing was verified.

### Exécuter la pipeline sans GitLab

    ./demo/run-ci-locally.sh

Ce n’est pas une simulation. `demo/gitlab_job.py` lit `.gitlab-ci.yml`, récupère
`image`, `before_script` et `script` tels que GitLab les exécuterait, les assemble
dans un script shell unique comme le fait le runner — une variable définie sur
une ligne reste donc disponible à la suivante — puis les exécute **dans cette
image, sous Docker**. Cassez la pipeline, et ce script cassera avec elle. Une
démo qui réimplémenterait les étapes en bash continuerait au contraire de
fonctionner alors que la pipeline réelle serait en panne.

Le script prépare une copie propre du dépôt afin de ne rien modifier dans votre
worktree, et refuse complètement de s’exécuter sans Docker plutôt que de
substituer un environnement qui lui ressemble seulement.

Une différence de fidélité reste explicitée parce qu’elle compte pour ce que
cette démonstration prouve : GitLab checkout un commit, tandis que ce helper
prépare le worktree courant. Pour une répétition fidèle, commitez d’abord l’état
de livraison — y compris `demo-spellbook/golden-thread-attestations.json`. Le
helper ne prétend pas qu’un worktree non commité équivaut à un checkout GitLab.

## Structure

    .gitlab-ci.yml           the pipeline: verify, report, and one line that decides to block

    golden-thread-source/    corporate source of authority — POLICY only, versioned by Git tag
      golden-thread.toml       catalog: schema version, default profile
      profiles/                which rules a profile enforces
      rules/ARCH-001.toml      the declarative architecture rule
      rules/DOR-001.toml       the Definition of Ready: rubric pinned, thresholds set
      rules/TEST-001.toml      the test suite: an argv, and an exit code
      rules/SEC-001.toml       bandit, and the Academy's severity threshold
      rules/DOC-001.toml       the documentation stamp
      rules/COOKIE-001.toml    the requirement nothing can check
      rubrics/spec-readiness-1.0.0.toml   the versioned rubric, with its own caveat

    golden-thread-cli/       the tool — ENGINE only, stdlib Python, no harness dependency
      src/golden_thread/
        cli.py                 init / status / verify, human and --json output
        manifest.py            the project manifest (lockfile semantics)
        source.py              Git clone and commit resolution
        policy.py              reading the corporate policy
        subject.py             what a requirement was verified on, by content digest
        evidence.py            the evidence record, and whether it still applies
        verify.py              producing evidence
        status.py              reading evidence, and the path status it implies
        state.py               where records are kept
        report.py              the machine-readable report
        attestation.py         claims the CLI received rather than produced
        rubric.py              loading the versioned rubric from the pinned policy
        readiness.py           publish the rubric, validate an assessment, witness a decision
        attest.py              record a claim no tool can check
        docs.py                stamp a document with the code it describes
        checks/importgraph.py  the real import graph
        checks/layered_dependencies.py   the architecture check engine
        checks/spec_readiness.py         the readiness engine — reads claims, runs no check
        checks/subprocess_engine.py      argv, declared subjects, and "could not run"
        checks/external_command.py       a command, and its exit code
        checks/security_scan.py          a real analyser, and the policy's threshold
        checks/doc_stamp.py              the documentation stamp
        checks/human_attestation.py      a person's word, and nothing else
      tests/

    demo-spellbook/          a consumer project
      golden-thread.json       the manifest: committed, and what CI reads
      golden-thread-attestations.json   committed — human claims travel to CI and review
      MISSION.md               what DOR-001 is about, digested by content
      src/                     the spells
      tests/                   what TEST-001 runs
      docs/ARCHITECTURE.md     what DOC-001 stamps
      .golden-thread/          disposable: policy cache and evidence
      .claude/settings.json     registers the Claude Code adapter's hooks
      .claude/skills/          symlink to the adapter's skills

    claude-code-adapter/     Spike 3 — harness-specific glue, isolated from the core
      hooks/session_start.py   shows Golden Thread context at session start
      hooks/pre_tool_use.py    signals OFF PATH/STALE/NOT READY before Edit/Write, never blocks
      skills/spec-readiness/   Spike 4 — the skill that assesses, and may never approve
      lib/                     the only code that shells out to `golden-thread`
      tests/

    demo/                    the demonstration

Policy et engine sont volontairement séparés. Le dépôt corporate livre les
règles comme données : un tag Git pinne donc la *policy* à laquelle une équipe
est tenue, indépendamment de la version de l’outil qu’elle utilise.

`verify` produit des preuves ; `status` les lit seulement. Réidentifier un sujet
et recalculer un requirement fingerprint ne produit pas de preuve : `status`
n’exécute aucun check, il détermine uniquement si ce qui a été enregistré
s’applique encore.

## Reproduire la démonstration

Trois démonstrations. Spike 1–2 — attacher, vérifier, invalider, réparer :

    ./demo/run-demo.sh

Spike 4 — la Definition of Ready, de NOT READY à READY :

    ./demo/run-dor-demo.sh

Spike 5 — la Definition of Done, tous les chemins d’échec et la pipeline :

    ./demo/run-dod-demo.sh

La dernière fait passer le projet par un état vert, une violation
d’architecture, une vraie faille de sécurité, une attestation manquante, une
réparation après chaque cas, puis termine en exécutant le vrai job GitLab dans
Docker. Docker et un accès réseau sont nécessaires lors de la première
exécution : `demo/install-toolchain.sh` construit un venv jetable avec pytest et
bandit dans `.demo/venv`, et la pipeline télécharge `python:3.12-slim`.

Ou, étape par étape, depuis la racine du dépôt :

    # 0. publish the corporate Golden Thread as a tagged Git repository.
    #    v0.1.0 is the golden path before the DoR; v0.2.0 adds it.
    ./demo/publish-source.sh

    # 1. attach the project
    ./golden-thread-cli/bin/golden-thread -C demo-spellbook \
        init --source "../.demo/golden-thread-source" --ref v0.1.0

    # 2. nothing verified yet — and that is said, not assumed
    ./golden-thread-cli/bin/golden-thread -C demo-spellbook status
    #    UNKNOWN ARCH-001  Protection spells must not depend on Fire
    #           never verified
    #    PATH STATUS   INCOMPLETE                               exit 0

    # 3. run the architecture rule; evidence is produced
    ./golden-thread-cli/bin/golden-thread -C demo-spellbook verify
    #    PASS   ARCH-001  Protection spells must not depend on Fire
    #           subject   src/ - 10 file(s) sha256:cdd324e7312c
    #           method    layered_dependencies - academy-spells - policy v0.1.0 @ 651f644a18bf
    #           producer  golden-thread 0.2.0
    #    PATH STATUS   ON PATH                                  exit 0

    cat demo-spellbook/.golden-thread/evidence.json

    # 4. change a verified file without re-verifying
    printf '\n# a later thought\n' >> demo-spellbook/src/spells/protection/shield.py

    ./golden-thread-cli/bin/golden-thread -C demo-spellbook status
    #    STALE  ARCH-001
    #           recorded PASS no longer applies:
    #             - the code changed: 10 file(s) cdd324e7312c -> 10 file(s) 27d737e001f1
    #    PATH STATUS   STALE                                    exit 3

    # 5. break ARCH-001: a protection spell reaches into Fire
    printf '\nfrom ..elements import fire\n' \
        >> demo-spellbook/src/spells/protection/ward.py

    ./golden-thread-cli/bin/golden-thread -C demo-spellbook verify
    #    FAIL   ARCH-001
    #           spells/protection/ward.py:18
    #           spells.protection.ward -> spells.elements.fire
    #    PATH STATUS   OFF PATH                                 exit 1

    # 6. repair the code — the recorded FAIL is not silently kept either
    git checkout demo-spellbook/src/spells/protection/ward.py
    ./golden-thread-cli/bin/golden-thread -C demo-spellbook status
    #    PATH STATUS   STALE                                    exit 3

    ./golden-thread-cli/bin/golden-thread -C demo-spellbook verify
    #    PATH STATUS   ON PATH                                  exit 0

    # 7. the same report, machine-readable
    ./golden-thread-cli/bin/golden-thread -C demo-spellbook status --json

    git checkout demo-spellbook/src/spells/protection/shield.py

### La Definition of Ready, étape par étape

    # 1. attach to the profile that enforces a DoR
    ./golden-thread-cli/bin/golden-thread -C demo-spellbook init \
        --source "../.demo/golden-thread-source" --ref v0.2.0 \
        --profile academy-spells-ready

    # 2. nothing assessed, nobody asked
    ./golden-thread-cli/bin/golden-thread -C demo-spellbook verify
    #    FAIL   DOR-001  A mission is Ready before implementation starts
    #           - no readiness assessment on record
    #           - no human approval on record. A readiness score never approves itself.
    #    PATH STATUS   NOT READY                                exit 4

    # 3. the rubric is policy, published by the golden path
    ./golden-thread-cli/bin/golden-thread -C demo-spellbook readiness rubric

    # 4. an assessment arrives — from the skill, or canned for reproducibility
    ./golden-thread-cli/bin/golden-thread -C demo-spellbook \
        readiness assess --input demo/assessment-initial.json
    ./golden-thread-cli/bin/golden-thread -C demo-spellbook verify
    #    FAIL   DOR-001
    #           - assessed at 7/10, below the 8 this profile requires
    #           - 2 decision(s) still awaiting a human answer
    #    PATH STATUS   NOT READY                                exit 4

    # 5. the developer answers the decisions in the mission itself
    cp demo/mission-clarified.md demo-spellbook/MISSION.md

    ./golden-thread-cli/bin/golden-thread -C demo-spellbook verify
    #    FAIL   DOR-001
    #           - the assessment was made about a different version of the mission
    #    PATH STATUS   NOT READY                                exit 4

    # 6. re-assess: 9/10, no blockers, no open decisions — and still not ready
    ./golden-thread-cli/bin/golden-thread -C demo-spellbook \
        readiness assess --input demo/assessment-clarified.json
    ./golden-thread-cli/bin/golden-thread -C demo-spellbook verify
    #    FAIL   DOR-001
    #           - assessed at 9/10 against spec-readiness@1.0.0, at or above the 8 ...
    #           - no human approval on record.
    #    PATH STATUS   NOT READY                                exit 4

    # 7. a human decides. Interactive: it prints what is being decided and
    #    asks for a phrase tied to this exact text.
    ./golden-thread-cli/bin/golden-thread -C demo-spellbook readiness approve

    ./golden-thread-cli/bin/golden-thread -C demo-spellbook verify
    #    PASS   DOR-001
    #           - assessed at 9/10 ...   - approved by you@example.com
    #           - an acceptable score and a human decision were both required;
    #             neither would have been enough alone
    #           rests on  assessment: 9/10 by ... under spec-readiness@1.0.0
    #           rests on  human-attestation: approved by ... under spec-readiness@1.0.0
    #    PATH STATUS   ON PATH                                  exit 0

    git checkout demo-spellbook/MISSION.md

### La Definition of Done, étape par étape

    # 0. the corporate golden path, and the project's own toolchain
    ./demo/publish-source.sh          # v0.1.0, v0.2.0, v0.3.0
    ./demo/install-toolchain.sh       # pytest and bandit, into .demo/venv
    export PATH="$PWD/.demo/venv/bin:$PATH"

    # 1. attach to the profile carrying the whole contract
    ./golden-thread-cli/bin/golden-thread -C demo-spellbook init \
        --source "../.demo/golden-thread-source" --ref v0.3.0 \
        --profile academy-spells-done

    # 2. six requirements, and the headline answers the first question first
    ./golden-thread-cli/bin/golden-thread -C demo-spellbook verify
    #    PATH STATUS   NOT READY                                exit 4

    # ... satisfy the Definition of Ready as above ...

    # 3. now the question has changed: is it finished?
    #    PATH STATUS   OFF PATH                                 exit 1
    #    FAIL   DOC-001    - docs/ARCHITECTURE.md carries no golden-thread stamp
    #    FAIL   COOKIE-001 - nobody has attested this

    # 4. the document says which code it describes
    ./golden-thread-cli/bin/golden-thread -C demo-spellbook docs stamp

    # 5. and somebody made the cookies
    ./golden-thread-cli/bin/golden-thread -C demo-spellbook attest COOKIE-001 --show
    ./golden-thread-cli/bin/golden-thread -C demo-spellbook attest COOKIE-001 \
        --attestor "you@example.com" --note "Chocolate chip. 24 of them."
    #    Type the phrase to confirm: attest cdd324e7312c

    ./golden-thread-cli/bin/golden-thread -C demo-spellbook verify
    #    PATH STATUS   ON PATH                                  exit 0

    # 6. a real security defect: a ward that evaluates what it is handed
    printf '\n\ndef improvise(i):\n    return eval(i)\n' \
        >> demo-spellbook/src/spells/protection/ward.py

    ./golden-thread-cli/bin/golden-thread -C demo-spellbook verify
    #    FAIL   SEC-001
    #           src/spells/protection/ward.py:21
    #             MEDIUM B307 (bandit): Use of possibly insecure function ...
    #    FAIL   DOC-001    - the code moved and the documentation did not say so
    #    FAIL   COOKIE-001 - attested about a different version of the work
    #    PATH STATUS   OFF PATH                                 exit 1

Une modification, trois exigences. `ARCH-001` continue de passer car le graphe
d’import n’a pas changé ; l’analyseur trouve la faille, le stamp ne décrit plus
le code et l’attestation ne décrit plus le travail. Une affirmation est liée à
ce qu’elle concernait, qu’elle provienne d’une personne ou d’une règle.

    # 7. repair, re-stamp, re-attest
    git checkout demo-spellbook/src/spells/protection/ward.py

    # 8. and the pipeline replays the whole thing, with no agent
    ./demo/run-ci-locally.sh

`golden-thread` peut aussi être installé comme console script standard :

    pip install -e golden-thread-cli && golden-thread --help

## Le rapport machine-readable

`--json` sur `status` ou `verify` écrit un document unique sur stdout, contenant
les mêmes preuves que la sortie humaine :

    {
      "reportVersion": 1,
      "command": "status",
      "pathStatus": "STALE",
      "exitCode": 3,
      "goldenThread": { "source": "...", "ref": "v0.1.0", "revision": "651f…", "profile": "academy-spells" },
      "requirements": [
        {
          "requirement": "ARCH-001",
          "reportedStatus": "STALE",
          "freshness": {
            "state": "STALE",
            "reasons": ["the code changed: 10 file(s) cdd324e7312c -> 10 file(s) 27d737e001f1"],
            "currentSubjectDigest": "sha256:27d737e001f1…"
          },
          "evidence": { "requirement": "...", "subject": {...}, "producer": {...}, "method": {...}, "result": {...} }
        }
      ]
    }

`reportedStatus` représente ce que l’on peut croire aujourd’hui. Le
`result.status` enregistré reste présent, mais comme historique — jamais comme
réponse actuelle.

## Tests

Exécutez les suites séparément :

    python3 -m pytest golden-thread-cli/tests -q
    python3 -m pytest claude-code-adapter/tests -q

Les deux répertoires contiennent un `conftest.py` sans package. Les combiner
dans une seule invocation pytest peut lier la seconde suite aux fixtures de la
première. Le README de l’adapter documente la même contrainte.

La suite de sécurité exécute réellement bandit et ignore ce test d’intégration —
elle ne le simule pas — lorsque bandit n’est pas installé. Un parser qui est
d’accord avec sa propre fixture mais pas avec l’outil ne prouve rien.

`test_record_compatibility.py` charge littéralement d’anciennes formes de
preuves. Les champs additifs tels que `findings`, `blocking`, `command` et
`requirementFingerprint` conservent des valeurs par défaut conservatrices afin
que les anciens enregistrements restent lisibles ; les enregistrements legacy
sans fingerprint gardent une sémantique de fraîcheur conservatrice.

## Codes de sortie

    0   ON PATH, or INCOMPLETE (nothing verified yet)
    1   OFF PATH
    2   the command itself could not run
    3   STALE: evidence exists but no longer describes the current subject or requirement
    4   NOT READY: a readiness requirement is not satisfied
