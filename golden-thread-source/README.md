# Golden Thread - source corporate

Source d’autorité du golden path Golden Thread.

- `golden-thread.toml` - catalogue : version de schéma, profil par défaut
- `profiles/<name>.toml` - règles imposées par un profil
- `rules/<id>.toml` - définitions déclaratives des règles
- `rubrics/<id>-<version>.toml` - rubrics versionnées utilisées pour les évaluations

Ce dépôt contient **uniquement la policy**. L’engine de vérification vit dans la
CLI `golden-thread`. Cette séparation donne du sens à un tag Git : les projets
consommateurs pinnent une version de la policy, pas une version de l’outil.

## Profils

    academy-spells         ARCH-001
    academy-spells-ready   DOR-001, ARCH-001
    academy-spells-done    DOR-001, TEST-001, ARCH-001, SEC-001, DOC-001, COOKIE-001

Chaque profil reprend le précédent et formalise une partie supplémentaire du
contrat. Adopter un profil correspond à un changement de policy publié sous un
nouveau tag ; une équipe l’adopte en déplaçant la ref qu’elle pinne.

Il n’existe pas d’objet séparé « Definition of Ready » ou « Definition of Done »
dans ce schéma, et il n’en faut pas. Un profil est la liste des exigences
auxquelles une équipe est soumise ; la DoR et la DoD sont cette liste observée à
deux moments différents. Ce qui les distingue dans un rapport n’est pas un
label écrit ici, mais le comportement des engines : une exigence de readiness
rapporte `NOT READY`, car le travail n’a jamais été accepté ; les autres
rapportent `OFF PATH`, car quelque chose dans le travail n’est pas terminé.

## Exigences et valeur de chaque type de preuve

    ARCH-001     le vrai graphe d’import du projet
    TEST-001     une commande nommée ici, et son code de sortie
    SEC-001      bandit, et le seuil de sévérité défini dans cette règle
    DOC-001      un stamp de digest dans la documentation
    COOKIE-001   la parole d’une personne, et rien de plus

La dernière est volontairement inattendue et joue un rôle essentiel : toutes
les organisations ont dans leur Definition of Done quelque chose qu’aucun outil
ne peut établir. Un langage de policy capable d’exprimer uniquement ce qui est
vérifiable supprimerait silencieusement ces exigences. Lire
`rules/COOKIE-001.toml` avant de la retirer.

## Où s’arrête la CLI et où commence ce dépôt

Ajouter une *exigence* est un changement dans ce dépôt et entraîne un nouveau
tag. Ajouter un nouveau *type* de vérification est un changement dans la CLI,
car un engine est du code. `v0.1.0` et `v0.2.0` n’ont nécessité aucune nouvelle
release de CLI ; `v0.3.0` a introduit quatre exigences, dont deux nécessitaient
des engines qui n’existaient pas encore.

Cette frontière mérite de rester visible. Une règle qui déclare
`check = "security_scan"` désigne quelque chose que l’outil doit déjà savoir
faire. TOML ne peut pas inventer un engine.

## Les règles peuvent nommer une commande, sous forme de liste argv

`TEST-001` et `SEC-001` déclarent quoi exécuter :

    command = ["python3", "-m", "pytest", "-q", "tests"]

Une liste, jamais une chaîne. Aucun shell n’est impliqué : rien à quoter, rien à
expanser, aucun moyen pour un fichier de policy de glisser une seconde commande
à l’insu du lecteur. L’argv est enregistré dans la preuve, afin que ce qui a été
exécuté apparaisse dans le rapport et pas seulement dans ce dépôt.

C’est ici qu’adopter un golden path signifie accepter d’exécuter ses
vérifications. C’était déjà vrai pour un include `.gitlab-ci.yml` ; ici c’est
explicite plutôt qu’implicite.

## Les rubrics sont versionnées deux fois

Par leur nom de fichier : publier une nouvelle version revient à ajouter un
fichier et modifier une ligne dans la règle qui le pinne, tous deux visibles dans
un diff, tandis que l’ancienne rubric reste présente pour les éléments qui la
référencent encore. Et par le champ `version` contenu dans le fichier, enregistré
par chaque évaluation.

Ce deuxième niveau rend le score auditable. Une évaluation produite sous
`spec-readiness@1.0.0` n’est jamais silencieusement réinterprétée comme un score
selon `1.1.0` : elle cesse de s’appliquer et indique sous quelle version elle a
été produite.

Une rubric porte également son propre `caveat`, affiché textuellement par la CLI
plutôt que paraphrasé. Le fait qu’un score de readiness soit une évaluation et
non une mesure fait partie de la policy ; ce n’est pas un avertissement ajouté
par l’outil.

Utilisé par les projets avec :

    golden-thread init --source <this-repo> --ref v0.3.0 \
        --profile academy-spells-done
