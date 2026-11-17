# PyLabRobot env for a Hamilton STAR / STARlet (sim-first)

This file is advisory. Enforcement lives in `.claude/hooks/guard_plr.py` (PreToolUse) and the tests.

## Version pin
- `pylabrobot==1.0.0b1`, Python >= 3.10 (use `python3.12`; system `python3` here is 3.9).
- Your training data predates this version. STAR support lives under `pylabrobot.legacy.*`.
  Never guess a PLR name: verify with the `plr-api-check` skill. Installed package beats docs.

## Commands
- Setup: `python3.12 -m venv .venv && .venv/bin/pip install -e ".[dev]"`
- Tests: `.venv/bin/pytest -q`
- Sim demo: `.venv/bin/python scripts/run_demo.py [--machine star|starlet] [--sim-backend star-chatterbox]`
- Watch it: `.venv/bin/python scripts/run_demo.py --viz --delay 2` (http://127.0.0.1:1337/)
- Layout: `--save-layout layouts/x.json`, reuse with `--deck layouts/x.json`
- Check a name: `.venv/bin/python -W error::DeprecationWarning -c "from pylabrobot.X import Y"`

## Hard rules
1. Never run live mode, never set the live env var, never pass the live mode flag. The human does that. (hook-enforced)
2. The STAR hardware backend is constructed only in `src/adaptyv_plr/backends.py`, behind the gate.
   (hook-enforced: any edit adding that constructor call elsewhere, even in docs, is blocked)
3. Only `src/adaptyv_plr/compat.py` imports `pylabrobot`. (test-enforced: tests/test_isolation.py)
4. Never silence a DeprecationWarning; switch to the replacement it names. (pytest + conftest enforce)
5. No automatic error recovery that moves the robot. Fail, stop, report.
6. No invented deck positions: lab layout file or human instruction only, else a named
   constant marked `TODO(confirm on machine)`.
7. Units in names: `volume_ul`, `z_mm`, `flow_rate_ul_s`.
8. Nothing in `src/` imports from `experiments/`.
9. No new dependencies beyond pylabrobot and pytest without asking.

## Working style
- Simulation first. Report what simulation does NOT check (reach, collisions, liquid classes,
  firmware errors, real coordinates) every time you report a sim result.
- Every step gets a static `preflight` (no motion) before `run`; Pipeline preflights all steps
  before `lh.setup()`.
- Log decisions in `DECISIONS.md` with the `decision-log` skill (incl. human overrides).
- Before handing over protocol code, run the `protocol-reviewer` subagent.
- Say what you verified and how; say plainly what you did not verify.

## Layout
- `src/adaptyv_plr/` compat (PLR imports), config, backends (factory + live gate), deck (demo
  deck, layout JSON), viz (Visualizer), pipeline (preflight/run), steps (PLACEHOLDER transfer)
- `scripts/run_demo.py` CLI · `tests/` sim tests + hook tests · `layouts/` saved decks (gitignored)
- `experiments/agent_instructions/` isolated side project (README only)
- `.claude/` hooks, rules, skills, agents · `DECISIONS.md` running log
