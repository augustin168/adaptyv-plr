---
paths:
  - "src/**/*.py"
  - "tests/**/*.py"
  - "scripts/**/*.py"
---

# PyLabRobot API rules (pylabrobot==1.0.0b1)

- **Import only via compat.** `from adaptyv_plr import compat` then `compat.LiquidHandler`, etc.
  Only `src/adaptyv_plr/compat.py` may `import pylabrobot...`. Need a new name? Verify it with the
  `plr-api-check` skill, add it to compat.py with its verified path in the docstring.
- **STAR lives under `pylabrobot.legacy.*`.** `pylabrobot.liquid_handling` is a deprecated shim.
- **Resources are indexed by well name and return lists.** `plate["A1"]` -> `[Well]`,
  `tip_rack["A1:A8"]` -> list of TipSpots. Pass these lists straight to `pick_up_tips`/`aspirate`
  (`vols=[...]` list too). For a single object use `plate.get_well("A1")` / `tip_rack.get_item("A1")`.
- **Everything touching the machine is async.** `await lh.setup()`, `await lh.aspirate(...)`,
  `await lh.stop()`. Static checks (preflight) are sync and must not call the backend.
- **Deprecations: use the replacement the warning names.** Examples verified in 1.0.0b1:
  `rails=` -> `track=`; `TIP_CAR_480(_A00)` -> `hamilton_tip_carrier_L5`;
  `PLT_CAR_L5AC_A00` -> `hamilton_plate_carrier_L5_ac`; `ChatterBoxBackend` -> `LiquidHandlerChatterboxBackend`.
  Never add a `filterwarnings("ignore")`.
- **Tracking is on.** Tip and volume tracking are enabled globally (`deck.enable_tracking`).
  Read volumes with `well.tracker.get_used_volume()`, tips with `tip_spot.tracker.has_tip`.
