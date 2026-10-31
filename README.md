# Predicting 30-Day Hospital Readmission for Patients With Diabetes

**Residency Project, Deliverables 1 and 2** · Python Application for Data Analytics in AI (PhDAI-733-M20)
University of the Cumberlands · November 1, 2026

**Presented to** Dr. Marwan Omar
**Presented by** Yogananda Atreya Chinthaluri (53651) and Anil Kumar Abburi (53405)

Deliverable 2 notebook: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ychinthaluri53651/diabetes-readmission-residency-day-1/blob/main/Diabetes_Readmission_D2_Chinthaluri_Abburi.ipynb)
Deliverable 1 notebook: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ychinthaluri53651/diabetes-readmission-residency-day-1/blob/main/Diabetes_Readmission_D1_Chinthaluri_Abburi.ipynb)

---

Dr. Omar, thank you for reviewing our project. This page summarizes what we built, what we
found, and how we worked as a team, and it links to each piece of evidence.

## Our project at a glance

| | |
|---|---|
| **Question** | Can routinely collected encounter data rank diabetic inpatients by 30-day readmission risk at discharge, well enough to target a care-transition program that can enroll only a fraction of patients? |
| **Why it matters** | Medicare's Hospital Readmissions Reduction Program penalizes hospitals for excess 30-day readmissions, and follow-up programs have limited capacity. |
| **Data** | 101,766 encounters for 71,518 patients at 130 U.S. hospitals, 1999–2008 (Clore et al., 2014); 99,340 encounters after cleaning, 11.4% readmitted within 30 days |
| **Initial model (Deliverable 1)** | Class-weighted logistic regression in a leakage-safe scikit-learn `Pipeline`, tested on patients it never saw in training: ROC-AUC .661 |
| **Final model (Deliverable 2)** | Random forest chosen on patient-grouped cross-validation, then calibrated: ROC-AUC .668, Brier score .096 (from .229), so its predicted risks match observed rates |
| **Fairness** | Calibrated within every patient group, but patients 65 and older have fewer readmissions reached (recall .206 vs. .298) |
| **In practice** | At 10% capacity a care team reaches 26 of every 113 readmissions per 1,000 discharges (12 by random selection) and breaks even at about $670 per patient contacted |

## Where to find our work

| To review | Open |
|---|---|
| **Deliverable 2 report** (APA 7th) | [`Diabetes_Readmission_Deliverable2_Chinthaluri_Abburi.docx`](Diabetes_Readmission_Deliverable2_Chinthaluri_Abburi.docx) |
| **Deliverable 2 code** with every output | [`Diabetes_Readmission_D2_Chinthaluri_Abburi.ipynb`](Diabetes_Readmission_D2_Chinthaluri_Abburi.ipynb), or run it with the first Colab badge above |
| Deliverable 1 report and code | [`Diabetes_Readmission_Deliverable1_Chinthaluri_Abburi.docx`](Diabetes_Readmission_Deliverable1_Chinthaluri_Abburi.docx) and [`Diabetes_Readmission_D1_Chinthaluri_Abburi.ipynb`](Diabetes_Readmission_D1_Chinthaluri_Abburi.ipynb) |
| The decisions we made, and why | [`DECISIONS.md`](DECISIONS.md) |
| How we reviewed each other's work | [Pull requests](https://github.com/ychinthaluri53651/diabetes-readmission-residency-day-1/pulls?q=is%3Apr) |
| How we planned and tracked tasks | [Issues](https://github.com/ychinthaluri53651/diabetes-readmission-residency-day-1/issues?q=is%3Aissue) and [milestones](https://github.com/ychinthaluri53651/diabetes-readmission-residency-day-1/milestones?state=all) |

## Our team

| | Yogananda Atreya Chinthaluri | Anil Kumar Abburi |
|---|---|---|
| **Student ID** | 53651 | 53405 |
| **GitHub** | [@ychinthaluri53651](https://github.com/ychinthaluri53651) | [@Anil9618](https://github.com/Anil9618) |
| **Leads, Deliverable 1** | Data audit and cleaning · feature engineering · modeling · preliminary tuning | Introduction · ethical analysis · deployment scenario · Colab reproduction · APA proofread |
| **Leads, Deliverable 2** | Fairness audit and mitigation · cost and capacity analysis (notebook Sections 18–19) | Model tuning, boosting, and calibration · capacity-based thresholds · model explanation (Sections 15–17) |

We share the work equally: each of us leads part of it and reviews the other's, and the
roles rotate between deliverables, so each of us leads the core modeling once. We write
the report together.

## What we found in Deliverable 2

The Deliverable 2 notebook reproduces Deliverable 1 as Part 1 (Sections 1–14) and adds
Part 2 (Sections 15–20). Model choice, calibration, and thresholds were all set on the
training patients; the 24,757 test encounters were used once, for the final comparison.

| Measure (test set) | Initial model (D1) | Final model (D2) | Difference, 95% CI |
|---|---|---|---|
| ROC-AUC | .661 | **.668** | .002 to .012 |
| PR-AUC | .198 | **.213** | .008 to .022 |
| Brier score (lower is better) | .229 | **.096** | −.136 to −.130 |
| Mean predicted risk (observed .113) | .469 | **.114** | |
| Lift, top 10% | 2.08 | **2.21** | 0.01 to 0.24 |

1. **Wider tuning picked a random forest.** We searched 30 settings across logistic
   regression, a random forest, and a gradient-boosting challenger on patient-grouped folds.
   The forest won (cross-validated AUC .665, against .663 and .657) and cleared the margin
   we fixed in advance for giving up the interpretable model.
2. **Getting the probabilities right was the biggest gain.** The Brier score fell by more than
   half, so a predicted 20% now means about one patient in five. The ranking gain is real
   but modest, and the model now moves ahead of the prior-admissions rule at 10% capacity.
3. **Fairness: calibrated for everyone, uneven by age.** Predicted risk is within 0.7
   points of the observed rate in every large group. Patients 65 and older are ranked less
   well (AUC .641 vs. .715), and fewer of their readmissions are reached (recall .206 vs.
   .298). Age-specific thresholds close the gap, but mostly by reaching fewer younger
   patients, so we do not recommend them by default.
4. **In practice: one readmission reached per four contacts.** With the published trial
   effect (an 18% reduction) and the average readmission cost ($15,200), model-guided outreach
   breaks even at about $670 per patient contacted, against $308 for random selection.

## What we found in Deliverable 1

We held out 25% of patients as a test set (24,757 encounters); no patient appears in both
training and test. Cross-validation uses five folds grouped by patient.

| Model | CV ROC-AUC (mean ± SD) | Test ROC-AUC | Test PR-AUC | Recall | Lift, top 10% |
|---|---|---|---|---|---|
| **Logistic regression (our initial model)** | .656 ± .005 | **.661** | .198 | .573 | 2.08 |
| Random forest, default settings | .635 ± .008 | .635 | .187 | .001 | 2.04 |
| Prior-admissions heuristic | .608 ± .006 | .605 | .177 | .491 | 2.09 |
| Dummy (base rate) | .500 | .500 | .113 | .000 | 1.00 |

1. **The initial model works, modestly.** Logistic regression reaches a test ROC-AUC of
   .661 (95% patient-level bootstrap CI .650–.673). It beats a simple rule based on prior
   admissions by .048–.065 AUC and the default forest by .017–.034. In the top risk decile
   it only ties that rule.
2. **Accuracy is the wrong yardstick here.** The default forest's 88.7% accuracy matches a
   model that predicts "no readmission" for everyone, yet it catches only 0.1% of
   readmissions. We therefore tune on ROC-AUC.
3. **Preliminary tuning closes the gap.** A tuned forest (depth 10, 200 trees) reaches .665,
   against .662 for tuned logistic regression. The difference is not significant (95% CI
   −.001 to .008).
4. **Two fairness gaps need attention.** Women are flagged more often than men (38.8% vs.
   34.6%) at the same base rate, and the model ranks patients 65 and older less well (AUC
   .633 vs. .713).

## How we worked together

- **Planning.** Every task is a GitHub issue with one owner, grouped under a milestone for
  each deliverable.
- **Building.** Each task has its own branch, named `owner/short-task`.
- **Reviewing.** Nothing reaches `main` until the other member approves the pull request.
  `CODEOWNERS` requests that review automatically, and a template carries the review
  checklist.
- **Deciding.** Each methodological choice is logged in `DECISIONS.md` with who proposed
  it, who reviewed it, and when, along with notes from our check-ins.
- **Authorship.** Each of us commits under our own GitHub account, so the history shows who
  wrote and who reviewed each change.

## What we would do next

- **Add information the file lacks.** Discrimination near .67 is typical of models built
  from administrative data. Functional status, support at home, and scheduled follow-up are
  more likely than further tuning to improve it, especially for older patients.
- **Validate locally before use.** Recalibrate on recent data from the hospital that will
  use the model, and run it silently for a period before it guides outreach.
- **Measure the real effect.** Evaluate the program prospectively, rather than assuming the
  published average reduction.

## Reproducing our results

**In Colab:** click a badge at the top and run Runtime → Run all. The notebooks download
the UCI files themselves.

**Locally** (Python 3.14): run `pip install -r requirements.txt`, then run a notebook top
to bottom in Jupyter or VS Code.

Each notebook is the single source of truth for its report: running it writes every figure
(Deliverable 1 to `figures/`, Deliverable 2 to `figures/d2/`) and every reported number
(`outputs/results.json` and `outputs/results_d2.json`), and the report's tables and figures
come from that run.

<details>
<summary><b>Repository layout</b></summary>

| Path | Purpose |
|---|---|
| `Diabetes_Readmission_D2_Chinthaluri_Abburi.ipynb` | Deliverable 2 notebook, executed, with every output |
| `Diabetes_Readmission_Deliverable2_Chinthaluri_Abburi.docx` | Deliverable 2 report |
| `Diabetes_Readmission_D1_Chinthaluri_Abburi.ipynb` | Deliverable 1 notebook, executed, with every output |
| `Diabetes_Readmission_Deliverable1_Chinthaluri_Abburi.docx` | Deliverable 1 report |
| `figures/`, `figures/d2/` | Figures and notebook screenshots for each deliverable |
| `outputs/` | Results written by each notebook |
| `DECISIONS.md` | Decision log and meeting notes |
| `requirements.txt` | Package versions for a local run |
| `data/` | UCI files, downloaded on first run (not tracked) |

</details>

<details>
<summary><b>Safeguards against misleading results</b></summary>

- **No forward fill:** missing values are handled column by column, because each row is a
  different patient.
- **No leakage:** encoding and scaling are fit after the split, inside a `Pipeline`, so
  test-set statistics cannot leak into training.
- **No accuracy trap:** tuning is scored on ROC-AUC with folds grouped by patient (see
  Deliverable 1, finding 2).
- **No tuning on the test set:** the final model, its calibration, and its decision
  thresholds were all chosen on training patients, and the test set was used once.

</details>

## Data

Clore, J., Cios, K., DeShazo, J., & Strack, B. (2014). *Diabetes 130-US hospitals for years
1999–2008* [Data set]. UCI Machine Learning Repository. <https://doi.org/10.24432/C5230J>
(CC BY 4.0). The full reference lists are in the reports.
