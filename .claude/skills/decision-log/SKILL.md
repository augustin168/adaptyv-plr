---
name: decision-log
description: Use whenever a design or protocol decision is made or changed (by the human or the agent), when the human overrides an agent suggestion, when an assumption is adopted (e.g. channel count, deck position, liquid class), or when a verification reveals a limit or bug. Appends an entry to DECISIONS.md in the fixed format used for the end-of-day presentation.
---

# decision-log

Append (never rewrite history) to `DECISIONS.md` at the repo root. Newest entry at the bottom.
Get the time with `date "+%Y-%m-%d %H:%M"` (do not guess it).

## Entry format (exactly these fields)

```markdown
### YYYY-MM-DD HH:MM — <short title>
- **Decision:** what was decided, one or two sentences.
- **Alternatives:** what else was considered and why not.
- **Made by:** human | agent reviewed | agent unreviewed
- **Verified:** how (command, test name, file:line, observation). "not verified" if none.
- **NOT verified / limits:** what this does not prove; open TODO(confirm on machine) items.
```

## Rules
- **Made by**: `human` = the human decided; `agent reviewed` = agent proposed, human explicitly
  approved; `agent unreviewed` = agent decided, human has not reviewed yet. Never upgrade an entry
  to "reviewed" without the human saying so.
- **Human overrides**: when the human overrides an agent proposal, title it
  `HUMAN OVERRIDE: <topic>`, set Made by `human`, and put the agent's original proposal under
  Alternatives.
- Be concrete in Verified: name the test or command and its result. Simulation never verifies
  reach, collisions, liquid classes, or firmware behaviour; say so when relevant.
- Keep each entry under ~10 lines; it is read aloud in a presentation.
