---
description: Show the live harness state for this session - active gates (verification, oracle plan, syntax pending), read ledger strikes, recorded subagent leases, context usage, and recent harness failures.
allowed-tools: Bash(python3 *), Bash(ls *), Bash(cat *)
---

# /harness-status

Run and summarise (ADHD mode, <= 30 lines):

```bash
python3 - <<'EOF'
import json, os, glob, sqlite3, time
state = os.environ.get("CLAUDE_HARNESS_STATE_DIR") or os.path.expanduser("~/.cache/claude_harness")
sid = "${CLAUDE_SESSION_ID}"
d = os.path.join(state, "sessions", sid)
print("state dir:", d, "(exists)" if os.path.isdir(d) else "(missing)")
flags = sorted(os.listdir(os.path.join(d, "flags"))) if os.path.isdir(os.path.join(d, "flags")) else []
print("flags:", flags or "none")
for name in ("session_meta", "syntax_pending", "err_sig", "leases", "structured_feedback"):
    p = os.path.join(d, name + ".json")
    if os.path.isfile(p):
        print(name + ":", json.dumps(json.load(open(p)))[:400])
reads = os.path.join(d, "reads.json")
if os.path.isfile(reads):
    for f, e in json.load(open(reads)).items():
        if e.get("read_count", 0) >= 2 or len(e.get("file_slices", [])) >= 4:
            print("read budget:", os.path.basename(f), {k: e[k] for k in ("total_reads", "whole_reads", "read_count") if k in e}, "slices", len(e.get("file_slices", [])))
live = os.path.join(state, "live_state.json")
if os.path.isfile(live):
    print("context:", json.load(open(live)).get("used_percentage"), "%")
db = os.path.expanduser("~/.local/share/codex/projects/registry.sqlite")
if os.path.isfile(db):
    try:
        c = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
        for row in c.execute("SELECT failure_type, COUNT(*) FROM harness_failures WHERE conv_id = ? GROUP BY failure_type", (sid,)):
            print("failure:", row)
    except Exception as exc:
        print("failures: n/a", exc)
EOF
```

Then state which gates would currently block `Stop` and the single next action to clear them.
