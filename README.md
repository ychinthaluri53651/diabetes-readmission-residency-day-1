# Predicting 30-Day Hospital Readmission for Patients With Diabetes

**Residency Project, Deliverable 1** · Python Application for Data Analytics in AI (PhDAI-733-M20)
University of the Cumberlands · October 31, 2026

**Presented to** Dr. Marwan Omar
**Presented by** Yogananda Atreya Chinthaluri (53651) and Anil Kumar Abburi (53405)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ychinthaluri53651/diabetes-readmission-residency-day-1/blob/main/Diabetes_Readmission_D1_Chinthaluri_Abburi.ipynb)

---

Dr. Omar, thank you for reviewing our project. This page summarizes what we built, what we
found, and how we worked as a team, and it links to each piece of evidence.

## Our project at a glance

| | |
|---|---|
| **Question** | Can routinely collected encounter data rank diabetic inpatients by 30-day readmission risk at discharge, well enough to target a care-transition program that can enroll only a fraction of patients? |
| **Why it matters** | Medicare's Hospital Readmissions Reduction Program penalizes hospitals for excess 30-day readmissions, and follow-up programs have limited capacity. |
| **Data** | 101,766 encounters for 71,518 patients at 130 U.S. hospitals, 1999–2008 (Clore et al., 2014); 99,340 encounters after cleaning, 11.4% readmitted within 30 days |
| **Initial model** | Logistic regression in a leakage-safe scikit-learn `Pipeline`, tested on patients it never saw in training |
| **Result** | Test ROC-AUC .661. The 10% of patients it ranks highest are readmitted at 2.1 times the average rate. |
| **Next** | Deliverable 2 tunes, calibrates, and audits this same model for fairness. |

## Where to find our work

| To review | Open |
|---|---|
| The report (APA 7th) | [`Diabetes_Readmission_Deliverable1_Chinthaluri_Abburi.docx`](Diabetes_Readmission_Deliverable1_Chinthaluri_Abburi.docx) |
| The code with every output | [`Diabetes_Readmission_D1_Chinthaluri_Abburi.ipynb`](Diabetes_Readmission_D1_Chinthaluri_Abburi.ipynb), or run it with the Colab badge above |
| Who led and reviewed each part | [`TEAM_TASKS.md`](TEAM_TASKS.md) |
| The decisions we made, and why | [`DECISIONS.md`](DECISIONS.md) |
| How we reviewed each other's work | [Pull requests](https://github.com/ychinthaluri53651/diabetes-readmission-residency-day-1/pulls?q=is%3Apr) |
| How we planned and tracked tasks | [Issues](https://github.com/ychinthaluri53651/diabetes-readmission-residency-day-1/issues?q=is%3Aissue) and [milestones](https://github.com/ychinthaluri53651/diabetes-readmission-residency-day-1/milestones?state=all) |

## Our team

| | Yogananda Atreya Chinthaluri | Anil Kumar Abburi |
|---|---|---|
| **Student ID** | 53651 | 53405 |
| **GitHub** | [@ychinthaluri53651](https://github.com/ychinthaluri53651) | [@Anil9618](https://github.com/Anil9618) |
| **Leads, Deliverable 1** | Data audit and cleaning · feature engineering · modeling · preliminary tuning | Introduction · ethical analysis · deployment scenario · Colab reproduction · APA proofread |
| **Leads, Deliverable 2** | Fairness audit and mitigation · cost and capacity analysis | Model tuning, boosting, and calibration · capacity-based thresholds · model explanation |

We share the work equally: each of us leads part of it and reviews the other's, and the
roles rotate between deliverables, so each of us leads the core modeling once. We write
the report together.

## What we found

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

## What comes next: Deliverable 2

- **Model tuning and evaluation** (led by Abburi): wider tuning grids, a gradient-boosting
  challenger, calibration (class weighting raised the mean predicted risk to .469 against a
  true rate of .114), and a threshold set by program capacity.
- **Fairness and impact in practice** (led by Chinthaluri): recall, flag rate, and calibration
  by race, gender, and age with confidence intervals; a mitigation test for the two gaps
  above; and a cost and capacity analysis for a deployment plan.

## Reproducing our results

**In Colab:** click the badge at the top and run Runtime → Run all. The notebook downloads
the UCI files itself. Because the repository is private, Colab first asks for permission to
read private GitHub repositories.

**Locally** (Python 3.14):

```bash
pip install -r requirements.txt
python3 build_notebook.py       # executes the notebook -> figures/*.png, outputs/results.json
python3 render_screenshots.py   # renders the tagged notebook cells -> figures/shot_*.png
python3 generate_report.py      # -> Diabetes_Readmission_Deliverable1_Chinthaluri_Abburi.docx
```

The executed notebook is our single source of truth: every figure is written to `figures/`
and every reported number to `outputs/results.json`, which the report reads. The report build
fails if a sentence is no longer supported by the results, a reference is never cited, or an
exhibit is never called out.

<details>
<summary><b>Repository layout</b></summary>

| Path | Purpose |
|---|---|
| `build_notebook.py` | Assembles and executes the notebook |
| `render_screenshots.py` | Draws the cells tagged `shot:<key>` (code plus real output) as report figures |
| `generate_report.py`, `report_common.py` | Build the APA report from `outputs/results.json` |
| `figures/`, `outputs/` | Generated figures and results |
| `TEAM_TASKS.md` | Who leads and reviews what in each deliverable |
| `DECISIONS.md` | Decision log and meeting notes |
| `Hints and Tips for Success.docx` | Course guidance the notebook follows |
| `data/` | UCI files, downloaded on first run (not tracked) |

</details>

<details>
<summary><b>How we followed the course "Hints and Tips for Success"</b></summary>

We followed every step visibly; the notebook header maps each hint to its section. Three
hints would introduce errors on this dataset, so we applied them in corrected form and
explain why in the notebook:

- **Forward fill** → missing values are handled column by column, because each row is a
  different patient.
- **Encoding and scaling before the split** → both are fit after the split, inside a
  `Pipeline`, so test-set statistics cannot leak into training.
- **`GridSearchCV` scored on accuracy** → scored on ROC-AUC with folds grouped by patient
  (see finding 2).

</details>

## Data

Clore, J., Cios, K., DeShazo, J., & Strack, B. (2014). *Diabetes 130-US hospitals for years
1999–2008* [Data set]. UCI Machine Learning Repository. <https://doi.org/10.24432/C5230J>
(CC BY 4.0). The full reference list is in the report.
