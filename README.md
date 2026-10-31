# Predicting 30-Day Hospital Readmission for Patients With Diabetes

**Residency Project** · Python Application for Data Analytics in AI (PhDAI-733-M20)
University of the Cumberlands · Instructor: Dr. Marwan Omar

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ychinthaluri53651/diabetes-readmission-residency-day-1/blob/main/Diabetes_Readmission_D1_Chinthaluri_Abburi.ipynb)

## Team

| | Yogananda Atreya Chinthaluri | Anil Kumar Abburi |
|---|---|---|
| **Student ID** | 53651 | 53405 |
| **GitHub** | [@ychinthaluri53651](https://github.com/ychinthaluri53651) | [@Anil9618](https://github.com/Anil9618) |
| **Leads, Deliverable 1** | Dataset exploration · model development · preliminary tuning | Problem definition · ethics and impact · real-world application · Colab reproduction |
| **Leads, Deliverable 2** | Ethics and fairness audit · real-world cost and capacity analysis | Optimization and evaluation · problem-definition update · model explanation |

Each of us leads three rubric criteria and reviews the other's three. The roles rotate
between deliverables, so each of us leads the core modeling once. Teamwork, documentation,
and writing are shared. The full split is in [TEAM_TASKS.md](TEAM_TASKS.md).

## The problem

Under Medicare's Hospital Readmissions Reduction Program, hospitals are penalized for excess
30-day readmissions, and care-transition programs can enroll only a fraction of discharges.
We ask whether routinely collected encounter data can rank diabetic inpatients by 30-day
readmission risk at discharge, well enough to target such a capacity-limited program.

The data are 101,766 encounters for 71,518 patients at 130 U.S. hospitals, 1999–2008
(Clore et al., 2014). After cleaning, 99,340 encounters for 69,987 patients remain, and
11.4% were readmitted within 30 days.

## Deliverable 1 results

The test set holds 25% of patients (24,757 encounters). No patient appears in both
training and test, and cross-validation uses five folds grouped by patient.

| Model | CV ROC-AUC (mean ± SD) | Test ROC-AUC | Test PR-AUC | Recall | Lift, top 10% |
|---|---|---|---|---|---|
| **Logistic regression (initial model)** | .656 ± .005 | **.661** | .198 | .573 | 2.08 |
| Random forest, default settings | .635 ± .008 | .635 | .187 | .001 | 2.04 |
| Prior-admissions heuristic | .608 ± .006 | .605 | .177 | .491 | 2.09 |
| Dummy (base rate) | .500 | .500 | .113 | .000 | 1.00 |

- **Initial model.** Logistic regression reaches a test ROC-AUC of .661 (95% patient-level
  bootstrap CI .650–.673). It beats the heuristic by .048–.065 AUC and the default forest by
  .017–.034, and ties the heuristic in the top risk decile.
- **The accuracy trap.** The default forest's 88.7% accuracy equals a model that predicts
  "no readmission" for everyone, while it catches 0.1% of readmissions. Tuning is therefore
  scored on ROC-AUC.
- **Preliminary tuning.** A tuned forest (depth 10, 200 trees) reaches .665, against .662 for
  tuned logistic regression. The difference is not significant (95% CI −.001 to .008).
- **Ethics check.** Two gaps are carried into Deliverable 2. Women are flagged more often
  than men (38.8% vs. 34.6%) at the same base rate, and discrimination is weaker for
  patients 65 and older (AUC .633 vs. .713).

## Deliverables

| File | Contents |
|---|---|
| [`Diabetes_Readmission_Deliverable1_Chinthaluri_Abburi.docx`](Diabetes_Readmission_Deliverable1_Chinthaluri_Abburi.docx) | Report, APA 7th: problem framing, dataset exploration and preprocessing, initial model development and tuning, ethics and real-world application, team collaboration, references, Appendix A |
| [`Diabetes_Readmission_D1_Chinthaluri_Abburi.ipynb`](Diabetes_Readmission_D1_Chinthaluri_Abburi.ipynb) | Colab notebook, executed with outputs; downloads the data on first run |

## How we collaborate

- **Issues.** Every task is an [issue](https://github.com/ychinthaluri53651/diabetes-readmission-residency-day-1/issues) assigned to its owner and grouped under
  a [milestone](https://github.com/ychinthaluri53651/diabetes-readmission-residency-day-1/milestones) for each deliverable.
- **Branches.** Each task has its own branch, named `owner/short-task`.
- **Pull requests.** Nothing reaches `main` until the other member approves the
  [pull request](https://github.com/ychinthaluri53651/diabetes-readmission-residency-day-1/pulls?q=is%3Apr). `CODEOWNERS` requests that review automatically, and
  the pull-request template carries the review checklist.
- **Decisions.** Methodological choices are logged in [DECISIONS.md](DECISIONS.md) with
  proposer, reviewer, and date, along with notes from our weekly check-ins.
- **Authorship.** Each of us commits under our own GitHub account, so the history records
  who wrote and who reviewed each change.

## Reproducing the results

**In Colab:** click the badge above and run Runtime → Run all. The notebook downloads the
UCI files itself. For this private repository, Colab first asks for permission to read
private GitHub repositories.

**Locally** (Python 3.14):

```bash
pip install -r requirements.txt
python3 build_notebook.py       # executes the notebook -> figures/*.png, outputs/results.json
python3 render_screenshots.py   # renders the tagged notebook cells -> figures/shot_*.png
python3 generate_report.py      # -> Diabetes_Readmission_Deliverable1_Chinthaluri_Abburi.docx
```

The executed notebook is the single source of truth: every figure is written to `figures/`
and every reported number to `outputs/results.json`, which the report reads. The report build
fails on an abstract over 150 words, an uncited reference, an exhibit never called out, or a
sentence the results no longer support.

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
<summary><b>How the course "Hints and Tips for Success" are followed</b></summary>

Every step is followed visibly; the notebook header maps each hint to its section. Three
hints would introduce errors on this dataset, so they are applied in corrected form and the
notebook explains why:

- **Forward fill** → missing values are handled column by column, because each row is a
  different patient.
- **Encoding and scaling before the split** → both are fit after the split, inside a
  `Pipeline`, so test-set statistics cannot leak into training.
- **`GridSearchCV` scored on accuracy** → scored on ROC-AUC with folds grouped by patient
  (see the accuracy trap above).

</details>

## Data

Clore, J., Cios, K., DeShazo, J., & Strack, B. (2014). *Diabetes 130-US hospitals for years
1999–2008* [Data set]. UCI Machine Learning Repository. <https://doi.org/10.24432/C5230J>
(CC BY 4.0). The full reference list is in the report.
