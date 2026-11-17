---
name: plr-simulate
description: Use when asked to test, run, check, or demo the pipeline in simulation, after changing anything in src/, steps, deck, or scripts, or before claiming a protocol change "works". Runs pytest and the Chatterbox simulation (optionally with the browser Visualizer) and reports results together with the limits of simulation. Never runs live hardware.
---

# plr-simulate

## Steps
1. Tests: `.venv/bin/pytest -q`  (report pass/fail counts; paste failures verbatim).
2. Headless sim on both machines:
   - `.venv/bin/python scripts/run_demo.py --machine starlet`
   - `.venv/bin/python scripts/run_demo.py --machine star`
   - optional STAR command builder: add `--sim-backend star-chatterbox`
   Report the `RESULT ...` line of each run.
3. Optional Visualizer (when the user wants to watch, or to check the page serves):
   - Run in background: `.venv/bin/python scripts/run_demo.py --viz --no-browser --delay 2`
   - While running: `curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:1337/` (expect 200)
   - HTTP 200 only proves the page is served. Do not claim the deck rendered correctly unless
     you actually opened the page and looked at it.
4. Never add the live mode flag or the live env var. If the user wants hardware, tell them the
   command to run themselves.

## Report format
- Tests: N passed / N failed (+ failures)
- Sim runs: RESULT lines per machine
- Visualizer: HTTP status, and whether rendering was visually checked (usually: NOT checked)
- **Simulation does NOT check:** arm reach / deck boundaries, collisions between head and labware,
  liquid classes and real liquid behaviour (aspiration accuracy, foaming, LLD), firmware errors
  and timing, whether the demo/lab deck matches the physical deck, real channel count. A green sim
  run means the bookkeeping (tips, volumes, ordering) is consistent, nothing more.
