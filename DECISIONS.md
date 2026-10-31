# Decision Log — Residency Project (PhDAI-733-M20)

Each methodological choice is recorded with who proposed it and who reviewed it. A reviewer
signs off by replacing `pending` with the date and a short note.

| # | Decision | Rationale | Proposed by | Reviewed by |
|---|---|---|---|---|
| 1 | Dataset: UCI Diabetes 130-US hospitals; target is readmission within 30 days | Real-world penalty context (HRRP), adequate size, protected attributes available for a fairness audit | Chinthaluri | Abburi — 2026-10-31, agreed |
| 2 | Exclude deaths and hospice discharges | Readmission is impossible for these patients | Chinthaluri | Abburi — 2026-10-31, agreed |
| 3 | No forward fill; handle missing values per column | Rows are different patients; forward fill would copy values between them | Chinthaluri | Abburi — 2026-10-31, agreed |
| 4 | Keep `None` as a "Not measured" category | pandas would otherwise treat a clinically meaningful value as missing | Chinthaluri | Abburi — 2026-10-31, agreed |
| 5 | Split 75/25 **grouped by patient** | 46% of encounters belong to repeat patients; the aim is to estimate performance on new patients | Chinthaluri | Abburi — 2026-10-31, agreed |
| 6 | Encode and scale after the split, inside a `Pipeline` | Fitting them on all rows leaks test-set statistics into training | Chinthaluri | Abburi — 2026-10-31, agreed |
| 7 | Race, gender, and payer excluded as predictors; kept for the audit | Proxy-bias risk; fairness is judged on outcomes by group | Chinthaluri | Abburi — 2026-10-31, agreed |
| 8 | Logistic regression as the initial model; default random forest as the comparison | Interpretable clinical standard; nonlinear comparison per the course hints | Chinthaluri | Abburi — 2026-10-31, agreed |
| 9 | Tune with ROC-AUC scoring and grouped folds, not accuracy | The default forest reaches 88.7% accuracy while catching almost no readmissions | Chinthaluri | Abburi — 2026-10-31, agreed |

## Meetings

| Date | Attendees | Decisions / actions |
|---|---|---|
| 2026-10-31, in person | Chinthaluri, Abburi | First check-in (agenda in #6). Agreed: (1) Abburi re-runs the shared Colab notebook and posts his numbers against Tables 3 and 4 (#1), by October 31. (2) Abburi revises the Introduction and the Ethics and Real-World section on his own branch (#3), by October 31; Chinthaluri reviews and merges it (#4). (3) Abburi reviews and merges the proofread fixes (#12), by October 31. (4) Deliverable 2 roles confirmed: Abburi leads optimization and evaluation (#7); Chinthaluri leads the fairness audit and real-world analysis (#8). |
