# Residency Project — Deliverable 1: 30-Day Readmission for Patients With Diabetes

**Course:** Python Application for Data Analytics in AI (PhDAI-733-M20) · **Instructor:** Dr. Marwan Omar
**Team:** Yogananda Atreya Chinthaluri (53651) — data and modeling lead · Anil Kumar Abburi (53405) — evaluation, ethics, and application lead

Can routinely collected encounter data rank diabetic inpatients by 30-day readmission risk
at discharge, well enough to target a capacity-limited care-transition program?
Data: Clore, J., Cios, K., DeShazo, J., & Strack, B. (2014), *Diabetes 130-US hospitals for
years 1999–2008*, UCI Machine Learning Repository, CC BY 4.0 — <https://doi.org/10.24432/C5230J>.

## Deliverables

| File | What it is |
|---|---|
| `Diabetes_Readmission_D1_Chinthaluri.ipynb` | **Colab notebook** — self-contained (downloads the UCI file on first run), ships with outputs and figures; follows the course "Hints and Tips for Success" step by step (map in the notebook header) |
| `Diabetes_Readmission_Deliverable1_Chinthaluri.docx` | **Report** — APA 7th (Assignment 4 format): Introduction and Problem Framing → Dataset Exploration and Preprocessing → Initial Model Development (incl. Preliminary Tuning) → Ethical Considerations and Real-World Application → Team Collaboration Process → References → Appendix A (Colab link, rubric map, course-hints map) |

## Before submitting

1. Complete the team tasks in `TEAM_TASKS.md` and set each flag in `TEAM_TASKS`
   (`generate_report.py`) to `True` only once it is actually done.
2. Set `COLAB_URL` in `generate_report.py` (upload the `.ipynb` to Colab, Share → "Anyone with
   the link can view", paste the link).
3. Rebuild. `generate_report.py` prints a WARNING while either step is incomplete.

## Reproducing

```bash
python3 build_notebook.py       # executes the notebook -> figures/*.png, outputs/results.json
python3 render_screenshots.py   # renders the tagged notebook cells -> figures/shot_*.png
python3 generate_report.py      # -> Diabetes_Readmission_Deliverable1_Chinthaluri.docx
```

The random-forest cross-validation and grid search make the notebook take several minutes
on one core; in Colab the trees run in parallel (`N_JOBS = -1`).

`generate_report.py` fails the build on: an abstract over 150 words, a section outside ±25%
of its page budget, an uncited reference, a British spelling, an exhibit never called out,
exhibits first mentioned out of order, a spacing slip, or a **narrative claim the results
no longer support** (the `CLAIMS` list re-checks each results-dependent sentence).

## Course hints: where they are followed

The three hints that would introduce errors on this dataset are applied in corrected form,
and the notebook explains each:

- **`fillna(method='ffill')`** → per-column missing-value handling. Rows are different
  patients, so forward fill would copy one patient's values into another's record (and
  pandas 3 removed the argument).
- **Encode/scale before the split** → `OneHotEncoder` + `StandardScaler` inside a `Pipeline`
  fit after the split, so test-set statistics cannot leak into training.
- **`GridSearchCV(scoring='accuracy')`** → ROC-AUC scoring with patient-grouped folds. The
  default random forest shows why: its accuracy equals a do-nothing model's while it catches
  almost no readmissions.

## File layout

- `data/` — `diabetic_data.csv` and `IDS_mapping.csv` from the UCI archive
- `build_notebook.py` — assembles and executes the notebook, the **single source of truth**:
  every figure goes to `figures/`, every quoted number to `outputs/results.json`
- `render_screenshots.py` — draws the cells tagged `shot:<key>` (code + real output) to PNG
- `report_common.py` — APA-7th python-docx helpers (same house style as Assignment 4)
- `generate_report.py` — builds the DOCX from `results.json`, so the text cannot drift from the code
- `Hints and Tips for Success.docx` — the course guidance the notebook follows
- `TEAM_TASKS.md` — who leads and reviews what, Deliverable 1 tasks, Deliverable 2 split
- `DECISIONS.md` — decision log with proposer and reviewer, plus meeting notes
