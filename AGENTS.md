# Instructions for coding agents working on Centerfuge

This file governs how any AI coding agent (Copilot or otherwise) should write
code, comments, docstrings, commit messages, and generated docs in this
repository. It applies repository-wide, including `headless_blender/`,
`experiments/`, `safety/`, `docs/`, and `simulations/`.

## Project-specific glossary (read this section first)

These terms are already load-bearing in this repository's own documents.
Anything below in "Core vocabulary" is the general framework; these are its
Centerfuge-specific instances, and comments should prefer the specific term
where one applies:

- **Physical ledger (`L_phys`) / Epistemic ledger (`L_epi`)** — see
  `docs/operating-model.md` §3 and `docs/safety-maintenance-spec.md` §2. The
  physical ledger is *Record* (what was observed); the epistemic ledger is
  the *Warrant* over it (what the observation justifies). Code must never let
  a physical event (a successful render, a passed test, a sensor reading)
  silently stand in for its epistemic interpretation.
- **Evidence status (V / M / S / D / Q)** — see `docs/operating-model.md`
  §10: Vision, Modeled, Simulated, Demonstrated, Qualified. Any claim of
  capability in a comment, docstring, or commit message should be tagged with
  one of these, explicitly, if it is not obviously Q. A rendered scene is at
  most S evidence for the geometry it depicts, never D or Q for a physical
  mechanism.
- **Hazard register / apparatus safety manifest** — see `safety/hazards.json`
  and `safety/schemas/apparatus-manifest.schema.json`. These are the
  Policy/Warrant pair for physical experiments: a manifest is only ever
  Admitted (`scripts/validate-safety.py --require-runnable`) if every
  applicable field has provenance and passes verification. Never hand-wave a
  missing manifest field as "reasonable default."
- **Render manifest / provenance record** — see
  `headless_blender/common.py`'s `write_manifest_entry` and
  `headless_blender/check_manifest.py`. This is the Record stage for
  generated visual artifacts: generator, git commit, parameters, and
  verification result, keyed by scene name. `check_manifest.py` performs the
  separate Admit decision from that record, without requiring Blender itself.
- **Non-occlusion invariant** — see `common.verify_visibility`. A scene
  claiming to be a "cutaway" or "interior view" is admissible only if its
  interior geometry is proven reachable by camera ray casts through a real
  opening, not merely because no opaque object happens to block the current
  camera angle.

If a future addition needs a new project-specific term, add it here with a
citation to the file/section that defines it, rather than inventing ad hoc
vocabulary in a comment.

## Part I — Why this document exists

A stub is not just missing code. A stub is any moment where a comment,
docstring, or explanation *names* a concept without *doing the work* of that
concept. Examples of stubs to avoid, even when the surrounding code is
complete:

- `// TODO: verify this is admissible` — names the concept, defers the check.
- `# handles the repair case` — names the case, doesn't say what repair means
  here, what triggers it, or what happens if it fails.
- `// ledger entry` — doesn't say what the entry records, who reads it, or
  what invariant it protects.

The standard: **a reader with no prior context on this specific function, but
who knows the vocabulary below, should be able to reconstruct the reasoning
from the comment alone** — not just what the code does, but why this is the
admissible way to do it, what would make it inadmissible, and what happens on
failure.

## Part II — Core vocabulary

Use these terms precisely and consistently. When code or comments use these
words, they must mean exactly this:

**Admissibility** — A candidate (value, action, edit, state transition) is
*admissible* if it satisfies the constraints declared for the context it's
entering — not "roughly correct," but checked against an explicit,
inspectable rule. An admissibility check must state the rule being checked.

**Record / Admit / Commit** — Three distinct stages, never collapsed:
- *Record*: an event or candidate is logged, unevaluated. Recording is not
  endorsement.
- *Admit*: the candidate has passed the relevant constraint check and is now
  eligible for use.
- *Commit*: the admitted candidate has been incorporated into the system's
  persistent state.
Never "commit" something that was never checked for admission; state which
stage a given operation performs.

**Repair** — An operation that restores admissibility after a violation:
- *Vertical repair*: fixing a single artifact against its own local
  constraints.
- *Horizontal repair*: reconciling divergent artifacts (replicas, branches,
  agents) against each other.
A repair function's docstring must say what it repairs, what makes repair
*fail* (not just succeed), and whether it is vertical or horizontal.

**Continuation** — The property that a system/artifact can proceed from its
current state without re-deriving or re-verifying from scratch. Code
implementing continuation must state what is preserved across the
discontinuity (restart, version bump, schema change) and what is explicitly
*not* preserved.

**History / Operative state / Memory** — Three distinct data categories:
- *History*: the immutable record of what happened.
- *Operative state*: the current, mutable working state derived from history
  plus committed decisions.
- *Memory*: the subset of history/operative state made available for future
  decisions.
Treating a mutable cache as if it were history is a stub-level error.

**Candidate / Warrant / Policy / Authority**:
- *Candidate*: a proposed value or action awaiting evaluation.
- *Warrant*: the specific justification making a candidate admissible under a
  policy.
- *Policy*: the declared rule-set a candidate is checked against.
- *Authority*: the entity/function permitted to grant admission under a
  policy.
Never grant admission without a warrant referencing the specific policy
clause it satisfies.

**Blend / Validation** — A *blend* is a conceptual or structural combination
of two prior structures; it is generative but not self-validating.
*Validation* is the separate, explicit step checking a blend's output against
constraints before it is admissible. Never let a blend's plausibility
substitute for validation.

**Decision / Rationale (σ / ρ)**:
- *Decision (σ)*: the admit/reject output of a check — safe to aggregate
  across independent seams.
- *Rationale (ρ)*: the reasoning behind a decision — merging rationales
  across independent seams risks manufacturing an unaudited admission point.
Never merge rationale strings from multiple sources into one justification
without flagging that the merge is itself a new, unverified claim.

**Sync / Justification** — *Sync* (e.g. distributed nodes agreeing)
certifies only that a shared policy was executed uniformly — not that the
output is true, coherent, or justified. Sync failure is diagnostic; sync
success is not evidence of correctness by itself.

**Non-collapse** (governing discipline) — No artifact should inherit the
epistemic or operational status of the process that produced it unless a
separately represented boundary explicitly grants that status. Don't let a
render, a log line, a merged summary, or a passing test silently promote
itself to "verified" — verification must be a distinct, visible act.

**Spherepop primitives** (where relevant): *Pop* (extraction of a determinate
value from an underdetermined state), *Refuse* (explicit rejection of an
inadmissible candidate, not silent failure), *Bind* (committing a
relationship between two admitted structures), *Collapse* (irreversible
reduction of possibility space — must be logged as irreversible, never
treated as a routine step).

## Part III — Anti-stub policy (enforceable rules)

1. No comment may name a concept from Part II without stating the specific
   rule, trigger, or failure condition that applies at that point in the
   code.
2. No function that performs record/admit/commit may leave any of the three
   stages implicit; if a function only records, its name and docstring must
   say so and must not imply admission or commitment occurred.
3. Every repair function must document its failure mode, not just its
   success path.
4. Every merge of rationale (ρ) across sources must be flagged as a new
   claim, with a comment identifying it as such.
5. No test, render, or log output may be described as "verified" unless a
   distinct verification step actually ran and its result is attached.
6. When in doubt about which vocabulary term applies, ask in-line via a
   comment (`// TODO: is this vertical or horizontal repair? — flagging for
   review`) rather than defaulting to generic language.
7. Docstrings must be written for a reader who knows this vocabulary but has
   zero context on the specific file.
8. When this repository's own vocabulary extends this document (as the
   project-specific glossary above does), add the new term to that glossary
   with a citation, rather than duplicating this file or inventing ad hoc
   terms elsewhere.

## Part IV — Self-check before submitting any change

- [ ] Does every use of a Part II (or project-glossary) term state the
      specific rule/trigger/condition, not just the term?
- [ ] Is it explicit which of record/admit/commit this code performs?
- [ ] If this is a repair function, is the failure path documented?
- [ ] If rationales are merged, is the merge flagged as a new claim?
- [ ] Could someone who knows the vocabulary but not this file reconstruct
      the reasoning from the comments alone?
- [ ] Is anything described as "verified" that hasn't actually passed a
      distinct, attached verification step?

If any box is unchecked, the explanation is a stub and must be filled in
before the change is considered complete.
