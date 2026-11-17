---
name: plr-api-check
description: Use BEFORE writing or changing any code that uses a PyLabRobot class, function, module path, or keyword argument (new import in compat.py, a new LiquidHandler call, a new kwarg, a resource/carrier/deck name), and whenever a DeprecationWarning or AttributeError mentions pylabrobot. Verifies the name against the INSTALLED pylabrobot==1.0.0b1, not docs or memory.
---

# plr-api-check

Your training data is older than pylabrobot 1.0.0b1. The installed package is the source of truth;
docs (https://docs.pylabrobot.org/stable/) come second; memory comes last and is never enough.

## Steps
1. Confirm the installed version:
   `.venv/bin/python -c "import pylabrobot; print(pylabrobot.__version__, pylabrobot.__file__)"`
   Expect `1.0.0b1`. If not, stop and report.
2. Confirm the name exists and import is warning-free:
   `.venv/bin/python -W error::DeprecationWarning -c "from <module> import <Name>; print(<Name>)"`
   - STAR / liquid-handling names come from `pylabrobot.legacy.liquid_handling[...]`.
3. Confirm the signature / kwargs:
   `.venv/bin/python -c "import inspect; from <module> import <Name>; print(inspect.signature(<Name>))"`
   For methods: `inspect.signature(LiquidHandler.aspirate)`. For a kwarg, it must appear here.
4. Check for deprecation paths in the source if in doubt:
   `grep -rn "deprecated" .venv/lib/python3*/site-packages/pylabrobot/<area> | head`
   Calling with the candidate args under `-W error::DeprecationWarning` must not raise.
5. Find alternatives when a name is missing: `dir(module)`, filtered, e.g.
   `.venv/bin/python -c "import pylabrobot.resources as r; print([n for n in dir(r) if 'carrier' in n.lower()])"`

## Output
Report: the exact import path, the signature you saw, whether it warned, and the replacement if it
was deprecated. If it is a new name, add it to `src/adaptyv_plr/compat.py` (only there) with its
verified path in the module docstring. If docs and the installed package disagree, the installed
package wins; say so explicitly.
