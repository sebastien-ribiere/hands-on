# Mission: frost ward

## Problem

Academy casters have no protection spell that works against cold damage.
Today they improvise with `shield.cast()`, which draws on Air and does
nothing against cold, so the caster believes they are protected when they
are not. Two apprentice injuries last term came from exactly this.

## Outcome

A new `spells.protection.frost_ward` module exposing `cast(target: str) -> str`.

Done when:

- `frost_ward.cast()` returns a warded target, and is covered by a test;
- `golden-thread verify` reports ARCH-001 as PASS on the resulting code;
- the existing `shield` and `ward` spells are unchanged.

## Scope

In scope: the frost ward module and its test.

Out of scope: retiring the misuse of `shield` for cold (a separate mission),
any change to the elements package, and any spell balancing.

## Constraints

- The academy-spells-ready profile enforces ARCH-001: a protection spell must
  not depend on Fire. A frost ward draws on Water only, which ARCH-001 already
  allows, so this mission does not require a policy change.
- Python 3.11, standard library only, consistent with the rest of `src/`.

## Decisions taken

Two questions were raised by the readiness assessment and answered by the
mission owner:

1. **Which element does a frost ward draw from?** Water. Air was considered
   and rejected: the chill effect belongs with Water in the Academy's
   existing taxonomy, and Water is already an allowed dependency for the
   protection layer.
2. **Must it interoperate with the existing wards?** No. `frost_ward` stands
   alone for this mission; a combined ward is deliberately out of scope.

## Open unknowns

- The exact wording of the returned string is not fixed. The implementer
  chooses it; no caller depends on it yet.

No blockers.
