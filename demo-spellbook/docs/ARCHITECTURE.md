# Spellbook architecture

How the spells are arranged, and why the arrangement is what it is.

## Layers

    spells.elements     air, water, fire      the raw elements
    spells.protection   shield, ward          defensive spells
    spells.offense      flame_lance           offensive spells

Elements know nothing about spells. Spells draw on elements. Nothing draws on
another spell: two spells that need the same behaviour push it down into an
element rather than reaching sideways.

## What protection may draw on

Protection spells may use **Air** and **Water**. They may not use **Fire**.

This is ARCH-001 in the Academy's Golden Thread, and it is not a naming rule:
it is checked against the real import graph, relative imports included. The
reason is coupling rather than taste. Fire changes for offensive reasons — a
new damage type, a rebalanced heat curve — and a ward that reaches into it gets
dragged along with every one of those changes, for no defensive benefit.

`spells.offense.flame_lance` depends on Fire and is entirely compliant. The
rule binds the protection layer, not the word.

## Where the boundary actually is

    shield.py   -> spells.elements.air      allowed
    ward.py     -> spells.elements.water    allowed
    ward.py     -> spells.elements.fire     denied, and this is the one that bites

The third line is the interesting case, and it is the deviation the hands-on
introduces on purpose: a caster asks for a ward that also burns what it stops,
and the shortest way to write it is the one the golden path forbids.

## The stamp below

This document carries the digest of the code it describes. It is not a
signature and it is not a review: it records that somebody re-stamped this
document against this exact version of `src/`. If the code moves and this line
does not, DOC-001 says so.

<!-- golden-thread: describes src/ sha256:cdd324e7312cfc431f54ceab27885cd2ffc053e6e9469f7e3a87b3f428e5ef61 -->
