# The denominator: what happened to 310 bug bounty reports

Bug bounty write-ups report the finding that worked. The denominator stays private, so a
newcomer who sees a 70% duplicate rate cannot tell whether they are bad at this or whether
they picked a crowded program. This is one researcher's denominator, with the script that
produced it.

Snapshot of 2026-10-24. No titles, no vulnerability details, no amounts: program, state,
dates, and whether a bounty was awarded.

## What the numbers say

### 1. Once a report is actually decided, duplicates are the norm everywhere

Same researcher, same method, same period. Duplicate rate among **decided** reports only,
for every program with at least five decided:

| Program | Decided | Duplicate rate |
|---|---|---|
| common_codes | 5 | **60.0%** |
| mozilla | 7 | 71.4% |
| mongodb | 71 | 71.8% |
| wordpress | 57 | 73.7% |
| nextcloud | 8 | 75.0% |
| vercel | 8 | 75.0% |
| zabbix | 10 | 90.0% |
| gitlab | 19 | 94.7% |
| elastic | 15 | **100.0%** |
| spotify | 5 | **100.0%** |

The floor is 60% and two programs are at 100%. On this method, which is reading source for
access-control bugs on popular open-source targets, being second to a finding is the normal
outcome and the program only decides how extreme it gets. A duplicate rate is therefore not
a measure of the researcher's skill, and anyone using their own as one is measuring crowding.

### 2. An undecided report flatters you, and that is a trap worth naming

78 of the 310 are still undecided: new, triaged, pending program review or editing. They
have not been judged, so counting them in the denominator makes every rate look better than
it is.

Measured both ways, the same corpus:

| Program | Duplicate rate over all reports | Over decided reports only |
|---|---|---|
| mongodb | 46.8% | **71.8%** |
| elastic | 88.2% | **100.0%** |
| nextcloud | 27.3% | **75.0%** |
| discourse | 0.0% | too few decided to report |

A 0% duplicate rate on discourse looked like the best result in the corpus. It was an
artefact: those reports were mostly still open. Any dashboard that divides by total
submissions rather than by decisions is reporting a number that improves simply by filing
more reports and waiting.

### 3. The median decided report is closed the same day it is filed

Median days to close: **0**, over 232 decided reports. The 90th percentile is 10 days, the
longest was 88.

Half of everything was decided within hours. That is the real tempo of a public program, and
it means a report is not a conversation. Whatever the triager needs in order to decide is
either on the first screen or it is not there at all.

### 4. Volume was anti-correlated with revenue

| Month | Submitted | Paid |
|---|---|---|
| 2026-07 | 7 | 3 |
| 2026-08 | 67 | 3 |
| 2026-09 | 114 | 2 |
| 2026-10 | 120 | **0** |

Seventeen times the volume produced zero bounties. Scaling the pipeline scaled the
duplicates, because it scaled the obvious. The report is not the product; the verdict is.

This is also the honest reading of the overall paid rate. Eight of 310 reports were paid,
which is 2.6%. Six of those eight are among the 232 decided reports and two are still
triaged, so the paid rate among decided reports is 2.6% as well. That number is a property
of a deliberately high-volume period rather than a hit rate on considered work: the three
months that produced six of the eight bounties were the three months with the lowest volume.
A pipeline optimised for submissions will produce a low paid rate by construction, whoever
is running it.

Two of the eight bounties arrived while the report was still `triaged` rather than
`resolved`, which is worth knowing if you are waiting for a state change before expecting
payment. On these programs the money can precede the fix.

### 5. When a program does pay, it pays quickly

Days from submission to bounty, all eight: **1, 1, 2, 7, 7, 11, 22, 50**. Median 7.

A report sitting untouched for a month is not usually on its way to a bounty. The slow ones
are mostly slow because nobody is going to pay for them.

## The data

| File | What it is |
|---|---|
| [`reports.csv`](reports.csv) | 310 rows, one per report: a hashed reference, program, state, whether the state is terminal, dates, days to close, whether a bounty was awarded and how long it took. |
| [`per-program.csv`](per-program.csv) | Aggregated by program over decided reports only. |
| [`summary.json`](summary.json) | All of the above as JSON, plus monthly submission counts. |

## What is withheld, and why

Report titles and raw identifiers are removed, because a title is a description of a
vulnerability and many of these reports are not closed.

Beyond that, **a report that is not in a terminal state carries no program name and no
dates**. A row reading "program X, state triaged, submitted on date Y" announces that a
confirmed and unfixed vulnerability exists at a named company on a known date. That is a
disclosure with or without a title attached. For the same reason the per-program aggregate
is computed over decided reports only, so it cannot be used to count anybody's open queue,
and three programs that appear in this corpus solely through undecided reports do not appear
in the output at all.

[`build.py`](build.py) asserts every one of those properties and refuses to write the files
if any of them fails. The assertion about programs seen only through open reports is there
because writing it is what revealed that three such programs existed.

## Method

Pulled from the HackerOne API, `/v1/hackers/me/reports`, paginated at 100 per page. One trap
worth recording: that endpoint does **not** populate the `bounties` relation, so summing
bounties from the report list returns zero for every report. Bounty facts have to come from
`/v1/hackers/payments/earnings` or from fetching each report individually. The first version
of this analysis nearly published "nothing ever paid" off that artefact.

```bash
python3 build.py path/to/h1-reports.json out/
```

## What this is not

One researcher, one period, mostly open-source programs, and a method weighted toward
access-control bugs found by reading source. It is a denominator, not a benchmark. If you
have your own, publish it: two denominators are worth considerably more than one.

## Licence

Data under CC0. Code under MIT.
