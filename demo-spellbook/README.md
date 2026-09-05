# demo-spellbook

Un projet consommateur rattaché à Golden Thread.

    src/spells/
      elements/   air, water, fire
      protection/ shield, ward     <- soumis à ARCH-001
      offense/    flame_lance      <- peut utiliser fire librement
    tests/        ce que TEST-001 exécute
    docs/         ce que DOC-001 stampe
    MISSION.md    le sujet de DOR-001

## Ce qui est commité, et ce qui ne l’est pas

    golden-thread.json                commité      indique à quelle policy le projet est rattaché
    golden-thread-attestations.json   *voir ci-dessous*  ce qui nous a été déclaré, et par qui
    .golden-thread/                   ignoré       cache de policy et preuves enregistrées

La séparation dépend de ce qui peut être reconstruit. `verify` reproduit les
preuves et le manifest reproduit le cache ; `.golden-thread/` est donc jetable.
Une attestation est la seule chose que rien ne peut régénérer — la parole de
quelqu’un — et elle doit parvenir jusqu’au runner CI, qui signalerait autrement
comme non accepté un travail pourtant accepté.

**`golden-thread-attestations.json` est commité dans un vrai projet.** Il est
ignoré ici, et uniquement ici, parce qu’il s’agit d’une démonstration : son
contenu est produit par `demo/run-dod-demo.sh` à partir d’une mission que la démo
réécrit elle-même ; un snapshot commité deviendrait donc stale dès l’exécution
de la démo.

Le manifest contient une source *relative à ce répertoire*. C’est ce qui le
rend commitable : un chemin absolu est propre à une machine, et un manifest que
personne ne peut commiter ne pinne rien pour les autres.

La configuration corporate n’est jamais copiée dans ce projet.
