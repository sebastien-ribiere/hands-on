# Architecture du grimoire

## Organisation

| Couche | Modules actuels | Rôle |
|---|---|---|
| `spells.elements` | `air`, `water`, `fire` | éléments de base |
| `spells.protection` | `shield`, `ward` | sorts défensifs |
| `spells.offense` | `flame_lance` | sorts offensifs |

Les éléments ne connaissent pas les sorts. Les sorts utilisent les éléments.
Deux sorts qui ont besoin d’un comportement commun le placent dans un élément,
plutôt que de dépendre l’un de l’autre.

## Dépendances autorisées dans les protections

Les protections peuvent utiliser **Air** et **Water**. Elles ne peuvent pas
utiliser **Fire**.

C’est la règle `ARCH-001` du Golden Thread de l’Académie. Le contrôle analyse
le graphe d’import Python, imports relatifs compris. Il porte sur le couplage :
une évolution de Fire pour les besoins offensifs ne doit pas imposer une
modification des protections.

`spells.offense.flame_lance` utilise Fire et reste conforme : la règle concerne
la couche de protection.

| Dépendance | Verdict |
|---|---|
| `shield.py` vers `spells.elements.air` | autorisée |
| `ward.py` vers `spells.elements.water` | autorisée |
| protection vers `spells.elements.fire` | interdite |

L’atelier introduit temporairement la dernière dépendance pour observer un
écart réel au chemin supporté, puis sa correction.

## Le stamp

La ligne ci-dessous indique le digest du code décrit. Elle enregistre qu’une
personne a estampillé ce document pour cette version exacte de `src/`.
Elle ne certifie ni une relecture ni la justesse du texte. Si le code change
sans mise à jour du stamp, `DOC-001` le signale.

<!-- golden-thread: describes src/ sha256:cdd324e7312cfc431f54ceab27885cd2ffc053e6e9469f7e3a87b3f428e5ef61 -->
