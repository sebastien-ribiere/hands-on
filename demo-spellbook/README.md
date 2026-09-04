# demo-spellbook

A consumer project attached to the Golden Thread.

    src/spells/
      elements/   air, water, fire
      protection/ shield, ward     <- bound by ARCH-001
      offense/    flame_lance      <- may use fire freely
    tests/        what TEST-001 runs
    docs/         what DOC-001 stamps
    MISSION.md    what DOR-001 is about

## What is committed, and what is not

    golden-thread.json                committed   which policy this project is on
    golden-thread-attestations.json   *see below*  what we were told, and by whom
    .golden-thread/                   ignored     policy cache and recorded evidence

The split is by what can be rebuilt. `verify` reproduces the evidence and the
manifest reproduces the cache, so `.golden-thread/` is disposable. An
attestation is the one thing nothing can regenerate -- somebody's word -- and
it has to reach a CI runner that would otherwise report agreed work as
un-agreed.

**`golden-thread-attestations.json` is committed in a real project.** It is
ignored here, and only here, because this is a demonstration: its contents are
produced by `demo/run-dod-demo.sh` against a mission the demo itself rewrites,
so a committed snapshot would be stale the moment the demo ran.

The manifest carries a source *relative to this directory*, which is what makes
it committable at all -- an absolute path is specific to one machine, and a
manifest nobody can commit pins nothing for anybody else.

The corporate configuration is never copied into this project.
