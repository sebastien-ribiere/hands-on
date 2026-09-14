# Mission : Frost Ward

## Problème

Les mages de l’Académie ne disposent d’aucun sort de protection contre les dégâts
du froid. Ils improvisent avec `shield.cast()`, qui utilise Air et ne protège pas
contre le froid : le mage se croit protégé alors qu’il ne l’est pas.
Dans le scénario, deux apprentis se sont ainsi blessés au trimestre précédent.

## Résultat attendu

Un nouveau module `spells.protection.frost_ward` exposant `cast(target: str) -> str`.

La mission est terminée lorsque :

- `frost_ward.cast(target)` renvoie un texte représentant la cible protégée, avec un test associé ;
- `golden-thread verify` rapporte `ARCH-001 PASS` sur le code obtenu ;
- les sorts existants `shield` et `ward` restent inchangés.

## Périmètre

Inclus : le module Frost Ward et son test.

Exclus : supprimer les usages inadaptés de `shield` contre le froid (autre mission),
modifier le package `elements` ou équilibrer les sorts.

## Contraintes

- Le profil `academy-spells-ready` impose `ARCH-001` : une protection ne doit pas
  dépendre de Fire. Frost Ward utilise uniquement Water, déjà autorisé ; aucune
  modification de policy n’est nécessaire.
- Python 3.11 ou supérieur, bibliothèque standard uniquement dans `src/`,
  conformément au projet. Le lab s’exécute avec Python 3.12.

## Décisions prises

Le propriétaire de mission a répondu aux deux questions de readiness :

1. **Quel élément utilise Frost Ward ?** Water. Air a été envisagé puis écarté :
   pour cette mission, le froid relève de Water dans la taxonomie de l’Académie.
   Cold n’est pas un nouvel élément. Water est déjà autorisé dans les protections.
2. **Doit-il interagir avec les protections existantes ?** Non. Frost Ward est
   autonome ; une protection combinée est explicitement hors périmètre.

## Inconnues ouvertes

La formulation exacte du texte renvoyé est laissée à l’implémentation et sera
illustrée par un test. Aucun appelant n’en dépend encore.

Aucun blocker.
