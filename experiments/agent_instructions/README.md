# experiments/agent_instructions (ISOLATED)

Possible side project: turn a technician's free-text instructions ("transfer 50 µL from the
source plate A1 to dest plate A1") into a structured protocol (a list of pipeline steps) for review.

## Status
README only. No code yet.

## Isolation rules
- Nothing in `src/` may import from this folder (enforced by `tests/test_isolation.py`).
- Output of anything built here is a *proposal* (e.g. JSON step list) that a human reviews and
  that must pass `Pipeline.preflight` and the `protocol-reviewer` subagent before it is used.
- It never talks to hardware, never sets the live env var, and never invents deck positions:
  unknown positions stay unresolved and are flagged, not guessed.
- No new dependencies without asking (project rule: pylabrobot + pytest only).

## Open questions (to decide with the human)
- Input format from technicians (free text, form, spreadsheet?).
- Output format: JSON matching `SingleChannelTransfer` fields, or a richer step schema?
- How ambiguous instructions are surfaced back to the technician.
