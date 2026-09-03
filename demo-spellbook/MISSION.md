# Mission: frost ward

## Problem

Academy casters have no protection spell that works against cold damage.
They currently improvise with `shield.cast()`, which draws on Air and does
nothing against cold, so the caster believes they are protected when they
are not.

## Outcome

A new `spells.protection.frost_ward` module exposing `cast(target: str) -> str`,
covered by a test.

## Notes

It should work with the existing wards where that makes sense. Ideally soon.
