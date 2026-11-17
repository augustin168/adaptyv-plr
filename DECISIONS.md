# Decision log

Format: see `.claude/skills/decision-log/SKILL.md`. Newest at the bottom.
(Setup entries of 2026-11-17 were written in one batch at 20:24; their times are approximate.)

### 2026-11-17 20:05 — Environment scope and plan approved
- **Decision:** Build only the environment (config, guardrails, sim + test harness); no lab task. Package name `adaptyv_plr`, src layout.
- **Alternatives:** Implementing a first protocol now (rejected: out of scope).
- **Made by:** human (plan approved in plan mode)
- **Verified:** n/a
- **NOT verified / limits:** —

### 2026-11-17 20:12 — Python 3.12 venv; PLR names verified against installed 1.0.0b1
- **Decision:** venv on `python3.12` (system `python3` is 3.9.6, below the >=3.10 requirement). All PLR names in `compat.py` taken from the installed package.
- **Alternatives:** python3.11 (also available; 3.12 chosen as newest installed).
- **Made by:** agent unreviewed
- **Verified:** `inspect.signature` / `dir()` on each name; imports and a full sim transfer ran under `warnings.simplefilter("error", DeprecationWarning)` without error.
- **NOT verified / limits:** Only names we use were checked; docs site not cross-checked line by line.

### 2026-11-17 20:14 — Deprecated names found and replaced
- **Decision:** Use `pylabrobot.legacy.liquid_handling` (not `pylabrobot.liquid_handling`, a warning shim); `track=` (not `rails=`); `hamilton_tip_carrier_L5` (not `TIP_CAR_480(_A00)`); `hamilton_plate_carrier_L5_ac` (not `PLT_CAR_L5AC_A00`); `LiquidHandlerChatterboxBackend` (`ChatterBoxBackend` raises NotImplementedError).
- **Alternatives:** Old names (they still work but warn, or raise).
- **Made by:** agent unreviewed
- **Verified:** Read the warning text in the installed source (tip_carriers.py, plate_carriers.py, hamilton_decks.py, liquid_handling/__init__.py).
- **NOT verified / limits:** Other deprecated names may exist in parts of PLR we don't use yet.

### 2026-11-17 20:16 — Default sim backend: generic Chatterbox; STAR Chatterbox optional
- **Decision:** Default `LiquidHandlerChatterboxBackend(num_channels=...)`. Optional `--sim-backend star-chatterbox` uses `STARChatterboxBackend`, which also builds STAR firmware commands (no I/O). Tests run both.
- **Alternatives:** STAR Chatterbox as default (closer to STAR, but subclasses the STAR hardware backend and is less familiar; kept opt-in).
- **Made by:** agent unreviewed
- **Verified:** tests/test_sim_transfer.py parametrized over both backends × both machines.
- **NOT verified / limits:** Neither checks reach, collisions, liquid classes, or firmware error responses.

### 2026-11-17 20:16 — Channel counts and demo deck positions are placeholders
- **Decision:** STAR = 16, STARlet = 8 channels; demo tip carrier track 1, plate carrier track 7.
- **Alternatives:** None without machine access.
- **Made by:** agent unreviewed
- **Verified:** Track counts (54 / 30) read from installed `STARDeck` / `STARLetDeck`.
- **NOT verified / limits:** TODO(confirm on machine): our instrument's channel count; real layout must come from the lab layout file (`--deck`).

### 2026-11-17 20:18 — Preflight before setup; tips discarded to trash in the placeholder step
- **Decision:** `Pipeline.run` preflights all steps (with a ledger so later steps see earlier ones) before `lh.setup()`, because setup homes a real STAR. Placeholder transfer discards tips (no return-and-reuse).
- **Alternatives:** Preflight after setup (rejected: setup is motion). Return tips to rack (rejected: invites reuse).
- **Made by:** agent unreviewed
- **Verified:** tests/test_preflight.py asserts no setup/backend call on overdraw, cumulative overdraw, tip reuse, channel out of range.
- **NOT verified / limits:** Preflight is bookkeeping only; it does not know physical geometry.

### 2026-11-17 20:20 — PLR bug: core grippers lost on layout save/load
- **Decision:** Round-trip test compares everything except `core_grippers*`; a strict xfail test documents the loss and will fail once PLR fixes it.
- **Alternatives:** Patching PLR (rejected: no edits to the pinned package).
- **Made by:** agent unreviewed
- **Verified:** `Deck.save` writes `core_grippers`; `Deck.load_from_json_file` returns a deck without them (tests/test_layout.py).
- **NOT verified / limits:** Impact on gripper use with a loaded layout not explored. Worth reporting upstream.

### 2026-11-17 20:21 — Deprecation enforcement: pytest filter + conftest stack guard
- **Decision:** `error::DeprecationWarning:adaptyv_plr.*` in pytest config, plus `tests/conftest.py` raising any DeprecationWarning whose call stack passes through `src/adaptyv_plr` (covers warnings attributed to a PLR frame deeper in a chain our code started).
- **Alternatives:** Global `error::DeprecationWarning` (would also fail on PLR-internal warnings not caused by us).
- **Made by:** agent unreviewed
- **Verified:** Injected `rails=` in deck.py -> 16 tests fail; injected `from pylabrobot.liquid_handling import LiquidHandler` in compat.py -> collection errors; both name our file:line. Correction: I first assumed the import shim needed the conftest guard; with `--noconftest` the pyproject filter alone caught it (Python skips importlib frames for stacklevel).
- **NOT verified / limits:** Warnings emitted from C code bypass `warnings.warn` patching (none seen).

### 2026-11-17 20:22 — Hook strictness: block the constructor call in any file, docs included
- **Decision:** Guard blocks any Edit/Write adding the STAR hardware backend constructor call outside `src/adaptyv_plr/backends.py`, including Markdown. Hook fails closed on bad input. Matcher also covers MultiEdit.
- **Alternatives:** Only `.py` files (fewer false positives, but notebooks/heredoc scripts slip through).
- **Made by:** agent unreviewed
- **Verified:** tests/test_guard_hook.py (11 block, 9 allow cases). Live in this session: it blocked my own first CLAUDE.md draft, which quoted the call literally.
- **NOT verified / limits:** Hook only sees Claude's tool calls. Not tested on Windows (stdlib-only script; launcher uses POSIX `command -v`, needs Git Bash). If no python is on PATH the launcher fails and Claude Code treats that as non-blocking.

### 2026-11-17 20:28 — Hook gap closed: live flag passed as an argv list
- **Decision:** Guard regex also matches the live flag written as a Python argv list (`"--mode", "live"`), e.g. in `python -c` or subprocess calls.
- **Alternatives:** Leave it (rejected: if the operator's shell already exported the live env var, Claude inherits it, so the flag check is the remaining barrier).
- **Made by:** agent unreviewed
- **Verified:** New block case in tests/test_guard_hook.py (21 hook tests pass). The hook also blocked my own Bash heredoc that wrote this log entry because the text quoted the flag; entries are now written with the Edit tool.
- **NOT verified / limits:** Regexes cannot catch every obfuscation (variables, encoding, a script file that builds the args). Human review + protocol-reviewer remain the backstop.

### 2026-11-17 20:28 — Environment acceptance run
- **Decision:** Environment accepted for simulation work; no live hardware path was executed.
- **Alternatives:** —
- **Made by:** agent unreviewed
- **Verified:** Fresh venv + `pip install -e ".[dev]"` + `pytest -q` -> 42 passed, 1 xfailed. Headless demo exit 0 on star (16 ch) and starlet (8 ch). `--viz --no-browser --delay 2`: curl -> HTTP 200 during the run. Live path raises LiveModeNotAllowed; the hook blocked my live-flag and env-var commands in this session. Injected deprecated names make tests fail. grep: only compat.py imports pylabrobot.
- **NOT verified / limits:** Visualizer rendering in a browser not looked at. Hook not run on Windows. Nothing checked against the physical STAR (reach, collisions, liquid classes, firmware, channel count, deck layout).
