# Bienvenue à l’Académie d’Aurélis

**Votre mission : créer Frost Ward avec Claude Code, puis montrer pourquoi le travail peut être accepté.**

Air et Water sont autorisés dans les protections ; Fire y est interdit.
Pour les prérequis et la connexion, consultez [LAB.md](../LAB.md).


## Séquence participant

Vous pouvez avancer à votre rythme ou reprendre à l’étape où vous vous êtes arrêté.
Le [guide détaillé](../GUIDE-PARTICIPANT.md) explique les décisions et les limites de chaque contrôle.

**Où agir : POSTE** = terminal de votre ordinateur ; **LAB** = shell du conteneur ;
**CLAUDE** = prompt à copier dans Claude Code. Tous les chemins des étapes 1 à 5
partent de `/workspace/demo-spellbook`, même si vous lisez ce README à la racine du dépôt.
Dans Claude, `/exit` rend le shell ; `claude --continue` reprend la conversation.
Copiez les blocs un à un et regardez le résultat avant de poursuivre.

Le lab et le replay CI affichent les retours Golden Thread en français.
Les identifiants (`PASS`, `FAIL`, `SEC-001`…), les rapports JSON et les
diagnostics bruts des outils restent inchangés. Bandit B307 est accompagné
d’une explication française.

[0 · Démarrer](#lab-0) · [1 · Voir le chemin](#lab-1) ·
[2 · Préparer](#lab-2) · [3 · Décider et déléguer](#lab-3) ·
[4 · Prouver](#lab-4) · [5 · Rejouer](#lab-5) · [Reprendre](#lab-reprise)

Le contrat final comprend DOR, TEST, ARCH, SEC, DOC et COOKIE. Nous activons des
profils progressivement pour le découvrir ; en projet, DoR et DoD sont connues
avant de commencer. Un `ON PATH` se lit toujours avec le profil attaché.

<a id="lab-0"></a>
### 0 · Démarrer et se repérer

**POSTE.** Docker, un accès Claude Code et le réseau sont nécessaires. Utilisez
le tag figé fourni par l’animateur à la place de `lab` si vous en avez un.

```bash
docker run --rm -it \
  -v golden-thread-workspace:/workspace \
  -v golden-thread-claude:/home/apprentice/.claude \
  ghcr.io/sebastien-ribiere/hands-on:lab
```

Un volume déjà utilisé conserve votre progression. Si vous changez son nom,
utilisez le même dans la commande de replay à l’étape 5.

**LAB.**

```bash
pwd
command -v golden-thread
command -v claude
claude
```

**CLAUDE.**

> Pour cet atelier, réponds en français. Tu es mon familier à l’Académie d’Aurélis.
> Lis MISSION.md, puis fais une visite courte de src/spells/, tests/ et
> docs/ARCHITECTURE.md. Ne modifie rien et n’implémente pas encore.

**Repère atteint :** Claude répond dans `/workspace/demo-spellbook` et vous retrouvez la mission.

<a id="lab-1"></a>
### 1 · Voir le chemin et une preuve

**CLAUDE.** Demandez : « Exécute ces commandes dans l’ordre, explique chaque résultat,
puis montre golden-thread.json et la preuve ARCH-001 dans .golden-thread/evidence.json.
Ne modifie aucun sort. »

```bash
golden-thread init --source ../.demo/golden-thread-source --ref v0.1.0
golden-thread status
golden-thread verify
```

**À observer sur un workspace neuf :** `INCOMPLETE` avant verify, puis `ARCH-001 PASS / ON PATH`.
La preuve indique exigence, sujet, producteur, méthode, résultat et date.
Frost Ward reste à écrire.

**CLAUDE — expérience Fire.**

> J’autorise une expérience hors-piste temporaire. Vérifie que
> src/spells/protection/path_probe.py n’existe pas ; s’il existe, arrête-toi sans
> le modifier. Crée uniquement ce fichier avec `from ..elements import fire`.
> Exécute golden-thread status puis golden-thread verify. Montre la dépendance
> interdite et attends mon signal. Ne modifie pas la règle.

**À observer :** `STALE` puis `ARCH-001 FAIL / OFF PATH`. Autoriser l’expérience
ne change pas le verdict. Après lecture, donnez le signal dans Claude :

> Supprime uniquement path_probe.py que tu viens de créer. Relance golden-thread
> verify et confirme que ce fichier a disparu.

**Repère atteint :** sonde retirée, architecture à nouveau conforme.

<a id="lab-2"></a>
### 2 · Préparer la mission

**CLAUDE.** Faites exécuter ces commandes ; demandez ensuite de lire la règle attachée.
Aucune implémentation à cette étape.

```bash
golden-thread init --source ../.demo/golden-thread-source --ref v0.2.0 --profile academy-spells-ready
golden-thread verify
golden-thread readiness rubric
```

> Lis .golden-thread/source/rules/DOR-001.toml. Montre le sujet évalué, la version
> de la grille, le score minimum, les blockers autorisés et l’approbation requise.

**À observer :** `NOT READY` faute d’évaluation recevable et d’approbation.
Les conditions sont score ≥ 8/10, zéro blocker et approbation humaine.
Le digest couvre MISSION.md, pas le contenu des ADR.

**CLAUDE — évaluer.**

> Utilise spec-readiness pour évaluer MISSION.md avec la grille attachée.
> Lis les sorts existants. Enregistre ton évaluation et exécute golden-thread
> verify. Présente facts, assumptions, unknowns, blockers, decisions et
> « Qu’est-ce que je ne sais pas que je ne sais pas ? ». N’implémente rien,
> n’approuve rien et attends mes réponses.

Le score est une opinion argumentée et peut varier. Même 10/10 attend votre approbation.

**CLAUDE — répondre seulement dans le chat.**

> Frost Ward utilise Water et reste autonome. Ne modifie aucun fichier et
> n’enregistre aucune nouvelle évaluation. Exécute golden-thread verify
> et explique ce que ma réponse a changé dans l’état enregistré. N’implémente
> rien et n’approuve rien.

**À observer :** mission et évaluation enregistrée inchangées, approbation toujours
absente. Lisez les raisons affichées ; les décisions ouvertes ne constituent pas
une condition bloquante indépendante dans cette V0.

**CLAUDE — écrire les décisions, puis réévaluer.**

> Voici mes décisions pour cet exercice : Frost Ward utilise Water ; Cold n’est
> pas un nouvel élément. Il expose cast(target: str) -> str et fonctionne seul,
> sans interaction avec shield ou ward, qui restent inchangés. Le périmètre couvre
> le nouveau module et ses tests, sans changement du package elements ni équilibrage.
> La formulation exacte du résultat est laissée à l’implémentation et doit être
> illustrée par un test. Écris ces décisions dans MISSION.md en français, avec
> des critères observables. Montre le diff et les ambiguïtés restantes, puis
> réévalue le texte enregistré avec spec-readiness. Exécute golden-thread verify.
> N’implémente rien et n’approuve rien.

**Repère atteint :** mission relue et évaluation portant sur ce texte.
Résolvez les blockers et les questions nécessaires avant l’étape 3.
Le [raccourci DoR préparé](../GUIDE-PARTICIPANT.md#reprise-dor) permet de reprendre sans inventer une analyse live.

<a id="lab-3"></a>
### 3 · Décider, déléguer et accepter le sort

**VOUS.** Dans Claude, saisissez `/exit`. Relisez l’évaluation. Si vous l’acceptez,
exécutez vous-même dans le LAB, en remplaçant l’identité :

```bash
golden-thread readiness approve --attestor "votre-nom"
golden-thread verify
```

Saisissez vous-même la phrase de confirmation. **Ne confiez jamais readiness approve
à Claude.** Votre approbation ne compense ni un score insuffisant ni un blocker.

**LAB.**

```bash
claude --continue
```

**CLAUDE — implémenter.**

> Exécute golden-thread verify. Si DOR-001 n’est pas PASS, explique ce qui manque
> et attends ma décision avant de coder. Si NOT READY, propose de résoudre la
> readiness ou demande un départ hors-piste explicite. Sinon, implémente Frost Ward
> selon MISSION.md, avec ses tests, en respectant ARCH-001. Exécute les tests et
> golden-thread verify. Présente le diff et les résultats. Ne change pas la mission
> approuvée pour l’adapter à ton code.

**CLAUDE — réceptionner.**

> Pour chaque critère de MISSION.md, montre le comportement obtenu et le test
> associé. Exécute un exemple de cast(target) et les tests. Signale ce qui
> n’est pas démontré et attends ma décision.

**Repère atteint :** vous avez examiné le résultat et accepté ou demandé une
correction. Après correction, refaites cette revue. Une modification de la mission
demande une nouvelle évaluation et approbation. Cette réception n’ajoute pas
d’attestation au moteur. Si le travail est incomplet, gardez-le visible et
reprenez avec le guide ou un binôme.

<a id="lab-4"></a>
### 4 · Vérifier la livraison

**CLAUDE.** Faites exécuter ces commandes, avec status avant verify.

```bash
golden-thread init --source ../.demo/golden-thread-source --ref v0.3.0 --profile academy-spells-done
golden-thread status
golden-thread verify
```

**À observer :** six exigences. DOR et ARCH peuvent conserver leurs preuves si
leurs sujets et contrats sont inchangés ; TEST, SEC, DOC et COOKIE sont ajoutées.
DOC et COOKIE doivent normalement échouer au premier contrôle.

> Corrige les échecs TEST, ARCH et SEC d’après les résultats réels. Mets
> docs/ARCHITECTURE.md en cohérence avec Frost Ward et montre le diff.
> Ne modifie ni les règles ni les seuils. Laisse-moi docs stamp et attest.

**CLAUDE — expérience Bandit : les tests passent, et la sécurité ?**

> Nous allons vérifier que le contrôle de sécurité détecte un défaut, même
> lorsque les tests passent.
>
> Ajoute temporairement une fonction qui utilise `eval()` dans un nouveau fichier
> `src/spells/protection/security_probe.py`. Ne l’exécute jamais. Si ce fichier
> existe déjà, arrête-toi sans le modifier. Ne change aucun autre fichier.
>
> Lance `golden-thread verify`, puis explique quel problème Bandit a détecté,
> où il se trouve et pourquoi la règle `SEC-001` le considère comme un échec.
> Appuie ton explication sur le rapport et la règle attachée au projet.
>
> Garde le fichier le temps que nous lisions le résultat ensemble, puis attends
> mon accord pour le retirer.

**À observer :** Bandit signale B307, l’usage potentiellement dangereux de
`eval()`, avec une sévérité MEDIUM. La policy fixe les seuils qui rendent
l’exigence non satisfaite : ici, sévérité et confiance au moins MEDIUM,
donc `SEC-001 FAIL`.

Ces seuils se lisent dans `.golden-thread/source/rules/SEC-001.toml` :
`fail_on_severity` pour la sévérité, `min_confidence` pour la confiance du scanner.
Bandit détecte le problème ; la policy fixe les seuils d’échec. Plus tard,
la configuration CI décidera de l’effet de ce verdict sur la pipeline.

**CLAUDE — après lecture, retirer le défaut temporaire.**

> Retire uniquement le fichier temporaire `src/spells/protection/security_probe.py`
> que tu viens de créer, puis relance `golden-thread verify`. Vérifie que
> `SEC-001` passe et indique si d’autres exigences restent à traiter.
> Ne change ni les règles ni les attestations.

**À observer :** le fichier temporaire et son diagnostic B307 ont disparu.
`SEC-001` passe si aucun autre diagnostic n’atteint les seuils de la policy.
D’autres exigences peuvent encore échouer ; un PASS du scanner ne garantit
pas l’absence de vulnérabilité.

**Avant de passer à la CI :** confirmez que
`src/spells/protection/security_probe.py` a disparu et lisez le nouveau verdict
de `SEC-001`. Si cette sonde reste présente, la CI retrouvera volontairement
le même défaut B307. Le [dépannage du replay](#lab-ci-sec) explique comment reprendre.

**VOUS.** Quittez Claude avec `/exit`. Après lecture de la documentation, dans le LAB :

```bash
golden-thread docs stamp
golden-thread attest COOKIE-001 --show
```

Le stamp vise ce code exact ; il ne certifie pas la justesse de la prose.
**Seulement si les cookies ont réellement été préparés et partagés**, attestez vous-même :

```bash
golden-thread attest COOKIE-001 --attestor "votre-nom" --note "Cookies préparés et partagés pendant l’atelier."
```

Avec ou sans cookies, vérifiez :

```bash
golden-thread verify
```

**Repère atteint :** sondes retirées, résultats relus. `ON PATH` si tout est satisfait ;
sinon, le rapport garde les manques visibles. Ne fabriquez pas une attestation
pour suivre le rythme de la salle.

<a id="lab-5"></a>
### 5 · Conserver le travail et rejouer

**LAB.** Si vous êtes dans Claude, quittez-le avec `/exit`. Examinez la livraison :

```bash
git status --short
git diff -- MISSION.md src tests docs golden-thread.json golden-thread-attestations.json
```

Lisez aussi les fichiers non suivis listés par status : ils n’apparaissent pas dans
ce diff. Après revue :

```bash
git add MISSION.md src tests docs golden-thread.json golden-thread-attestations.json
git diff --cached --stat
git commit -m "Complete Frost Ward workshop delivery"
```

S’il n’y a rien à commiter, poursuivez. Les attestations et le manifest voyagent
avec le projet ; le cache et les preuves calculées restent jetables.

**POSTE — second terminal, hors du LAB.**

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

**Repère atteint :** le job affiche la policy, son SHA, le profil et les verdicts.
Les exigences encore ouvertes peuvent faire échouer le job. Ce replay copie le
workspace et exécute le job sans Claude ; un runner GitLab part d’un commit.
Le conteneur local est jetable et ne publie pas son rapport comme artefact.
Si un téléchargement échoue, cette étape reste non vérifiée sur votre poste.

<a id="lab-ci-sec"></a>
#### Si la CI affiche SEC-001 FAIL avec B307

**Pourquoi :** si le rapport désigne
`src/spells/protection/security_probe.py:2`, le fichier créé pour l’expérience
Bandit est encore dans le workspace. Bandit détecte l’usage de `eval()` même
si la fonction n’est jamais appelée. Ce constat est attendu tant que la sonde
reste présente.

Dans cet exemple, Bandit fournit le diagnostic B307 et la sévérité MEDIUM.
La règle SEC-001 fixe les seuils de sévérité et de confiance à MEDIUM ; ce
diagnostic rend donc l’exigence non satisfaite. Le job propage le code de sortie
de la vérification, ce qui fait échouer la pipeline selon la configuration
de ce projet.

**Les sorties restent en partie en anglais.** Voici comment lire ce passage :

| Dans le terminal | Ce que cela signifie |
|---|---|
| `No known security defect at MEDIUM or above` | Le contrôle recherche les défauts signalés à partir du seuil de sévérité MEDIUM. Un PASS ne garantit pas l’absence de vulnérabilité. |
| `MEDIUM B307 (bandit)` | Bandit signale un usage potentiellement dangereux de `eval()`, de sévérité moyenne. |
| `ran ... over 12 file(s)` | Le scanner a analysé 12 fichiers dans cet exemple ; votre nombre peut différer. |
| `this profile fails on MEDIUM and above, at MEDIUM confidence and above` | Le profil échoue dès les seuils MEDIUM de sévérité et de confiance. |
| `PIPELINE FAILED BY THIS PROJECT'S POLICY` | La pipeline échoue parce que ce projet propage le résultat de la vérification. |

La suggestion de Bandit concernant `ast.literal_eval` fait partie de son
diagnostic générique. Pour cette expérience, retirez la sonde temporaire :
elle ne fait pas partie de Frost Ward. Si le rapport désigne un autre fichier
ou un autre diagnostic, examinez ce résultat avant de choisir la correction.

**Action — CLAUDE, dans le LAB d’origine.** Reprenez avec `claude --continue`
si nécessaire, puis donnez ce prompt :

> Le replay CI signale B307 dans src/spells/protection/security_probe.py.
> Retire uniquement ce fichier créé pour notre expérience Bandit. Confirme son
> absence, puis exécute golden-thread verify. Montre les verdicts et explique
> les éventuels échecs en français. Ne change ni les règles ni les seuils.
> N’exécute aucune approbation, docs stamp ou attestation à ma place.

**Ce que je dois observer :** le finding B307 de cette sonde disparaît.
SEC-001 passe si aucun autre diagnostic ne dépasse les seuils du profil.
D’autres exigences peuvent encore échouer : lisez le rapport complet.

Le retrait change le digest du code. Si DOC-001 indique que son stamp ne
correspond plus au code courant, relisez `docs/ARCHITECTURE.md` et faites-la
corriger si nécessaire. Après cette revue, quittez Claude avec `/exit` et
exécutez vous-même dans le LAB :

```bash
golden-thread docs stamp
golden-thread verify
```

Refaites le stamp uniquement s’il est nécessaire et après lecture.
La mission inchangée ne demande pas une nouvelle approbation DoR du seul fait
du retrait de cette sonde.

Relisez et conservez ensuite la correction avec la séquence Git du début de
l’[étape 5](#lab-5), puis relancez la même commande Docker de replay depuis votre
POSTE. Corrigez le workspace d’origine : le conteneur de replay travaille sur
une copie jetable. Le résultat final reflète toutes les exigences ; un manque
restant, y compris COOKIE-001, doit rester visible.

<a id="lab-reprise"></a>
### Reprendre sans recommencer

Pour une nouvelle répétition depuis zéro : [reset avec sauvegarde](../LAB.md#repartir-de-zéro).

**LAB**, après `/exit` si nécessaire :

```bash
pwd
golden-thread status
```

| Ce que vous voyez | Où reprendre |
|---|---|
| Pas de manifest | [1 · Attachement](#lab-1) |
| INCOMPLETE / UNKNOWN | lancer verify, puis lire les exigences manquantes |
| NOT READY | [2 · Préparation](#lab-2), puis [3 · Approbation](#lab-3) |
| STALE | identifier ce qui a changé, puis relancer verify |
| OFF PATH | lire l’exigence en échec ; corriger ou décider explicitement de la déviation |
| ON PATH | lire aussi le profil : architecture, readiness ou livraison |
| Erreur d’exécution | résoudre l’erreur ; aucun verdict n’a été établi pour ce contrôle |

Pour reprendre la conversation : `claude --continue`, puis :

> Ne modifie rien. Lis MISSION.md, golden-thread.json et golden-thread status.
> Indique mon profil, ce qui a déjà été fait, les exigences ouvertes et une seule
> prochaine action. Distingue les faits des suppositions. N’approuve rien.

Relancer Docker avec les mêmes volumes conserve le travail. Évitez de rejouer
les commandes init des premières étapes si vous êtes déjà sur un profil plus
avancé ; commencez par status. Les incidents et la reprise DoR préparée sont
détaillés dans le [guide](../GUIDE-PARTICIPANT.md#retrouver-son-point-darrêt).

