# Mission : Frost Ward

## Problème

Les mages de l’Académie ne disposent d’aucun sort de protection contre les dégâts
du froid. Ils improvisent avec `shield.cast()`, qui utilise Air et ne protège pas
contre le froid : le mage se croit protégé alors qu’il ne l’est pas.

## Résultat attendu

Un nouveau module `spells.protection.frost_ward` exposant
`cast(target: str) -> str`, couvert par un test.

## Notes

Il devrait fonctionner avec les protections existantes lorsque cela a du sens.
Idéalement, assez vite.
