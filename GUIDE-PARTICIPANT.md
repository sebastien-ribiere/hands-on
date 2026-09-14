# Golden Thread — carnet de l’apprenti
## Hands-on PlatformCon Paris 2026 · Académie d’Aurélis

**Votre mission : créer Frost Ward, une protection contre le froid, avec un familier IA, et montrer pourquoi le travail peut être accepté.**

Un **golden path** est un chemin supporté par une plateforme : il fournit des conventions, des outils et un parcours pour réaliser un travail de façon répétable. Golden Thread applique ce principe à la délégation aux agents IA. Le chemin aide ; une sortie reste possible, mais doit être explicite et visible.

> L’agent prépare la décision ; l’humain prend la décision.

Vous êtes l’apprenti mage. Claude Code est votre familier pour cet atelier.
Les règles de l’Académie sont la policy ; le grimoire est le projet Python.
Air et Water sont autorisés dans les protections ; Fire y est interdit.
Fire reste autorisé dans les sorts offensifs : le contrôle porte sur les dépendances d’architecture.

## Le parcours, avant de commencer

Les durées sont des repères pour une séance de 60 minutes, avec le téléchargement et la connexion réalisés avant la séance.

| Repère | Durée | Vous allez… | Ce que vous démontrez |
|---|---:|---|---|
| 0 · Entrer à l’Académie | 5 min | ouvrir le lab et visiter les fichiers | où vivent le travail, les règles et les preuves |
| 1 · Voir le chemin | 7 min | attacher une policy et vérifier | une règle nommée produit une preuve |
| 2 · Préparer la mission | 12 min | évaluer et clarifier Frost Ward | une conversation doit devenir un contrat |
| 3 · Décider et déléguer | 10 min | approuver puis faire implémenter | l’évaluation et l’autorisation sont distinctes |
| 4 · Prouver la livraison | 12 min | adopter la DoD et réunir les preuves | tests, sécurité, documentation et attestations ont des portées différentes |
| 5 · Rejouer sans familier | 8 min | exécuter le job dans un autre conteneur | le contrôle fonctionne sans Claude |
| Débrief | 6 min | relire le résultat et ses limites | ce que vous pourriez emporter dans votre IDP |

**Un résultat rouge attendu est une observation réussie.** Cherchez l’exigence et la raison, pas seulement la couleur.

### Où agir ?

- **POSTE** : votre terminal habituel, pour les commandes Docker.
- **LAB** : le shell du conteneur, dans `/workspace/demo-spellbook`.
- **CLAUDE** : un prompt à copier dans Claude Code.

Les commandes LAB se lancent toutes depuis `/workspace/demo-spellbook`.
Dans Claude Code, `/exit` rend la main au shell du lab ; `claude --continue` permet de reprendre la dernière conversation de ce répertoire. Les commandes d’approbation et d’attestation sont exécutées par vous dans ce shell.

## 0 · Entrer à l’Académie

**Pourquoi.** Partager le même environnement sans installer la chaîne Python sur chaque poste.

**Action — POSTE.** Suivez [LAB.md](LAB.md) pour les prérequis et la connexion, puis lancez :

```bash
docker run --rm -it \
  -v golden-thread-workspace:/workspace \
  -v golden-thread-claude:/home/apprentice/.claude \
  ghcr.io/sebastien-ribiere/hands-on:lab
```

Si l’animateur vous a fourni un tag d’image figé, utilisez-le à la place de `lab`.
Le volume de travail conserve votre progression. Relancer le conteneur ne remet pas le lab à zéro.

**Action — LAB.**

```bash
pwd
command -v golden-thread
command -v claude
claude
```

**Ce que je dois observer.** Le répertoire est `/workspace/demo-spellbook`, les deux commandes sont disponibles et vous pouvez échanger avec Claude. Le [README participant](demo-spellbook/README.md) sert de point d’entrée court.

**Action — CLAUDE.**

> Pour tout cet atelier, réponds en français, même si les fichiers sont en anglais. Nous sommes à l’Académie d’Aurélis et tu es mon familier. Fais une visite courte de MISSION.md, src/spells/protection/, tests/ et docs/ARCHITECTURE.md : une phrase sur le rôle de chacun. Ne modifie rien et n’implémente pas encore Frost Ward.

### Les fichiers à reconnaître

| Fichier ou emplacement | Son rôle |
|---|---|
| `MISSION.md` | contrat de la mission : comportement, périmètre, critères observables |
| `src/spells/` et `tests/` | sorts et tests du projet |
| `docs/ARCHITECTURE.md` | documentation du code livré |
| `golden-thread.json` | après l’attachement : source, tag, SHA résolu et profil choisis |
| `.golden-thread/source/` | cache de la policy réellement attachée |
| `.golden-thread/evidence.json` | dernier résultat enregistré par exigence |
| `golden-thread-attestations.json` | évaluations et décisions enregistrées, à conserver avec le projet |
| `/workspace/.gitlab-ci.yml` | vérification rejouée indépendamment de Claude |

La source de démonstration est déjà préparée dans `/workspace/.demo/golden-thread-source`.
Le chemin `../.demo/golden-thread-source` y mène depuis le projet. Il reste identique pendant tout l’atelier.

**Pour raccrocher.** Si Docker ou l’authentification bloque, sollicitez l’animateur et suivez temporairement son écran ou un binôme. N’installez pas une autre chaîne d’outils pendant la séance.

## 1 · Voir le Golden Path avant d’écrire un sort

**Pourquoi.** Rendre le chemin observable : une version, un profil, une règle et une preuve.

**Action — CLAUDE.**

> Depuis /workspace/demo-spellbook, exécute successivement les trois commandes ci-dessous. Après chacune, explique en une phrase ce qui a changé. Ne modifie aucun sort.
>
> `golden-thread init --source ../.demo/golden-thread-source --ref v0.1.0`
>
> `golden-thread status`
>
> `golden-thread verify`
>
> Montre ensuite golden-thread.json et la preuve ARCH-001 dans .golden-thread/evidence.json. Relie requirement, subject, producer, method, result et timestamp aux données réelles.

**Ce que je dois observer sur un workspace neuf.**

| Moment | Observation |
|---|---|
| Après `init`, puis `status` | profil `academy-spells`, `ARCH-001` inconnue, état `INCOMPLETE` |
| Après `verify` | `ARCH-001 PASS`, état `ON PATH`, preuve consultable |

`status` consulte les preuves et leur fraîcheur. `verify` exécute les contrôles et produit les preuves.

**ON PATH à cette étape signifie seulement que le profil d’architecture est satisfait. Frost Ward n’existe pas encore et aucune DoR n’est imposée par ce profil.**

### Observer une sortie du chemin

Cette manipulation porte sur un fichier temporaire et se fait avant l’adoption de la DoR.

**Action — CLAUDE.**

> Nous faisons une expérience hors-piste explicite. Vérifie que src/spells/protection/path_probe.py n’existe pas ; s’il existe, arrête-toi. Crée ce fichier temporaire avec uniquement `from ..elements import fire`. Exécute golden-thread status puis golden-thread verify. Montre la dépendance interdite rapportée. Supprime uniquement le fichier temporaire que tu viens de créer, puis exécute à nouveau golden-thread verify.

**Ce que je dois observer.** `STALE` après modification, puis `ARCH-001 FAIL / OFF PATH` après contrôle, puis `PASS / ON PATH` après retrait et nouvelle vérification. Le hook informe ; il n’empêche pas cette expérience.

**Pour raccrocher.** Demandez à Claude de vérifier que le fichier temporaire a bien été retiré et de relancer `golden-thread verify`. N’effacez pas le cache pour masquer un résultat.

## 2 · Préparer la mission : Conversation ≠ contrat

**Pourquoi.** Détecter les décisions manquantes avant de déléguer l’implémentation.

**Action — CLAUDE.**

> Attache maintenant le profil de readiness :
>
> `golden-thread init --source ../.demo/golden-thread-source --ref v0.2.0 --profile academy-spells-ready`
>
> Exécute golden-thread verify, puis golden-thread readiness rubric. Montre les conditions de DOR-001 et explique pourquoi nous sommes NOT READY. N’implémente rien.

**Ce que je dois observer.** `DOR-001 FAIL` et `NOT READY` : aucune évaluation recevable et aucune approbation humaine ne sont encore enregistrées.

La **Definition of Ready** fixe les conditions requises avant de commencer. Ici : score d’évaluation au moins égal à 8/10, aucun blocker, validation humaine obligatoire.

**Montrer la vraie règle — CLAUDE.**

> Lis `.golden-thread/source/rules/DOR-001.toml`, puis exécute `golden-thread readiness rubric`. Montre les valeurs `subject_files`, `rubric_version`, `min_score`, `max_blockers` et `requires_human_approval`, puis explique-les en français. Lis la policy attachée, pas une règle mémorisée.

Dans cette version, les valeurs sont `MISSION.md`, `1.0.0`, `8`, `0` et `true`. Les identifiants et la policy restent dans leur forme technique ; les documents participant et les évaluations préparées sont en français.

**Action — CLAUDE.**

> Utilise la skill spec-readiness pour évaluer MISSION.md avec la rubric réellement attachée. Lis aussi les sorts existants. Enregistre ton évaluation puis exécute golden-thread verify. Présente en français facts, assumptions, unknowns, blockers, decisions et « Qu’est-ce que je ne sais pas que je ne sais pas ? ». N’approuve rien et arrête-toi avant toute implémentation.

**Ce que je dois observer.** Une évaluation attribuée à son producteur et des questions à résoudre. Le score live peut différer des exemples préparés : c’est une opinion argumentée, pas une mesure objective. Même 10/10 ne suffit pas à approuver.

### Matérialiser les réponses

Pour le parcours commun, le propriétaire de mission retient Water et un sort autonome, sans combinaison avec les protections existantes. Relisez ces choix avant de les transmettre.

**Action — CLAUDE.**

> Voici mes décisions pour cet exercice : Frost Ward utilise Water ; Cold n’est pas un nouvel élément. Le sort expose cast(target: str) -> str. Il fonctionne seul, sans interaction avec shield ou ward ; ces sorts restent inchangés. Le périmètre couvre le nouveau module et ses tests, sans modification du package elements ni équilibrage des sorts. La formulation exacte du résultat est laissée à l’implémentation et devra être illustrée par un test.
>
> Matérialise ces décisions dans MISSION.md, en français, avec des critères observables. Présente le diff, signale toute ambiguïté restante, puis réévalue le document enregistré avec spec-readiness. N’implémente rien et n’approuve rien.

**Ce que je dois observer.** Les décisions sont dans le fichier, puis une nouvelle évaluation porte sur ce texte. Si des blockers subsistent, résolvez-les avant de poursuivre.

| Nature de la décision | Artefact qui fait autorité |
|---|---|
| comportement et scope de Frost Ward | `MISSION.md` |
| choix architectural durable, par exemple spécialisation de Water | ADR si formalisé dans le projet |
| interdiction de Fire dans les protections | policy Golden Thread |

**Limite de cette V0 : `DOR-001` calcule le digest de `MISSION.md` uniquement. Un ADR n’entre pas automatiquement dans ce digest.** Toute décision nécessaire à la readiness doit donc être matérialisée dans la mission ; une simple référence vers un ADR ne protège pas contre une modification de cet ADR.

**Pour raccrocher.** Si vous manquez de temps, utilisez le [point de reprise de la DoR](#reprise-dor). Il importe une mission et une évaluation préparées et conserve la décision humaine.

## 3 · Décider, puis déléguer Frost Ward

**Pourquoi.** Séparer l’évaluation proposée par le familier de votre décision de démarrer.

**Action — LAB, vous-même.** Quittez momentanément Claude avec `/exit`. Relisez l’évaluation. Si vous l’acceptez, remplacez l’identité d’exemple par la vôtre :

```bash
golden-thread readiness approve --attestor "votre-nom"
golden-thread verify
```

Lisez puis saisissez vous-même la phrase de confirmation affichée. **Ne demandez jamais à Claude d’exécuter cette approbation.**

**Ce que je dois observer.** `DOR-001 PASS` et, si l’architecture reste conforme, `ON PATH`. Une approbation ne compense ni un score insuffisant ni un blocker.

**Action — LAB.**

```bash
claude --continue
```

**Action — CLAUDE.**

> Exécute golden-thread verify et vérifie que DOR-001 est PASS. Si le résultat est NOT READY, propose de résoudre la readiness ou de demander explicitement un départ hors-piste, puis attends mon choix. Sinon, implémente Frost Ward selon MISSION.md, avec ses tests, en respectant ARCH-001. Exécute les tests et golden-thread verify. Présente les fichiers modifiés et les résultats réels. Ne change pas la mission approuvée pour l’adapter à ton code.

**Ce que je dois observer.** Un module `frost_ward`, des tests associés et une architecture conforme. Si la mission doit évoluer, revenez à l’évaluation puis à l’approbation : le digest de la mission a changé.

**Pour raccrocher.** Demandez au familier : « Lis MISSION.md et l’état Golden Thread ; indique ce qui manque pour terminer cette seule mission. » Il n’existe pas de snapshot d’implémentation de rattrapage annoncé par ce guide. Si le développement prend trop de temps, poursuivez en binôme.

## 4 · Prouver la livraison avec la DoD

**Pourquoi.** Un sort fonctionnel doit aussi satisfaire le contrat de livraison de l’Académie.

**Action — CLAUDE.**

> Attache le profil final :
>
> `golden-thread init --source ../.demo/golden-thread-source --ref v0.3.0 --profile academy-spells-done`
>
> Exécute d’abord golden-thread status et explique quelles preuves subsistent et quelles exigences n’ont pas encore de preuve. Puis exécute golden-thread verify et présente ce qui manque pour terminer.

**Ce que je dois observer.** Six exigences. Les preuves DOR et ARCH peuvent subsister si leur sujet et leur contrat n’ont pas changé. Les quatre nouvelles exigences n’ont initialement aucune preuve ; verify les évalue. DOC et COOKIE doivent normalement échouer à ce premier contrôle.

> Une nouvelle version de policy ajoute des exigences. Les preuves existantes survivent lorsque leur sujet et leur contrat restent inchangés.

| Exigence | Provider | Ce que son PASS établit |
|---|---|---|
| `DOR-001` | évaluation + décision enregistrées | conditions de readiness satisfaites pour cette mission |
| `TEST-001` | commande pytest | la suite exécutée termine avec succès ; sa pertinence reste à examiner |
| `ARCH-001` | analyse du graphe d’import Python | dépendances conformes à la règle d’architecture |
| `SEC-001` | Bandit | aucun finding bloquant selon les seuils de la policy ; cela ne garantit pas l’absence de vulnérabilité |
| `DOC-001` | stamp du digest du code | document estampillé pour ce code exact ; cela ne certifie pas sa justesse |
| `COOKIE-001` | attestation nominative | quelqu’un a déclaré avoir préparé et partagé les cookies ; aucun outil n’a observé ce fait |

**Action — CLAUDE.**

> Traite les éventuels échecs TEST, ARCH et SEC en t’appuyant sur leurs résultats réels. Mets ensuite docs/ARCHITECTURE.md en cohérence avec Frost Ward et montre-moi le diff. Ne modifie ni les seuils ni les règles pour obtenir PASS. N’exécute ni docs stamp ni attest ; laisse-moi ces étapes.

**Action — LAB, vous-même.** Après lecture et éventuelle correction de la documentation :

```bash
golden-thread docs stamp
golden-thread attest COOKIE-001 --show
```

La règle des cookies montre une exigence maison dont la vérification repose sur une personne. **Attestez seulement si les cookies ont réellement été préparés et partagés pour cet exercice.** Si c’est le cas :

```bash
golden-thread attest COOKIE-001 --attestor "votre-nom" --note "Cookies préparés et partagés pendant l’atelier."
golden-thread verify
```

Sinon, conservez le manque visible et lancez seulement `golden-thread verify`. Un état `OFF PATH` expliqué est un résultat pédagogique valide ; ne fabriquez pas une attestation pour rendre l’écran vert.

**Ce que je dois observer.** `ON PATH` si les six exigences sont satisfaites. Sinon, le rapport nomme précisément ce qui reste ouvert.

**Pour raccrocher.** Un changement de code peut invalider le stamp DOC et l’attestation COOKIE. Terminez le code avant ces actes. Relancez verify pour distinguer une preuve périmée d’un contrôle qui échoue réellement.

### Expérience sécurité — facultative, sur signal de l’animateur

**Action — CLAUDE.**

> Pour cette expérience hors-piste explicite, vérifie que src/spells/protection/security_probe.py n’existe pas. S’il existe, arrête-toi. Crée ce fichier temporaire avec une fonction improvise(value) qui retourne eval(value), sans jamais appeler cette fonction. Exécute golden-thread verify et montre le finding Bandit, son identifiant, sa sévérité et son caractère bloquant. Supprime uniquement ce fichier temporaire, puis relance verify.

Attendez-vous à un finding `B307` et à `SEC-001 FAIL` pendant l’expérience.
DOC et COOKIE peuvent aussi ne plus s’appliquer au code modifié. Après retour exact au code initial, leurs affirmations peuvent redevenir applicables ; lisez le rapport avant toute nouvelle attestation.

## 5 · Rejouer sans familier

**Pourquoi.** Faire vérifier le même travail par un environnement qui n’exécute aucun agent IA.

**Action — LAB.** Quittez Claude. Examinez ce qui va voyager avec le projet :

```bash
git status --short
git diff -- MISSION.md src tests docs golden-thread.json golden-thread-attestations.json
```

Les nouveaux fichiers non suivis n’apparaissent pas dans ce diff : lisez aussi ceux indiqués par `git status`. Après revue, conservez l’état de livraison :

```bash
git add MISSION.md src tests docs golden-thread.json golden-thread-attestations.json
git diff --cached --stat
git commit -m "Complete Frost Ward workshop delivery"
```

Si Git indique qu’il n’y a rien à commiter, poursuivez. Les attestations sont conservées avec le projet ; le cache et les preuves calculées restent jetables.

**Action — POSTE, dans un second terminal.** Utilisez la commande de [replay du job GitLab dans LAB.md](LAB.md#rejouer-le-job-gitlab-sans-donner-accès-au-docker-du-poste-au-lab). Elle lit le volume du lab en lecture seule, en fait une copie et exécute le job dans un autre conteneur.

N’exécutez pas cette commande depuis le LAB : celui-ci ne dispose pas du socket Docker du poste.

**Ce que je dois observer.** Le journal affiche la policy épinglée, son SHA, le profil et les verdicts des six exigences. Il doit refléter les exigences encore ouvertes, cookies compris. La policy du projet fait échouer le job quand le verdict l’exige.

Le replay local lit les instructions de `.gitlab-ci.yml`, mais copie le workspace courant : il ne constitue pas une exécution sur un runner GitLab et ne teste pas tout le service GitLab. Le vrai runner part d’un commit. Il conserve le rapport JSON comme artefact, y compris en échec ; le conteneur local jetable ne publie pas cet artefact.

**Pour raccrocher.** Si le téléchargement ou le réseau échoue, la vérification n’a pas été démontrée. Suivez le replay de l’animateur et gardez cette étape comme non vérifiée sur votre poste.

## Retrouver son point d’arrêt

**Action — LAB.**

```bash
pwd
golden-thread status
```

| Observation | Prochaine action |
|---|---|
| Pas de manifest | reprendre l’attachement de l’étape 1 |
| `INCOMPLETE` / `UNKNOWN` | lancer verify pour produire les preuves manquantes |
| `NOT READY` | lire les raisons de DOR-001 ; reprendre évaluation, décisions ou approbation |
| `STALE` | identifier ce qui a changé, puis vérifier ; ne pas supposer l’ancien PASS valable |
| `OFF PATH` | lire l’exigence en échec ; corriger ou rendre la déviation explicite |
| `ON PATH` | lire aussi le profil : v0.1, v0.2 et v0.3 ne prouvent pas la même chose |
| Erreur d’exécution | résoudre l’erreur d’outil ; aucun verdict de conformité ne peut être déduit |

**Prompt de reprise — CLAUDE.**

> Ne modifie rien. Lis MISSION.md, golden-thread.json et golden-thread status. Indique mon profil, les exigences non satisfaites, ce qui a déjà été fait et une seule prochaine action. Distingue les faits observés des suppositions. N’approuve rien.

### Reprise DoR

Ce raccourci utilise des fixtures de démonstration. Il remplace votre mission locale après sauvegarde et enregistre une évaluation préparée. Il ne représente pas une nouvelle analyse live de Claude.

**Action — LAB, uniquement si vous choisissez ce raccourci.**

```bash
cp -i MISSION.md MISSION.before-recovery.md
cp ../demo/mission-clarified.md MISSION.md
golden-thread readiness assess --input ../demo/assessment-clarified.json
golden-thread verify
```

Si une sauvegarde existe déjà, ne l’écrasez pas ; choisissez un autre nom avant de poursuivre.
Relisez la mission importée, en français. Si vous la modifiez ensuite, demandez une nouvelle évaluation. Le score préparé est 9/10 ; il ne remplace pas votre décision. Reprenez l’étape 3 pour l’approbation humaine.

### Petits incidents

| Incident | Reprise |
|---|---|
| Claude répond en anglais | rappeler « Réponds en français » ; ne traduire la mission qu’avant sa réévaluation |
| Mauvais répertoire | dans le LAB : `cd /workspace/demo-spellbook` |
| Commande golden-thread introuvable | vérifier que vous êtes dans le LAB, pas sur le poste |
| Contraste insuffisant | utiliser un thème contrasté du terminal ; dans Claude, ouvrir `/theme` et choisir le thème adapté ; lire aussi PASS/FAIL |
| Fermeture du conteneur | relancer la commande Docker avec les mêmes volumes |
| Nouvelle image, ancien travail toujours présent | le volume conserve l’ancien workspace ; ne pas le supprimer pendant l’atelier |
| Besoin de tout recommencer | suivre LAB.md seulement après sauvegarde : supprimer le volume détruit la progression |

## Avant de quitter l’Académie

Vous devez pouvoir montrer le contrat accepté, la version de policy et le profil,
une preuve avec son sujet et sa méthode, une décision humaine enregistrée et le
résultat du replay indépendant.

Golden Thread peut accueillir plusieurs workflows, dont SDD et Agentic Scrum.
Ce parcours illustre un chemin supporté pour déléguer, décider et vérifier :
les règles et leurs preuves restent utilisables lorsque le familier change.

**Question de débrief : quelle exigence de votre organisation confieriez-vous à un contrôle déterministe, à un artefact de preuve ou à une attestation humaine ?**
