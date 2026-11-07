#!/usr/bin/env python3
"""Build the public dataset from a raw HackerOne report export.

Two things are stripped, for two different reasons.

Titles and raw report ids come out because a title is a description of a
vulnerability, and many of these reports are not closed.

The program name comes out of any row that is NOT in a terminal state. A row
saying "program X, state triaged, submitted on date Y" announces that a
confirmed, unfixed vulnerability exists at a named company on a known date.
That is a disclosure whether or not the title is attached, so the per program
aggregate is computed over closed reports only and cannot be used to count
somebody's open queue.
"""
import json, csv, pathlib, collections, datetime, hashlib, sys

SRC = pathlib.Path(sys.argv[1] if len(sys.argv) > 1
                   else "/root/hunt-2026-10-24/out/h1-reports.json")
OUT = pathlib.Path(sys.argv[2] if len(sys.argv) > 2
                   else "/root/gh-expand-2026-11-07/dataset")
OUT.mkdir(parents=True, exist_ok=True)

# A report in one of these states is finished: nothing about it is still live.
TERMINAL = {"resolved", "duplicate", "informative", "not-applicable", "spam"}
WITHHELD = "withheld"

rows = json.loads(SRC.read_text())
print("source records:", len(rows))

def day(s):
    return s[:10] if s else ""

def days_between(a, b):
    if not a or not b:
        return ""
    try:
        da = datetime.datetime.fromisoformat(a.replace("Z", "+00:00"))
        db = datetime.datetime.fromisoformat(b.replace("Z", "+00:00"))
        return (db - da).days
    except Exception:
        return ""

safe = []
for r in rows:
    state = r.get("state") or ""
    terminal = state in TERMINAL
    safe.append({
        "report_ref": hashlib.sha256(str(r["id"]).encode()).hexdigest()[:10],
        "program": (r.get("program") or "") if terminal else WITHHELD,
        "state": state,
        "terminal": "yes" if terminal else "no",
        "submitted": day(r.get("submitted_at")),
        "closed": day(r.get("closed_at")) if terminal else "",
        "days_to_close": days_between(r.get("submitted_at"), r.get("closed_at")) if terminal else "",
        "bounty_awarded": "yes" if r.get("bounty_awarded_at") else "no",
        "days_to_bounty": days_between(r.get("submitted_at"), r.get("bounty_awarded_at")),
        "swag": "yes" if r.get("swag_awarded_at") else "no",
    })

# ---------------------------------------------------------------- the gate
blob = json.dumps(safe)
assert "title" not in blob, "a title reached the output"
for r in rows:
    t = (r.get("title") or "").strip()
    if len(t) > 12:
        assert t not in blob, "a title string reached the output"
    assert str(r["id"]) not in blob or len(str(r["id"])) < 4, "a raw report id reached the output"
open_rows = [s for s in safe if s["terminal"] == "no"]
for s in open_rows:
    assert s["program"] == WITHHELD, "an open report kept its program name"
    assert s["closed"] == "" and s["days_to_close"] == "", "an open report kept a close date"
# A program that is present ONLY through open reports must not appear anywhere in
# the output at all, since any mention of it would itself be the disclosure.
open_only = {(r.get("program") or "") for r in rows if (r.get("state") or "") not in TERMINAL}
open_only -= {(r.get("program") or "") for r in rows if (r.get("state") or "") in TERMINAL}
open_only.discard("")
for name in sorted(open_only):
    assert name not in blob, "a program known only through an open report is named: %s" % name
# And no program may have its open count inferable: open rows carry no program at all.
assert {s["program"] for s in open_rows} == {WITHHELD}, "an open row named its program"
print("GATE PASS: %d open rows carry no program and no dates; no title or raw id present; "
      "%d programs seen only in open reports are absent from the output (%s)"
      % (len(open_rows), len(open_only), ", ".join(sorted(open_only)) or "none"))

with open(OUT / "reports.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(safe[0].keys()))
    w.writeheader(); w.writerows(safe)

# ------------------------------------------------------------ statistics
states = collections.Counter(s["state"] for s in safe)
print("\nSTATES")
for s, n in states.most_common():
    print("  %-26s %4d  %5.1f%%" % (s, n, 100 * n / len(safe)))

paid = [s for s in safe if s["bounty_awarded"] == "yes"]
print("\nbounty awarded: %d of %d = %.1f%%" % (len(paid), len(safe), 100 * len(paid) / len(safe)))

# closed reports only: an aggregate over open rows would leak the open queue
closed = [s for s in safe if s["terminal"] == "yes"]
per = collections.defaultdict(lambda: collections.Counter())
for s in closed:
    p = per[s["program"]]
    p["n"] += 1
    p[s["state"]] += 1
    if s["bounty_awarded"] == "yes":
        p["paid"] += 1

print("\nPER PROGRAM, closed reports only, n >= 5, by duplicate rate")
agg = []
for name, d in sorted(per.items(), key=lambda x: (100 * x[1]["duplicate"] / x[1]["n"])):
    if d["n"] < 5:
        continue
    dup = round(100 * d["duplicate"] / d["n"], 1)
    print("  %-16s closed %4d  paid %2d  dup %5.1f%%  info %5.1f%%"
          % (name, d["n"], d["paid"], dup, 100 * d["informative"] / d["n"]))
    agg.append({"program": name, "closed_reports": d["n"], "bounties": d["paid"],
                "duplicate_pct": dup,
                "informative_pct": round(100 * d["informative"] / d["n"], 1),
                "resolved": d["resolved"], "not_applicable": d["not-applicable"]})
with open(OUT / "per-program.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(agg[0].keys()))
    w.writeheader(); w.writerows(agg)

dtc = sorted(s["days_to_close"] for s in safe if isinstance(s["days_to_close"], int))
dtb = sorted(s["days_to_bounty"] for s in safe if isinstance(s["days_to_bounty"], int))
def med(x): return x[len(x) // 2] if x else None
print("\ndays to close:  n=%d median=%s p90=%s max=%s"
      % (len(dtc), med(dtc), dtc[int(len(dtc) * 0.9)] if dtc else None, max(dtc) if dtc else None))
print("days to bounty: n=%d median=%s values=%s" % (len(dtb), med(dtb), dtb))

by_month = collections.Counter(s["submitted"][:7] for s in safe if s["submitted"])
paid_month = collections.Counter(s["submitted"][:7] for s in paid if s["submitted"])
print("\nSUBMISSIONS BY MONTH vs bounties")
for m in sorted(by_month):
    print("  %s  %4d submitted  %d paid" % (m, by_month[m], paid_month.get(m, 0)))

json.dump({"snapshot": "2026-10-24", "total": len(safe), "closed": len(closed),
           "open": len(open_rows), "paid": len(paid), "states": dict(states),
           "per_program_closed_only": agg, "by_month": dict(by_month),
           "paid_by_month": dict(paid_month),
           "days_to_close": {"n": len(dtc), "median": med(dtc), "max": max(dtc) if dtc else None},
           "days_to_bounty": dtb},
          open(OUT / "summary.json", "w"), indent=1)
print("\nwrote", OUT)
