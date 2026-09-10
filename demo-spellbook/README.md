# Bienvenue à l’Académie d’Aurélis

**Votre mission : créer Frost Ward avec votre familier IA, puis apporter les
preuves permettant d’accepter le travail.**

## Démarrer

Le lab Docker vous place dans `/workspace/demo-spellbook`.
Si vous n’y êtes pas encore, suivez [le lancement Docker](../LAB.md).

Dans le lab :

```bash
claude
```

Puis copiez ce premier prompt :

> Réponds en français. Lis MISSION.md et fais une visite courte de src/spells/,
> tests/ et docs/ARCHITECTURE.md. Ne modifie rien et n’implémente pas encore.

## Suivre le parcours

Ouvrez le [guide participant](../GUIDE-PARTICIPANT.md), puis avancez avec
l’animateur : **voir le chemin → préparer la mission → décider et déléguer →
prouver la livraison → rejouer sans Claude**.

Chaque étape indique : **Pourquoi → Action → Ce que je dois observer**.
Les prompts se copient dans Claude ; les approbations se font par vous-même.

## Retrouver sa place

Dans le shell du lab :

```bash
golden-thread status
```

Pas encore de manifest ? Reprenez l’étape 1 du guide.
`NOT READY` ? Revenez aux décisions et à la DoR.
`OFF PATH` ou `STALE` ? Lisez l’exigence et sa raison avant de continuer.

## Les quatre repères

| Emplacement | À quoi il sert |
|---|---|
| `MISSION.md` | le contrat à clarifier puis accepter |
| `src/` et `tests/` | le sort et ses tests |
| `golden-thread.json` | la policy et le profil attachés |
| `golden-thread-attestations.json` | évaluations et décisions à conserver avec Git |

Les preuves calculées et le cache vivent dans `.golden-thread/` et sont
reconstructibles. Les attestations doivent voyager avec le projet jusqu’à la CI.

**L’agent prépare la décision ; l’humain prend la décision.**
