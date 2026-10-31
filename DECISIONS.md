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
| 8 | Logistic regression as the initial model; default random forest as the comparison | Interpretable clinical standard; nonlinear comparison | Chinthaluri | Abburi — 2026-10-31, agreed |
| 9 | Tune with ROC-AUC scoring and grouped folds, not accuracy | The default forest reaches 88.7% accuracy while catching almost no readmissions | Chinthaluri | Abburi — 2026-10-31, agreed |
| 10 | Choose the final model on grouped CV only; keep logistic regression unless a challenger beats it by ≥ .005 AUC | The test set stays untouched until the final evaluation; a smaller gain does not justify losing readable coefficients. The random forest won by .009 and beat it in all three folds | Abburi | Chinthaluri — 2026-10-31, agreed; the rule was applied as written |
| 11 | Calibrate the final model (`CalibratedClassifierCV`, grouped folds); pick sigmoid vs. isotonic by out-of-fold Brier score | Class weighting inflated D1's mean predicted risk to .469 against a true rate of .114; a care team needs probabilities it can read at face value | Abburi | Chinthaluri — 2026-10-31, agreed; isotonic kept on out-of-fold Brier |
| 12 | Set flag thresholds from program capacity (top 5/10/20%) on out-of-fold training scores, not 0.5 and not the test set | Program capacity, not a fixed probability, limits how many patients can be followed up; reading thresholds off the test set would leak | Abburi | Chinthaluri — 2026-10-31, agreed; Sections 18–19 use these thresholds |
| 13 | Audit the final model at the 10% capacity threshold by race, gender, age (under 65 vs. 65+), and payer: ROC-AUC, flag rate, recall, precision, and mean predicted vs. observed risk, each with a patient-bootstrap 95% CI; omit groups with fewer than 30 readmissions | Equal recall means equal chance of help among patients who will be readmitted; group calibration checks that stated risks are right for everyone; small groups give unstable estimates | Chinthaluri | pending |
| 14 | Fix age as the mitigation target in advance; test separate thresholds for under 65 and 65+ chosen on out-of-fold training scores, with total capacity held at 10% | Deliverable 1 judged the age gap the most serious (the Medicare population); choosing thresholds on training data keeps the test set an honest check | Chinthaluri | pending |
| 15 | Cost scenario: break-even spending per contact = precision × 18% (pooled RR 0.82, 95% CI 0.73–0.91) × $15,200 per readmission, with the CI as the range | Published pooled trial effect (Leppin et al., 2014) and national average readmission cost (Weiss & Jiang, 2021); no local cost data | Chinthaluri | pending |

## Meetings

| Date | Attendees | Decisions / actions |
|---|---|---|
| 2026-10-31, in person | Chinthaluri, Abburi | First check-in (agenda in #6). Agreed: (1) Abburi re-runs the shared Colab notebook and posts his numbers against Tables 3 and 4 (#1), by October 31. (2) Abburi revises the Introduction and the Ethics section on his own branch (#3), by October 31; Chinthaluri reviews and merges it (#4). (3) Abburi reviews and merges the proofread fixes (#12), by October 31. (4) Deliverable 2 roles confirmed: Abburi leads model tuning and evaluation (#7); Chinthaluri leads the fairness audit and the cost and capacity analysis (#8). |
