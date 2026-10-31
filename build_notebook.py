"""
Assembles (and executes) the Google Colab deliverable for Residency Project Deliverable 1.

The notebook is written as data here so it is reproducible: re-running this script
regenerates the .ipynb with fresh, embedded outputs.  It is SELF-CONTAINED: in Colab it
downloads the UCI file itself, so the instructor needs only the notebook link.

When executed, the notebook is also the single source of truth for the report: it saves
every figure to figures/ and every scalar it computes to outputs/results.json, which
generate_report.py reads.  Cells tagged "shot:<key>" are rendered to PNG screenshots by
render_screenshots.py for the report.
"""

import nbformat as nbf
from nbclient import NotebookClient
from pathlib import Path

HERE = Path(__file__).resolve().parent
NB_PATH = HERE / "Diabetes_Readmission_D1_Chinthaluri.ipynb"

C = []          # (kind, source, tags)
md = lambda s: C.append(("md", s.strip("\n"), []))
code = lambda s, shot=None: C.append(("code", s.strip("\n"), [f"shot:{shot}"] if shot else []))

# ─────────────────────────────────────────────────────────────────────────────
md(r'''
# Predicting 30-Day Readmission for Hospitalized Patients With Diabetes
### Residency Project, Deliverable 1: Data Exploration, Preprocessing, and an Initial Model

**Course:** Python Application for Data Analytics in AI (PhDAI-733-M20)
**Team:** Yogananda Atreya Chinthaluri (Student ID 53651) and Anil Kumar Abburi (Student ID 53405)

---

**Problem.** Roughly one in five Medicare patients is rehospitalized within 30 days of
discharge, and the Hospital Readmissions Reduction Program penalizes hospitals with excess
readmissions. Patients with diabetes are a large, high-risk share of that population.

**Question.** *Using only information available at discharge, can routinely collected
encounter data rank diabetic inpatients by their risk of readmission within 30 days, well
enough to target a limited care-transition program?*

**Data.** Clore, J., Cios, K., DeShazo, J., & Strack, B. (2014). *Diabetes 130-US hospitals
for years 1999–2008* [Data set]. UCI Machine Learning Repository (CC BY 4.0).
<https://doi.org/10.24432/C5230J>

| Notebook section | Deliverable 1 component |
|---|---|
| 1–3 | Dataset identification and exploration |
| 4–6 | Preprocessing: duplicates, exclusions, missing values, recoding, feature engineering |
| 7–11 | Initial models: split, pipeline, training, cross-validation, holdout evaluation |
| 12 | Preliminary hyperparameter tuning |
| 13 | Ethical considerations |
| 14 | Foundations carried into Deliverable 2 |

**Course "Hints and Tips for Success" and where each is followed.** Three hints are applied in
a corrected form for this dataset; the cell that applies each one explains why.

| Hint | Section | How it is applied here |
|---|---|---|
| 1. Setup and imports | 1 | pandas, NumPy, Matplotlib, seaborn, scikit-learn; warnings suppressed |
| 2. Uploading or accessing data | 2 | Downloaded by URL (hint for large data), with `files.upload()` as fallback |
| 3. Exploration and cleaning | 3–4, 6 | `shape`, `info()`, `describe()`, `countplot`, distribution histograms, correlation heatmap, `drop_duplicates()`; missing values handled per column, **not** forward-filled |
| 4. Feature engineering and preprocessing | 5, 7 | One-hot encoding and `StandardScaler`, fit **after** the split inside a `Pipeline` |
| 5. Train–test split | 7 | 75/25 with `random_state=42`, **grouped by patient** |
| 6. Model training and evaluation | 8–11 | Logistic regression and `RandomForestClassifier`; `classification_report`; seaborn confusion-matrix heatmaps |
| 7. Hyperparameter tuning | 12 | `GridSearchCV` with the hint's forest grid, scored on ROC-AUC (**not** accuracy) with patient-grouped folds |
| 8. Ethical considerations | 13 | Markdown cell answering the hint's questions, plus a subgroup check |
''')

# ── 1. Setup ────────────────────────────────────────────────────────────────
md(r'''
## 1. Setup and imports
All libraries are imported up front (hint 1), including `GridSearchCV` for the preliminary
tuning in Section 12. `mean_squared_error` is left out: it is a regression metric and does not
apply to this classification task. One random seed, one house style, and one results dictionary (`R`)
collect every number quoted in the written report.
''')

code(r'''
import io, json, sys, urllib.request, warnings, zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import NullFormatter, PercentFormatter
import sklearn
from scipy.stats import chi2_contingency
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, average_precision_score,
                             classification_report, confusion_matrix, f1_score,
                             precision_recall_curve, precision_score, recall_score,
                             roc_auc_score, roc_curve)
from sklearn.model_selection import (GridSearchCV, GroupShuffleSplit,
                                     StratifiedGroupKFold, train_test_split)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

warnings.filterwarnings("ignore")
pd.set_option("display.width", 120)
SEED = 42

NAVY, RED, STEEL, GOLD, TEAL, GRAY = (
    "#131D45", "#B21E27", "#5B6E8C", "#C8922A", "#2F6E6B", "#9AA3B0")
plt.rcParams.update({
    "font.family": "serif", "font.serif": ["Georgia", "DejaVu Serif"],
    "font.size": 9, "axes.titlesize": 10, "axes.titleweight": "bold",
    "axes.labelsize": 9, "xtick.labelsize": 8, "ytick.labelsize": 8,
    "legend.fontsize": 8, "legend.frameon": False, "axes.spines.top": False,
    "axes.spines.right": False, "axes.grid": True, "grid.color": "#E2E2E2",
    "axes.edgecolor": "#4A4A4A", "axes.axisbelow": True, "figure.dpi": 110,
})
PCT_AXIS = PercentFormatter(1.0)

FIGDIR, OUTDIR = Path("figures"), Path("outputs")
FIGDIR.mkdir(exist_ok=True); OUTDIR.mkdir(exist_ok=True)
R = {"versions": {"python": sys.version.split()[0], "pandas": pd.__version__,
                  "sklearn": sklearn.__version__}}

def save(fig, name):
    """Save at print resolution, then display inline."""
    fig.savefig(FIGDIR / name, dpi=200, bbox_inches="tight")
    plt.show()

print(R["versions"])
''')

# ── 2. Load ─────────────────────────────────────────────────────────────────
md(r'''
## 2. Access the data
Following hint 2's advice for large datasets, the loader downloads the UCI archive by URL
(about 3 MB zipped, 19 MB unzipped), so the notebook runs unchanged in Colab or on a laptop.
If the download is blocked, it falls back to the Colab upload widget. Two parsing choices
matter: the file codes missing values as `?`, and it uses the literal string `None` to
mean *test not performed*. pandas treats `"None"` as missing by default, which would erase
a clinically meaningful category, so the default NA strings are switched off.
''')

code(r'''
DATA = Path("data/diabetic_data.csv")
UCI_ZIP = ("https://archive.ics.uci.edu/static/public/296/"
           "diabetes+130-us+hospitals+for+years+1999-2008.zip")

def load_raw() -> pd.DataFrame:
    """Read the UCI file; download it by URL, or fall back to a Colab upload."""
    if not DATA.exists():
        DATA.parent.mkdir(exist_ok=True)
        try:
            with urllib.request.urlopen(UCI_ZIP) as resp:
                zipfile.ZipFile(io.BytesIO(resp.read())).extractall(DATA.parent)
        except OSError:
            from google.colab import files                # hint 2: manual upload
            uploaded = files.upload()                       # choose diabetic_data.csv
            DATA.write_bytes(uploaded[next(iter(uploaded))])
    # '?' = missing; "None" = test not performed, so keep it as a category.
    return pd.read_csv(DATA, na_values="?", keep_default_na=False, low_memory=False)

raw = load_raw()
print(raw.shape)
R["n_raw"], R["n_cols_raw"] = raw.shape
R["n_patients_raw"] = int(raw["patient_nbr"].nunique())
R["n_dup_rows"] = int(raw.duplicated().sum())
print(f"{len(raw):,} encounters x {raw.shape[1]} columns, "
      f"{R['n_patients_raw']:,} patients, {R['n_dup_rows']} duplicate rows")

miss = raw.isna().mean().sort_values(ascending=False)
miss = miss[miss > 0]
R["missing_share"] = miss.round(4).to_dict()
print("\nShare of values missing ('?'):")
print(miss.map("{:.1%}".format).to_string())

target = raw["readmitted"].value_counts(normalize=True)
R["target_3class"] = target.round(4).to_dict()
print("\nreadmitted:", target.map("{:.1%}".format).to_dict())
''', shot="load")

md(r'''
## 3. Explore the data
Size, structure, and summary statistics first (hint 3), then the property that shapes
everything downstream: many patients appear more than once, so encounters are not
independent.
''')

code(r'''
print(raw.shape)
raw.info()
''')

code(r'''
raw.describe().T.round(2)
''')

code(r'''
per_patient = raw.groupby("patient_nbr").size()
enc_in_repeat = raw["patient_nbr"].map(per_patient) > 1
R["share_enc_repeat_patients"] = float(enc_in_repeat.mean())
R["share_patients_repeat"] = float((per_patient > 1).mean())
R["max_enc_per_patient"] = int(per_patient.max())
R["n_admission_codes"] = {c: int(raw[c].nunique()) for c in
                          ["admission_type_id", "discharge_disposition_id",
                           "admission_source_id"]}
R["n_icd9_codes"] = int(pd.concat([raw["diag_1"], raw["diag_2"], raw["diag_3"]]).nunique())
print(f"{R['share_patients_repeat']:.1%} of patients have >1 encounter; they account "
      f"for {R['share_enc_repeat_patients']:.1%} of encounters (max {R['max_enc_per_patient']})")
print("distinct ICD-9 codes across diag_1-3:", R["n_icd9_codes"])
''')

code(r'''
fig, ax = plt.subplots(1, 3, figsize=(12, 3.7), gridspec_kw={"width_ratios": [1.25, 1, 1]})

# (a) missingness
m = miss.sort_values()
colors = [RED if v > 0.30 else NAVY for v in m.values]
ax[0].barh(m.index, m.values, color=colors)
for i, v in enumerate(m.values):
    ax[0].text(v + 0.01, i, f"{v:.1%}", va="center", fontsize=8)
ax[0].set_xlim(0, 1.12)
ax[0].xaxis.set_major_formatter(PCT_AXIS)
ax[0].set(title="(a) Missing values by column", xlabel="Share of encounters missing")

# (b) target: seaborn countplot (hint 3)
OUTCOME = {"NO": "Not readmitted", ">30": "After 30 days", "<30": "Within 30 days"}
sns.countplot(data=raw.assign(outcome=raw["readmitted"].map(OUTCOME)), x="outcome",
              order=list(OUTCOME.values()), hue="outcome", hue_order=list(OUTCOME.values()),
              palette=[GRAY, STEEL, RED], legend=False, width=0.6, ax=ax[1])
for i, k in enumerate(OUTCOME):
    n = int((raw["readmitted"] == k).sum())
    ax[1].text(i, n * 1.02, f"{n / len(raw):.1%}", ha="center", fontsize=8)
ax[1].yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v / 1000:.0f}k"))
ax[1].set(title="(b) Readmission outcome (red = target)", xlabel="", ylabel="Encounters")

# (c) encounters per patient
k = per_patient.clip(upper=5).value_counts().sort_index()
ax[2].bar([str(i) if i < 5 else "5+" for i in k.index], k.values, color=NAVY, width=0.6)
ax[2].set_yscale("log")
for i, v in enumerate(k.values):
    ax[2].text(i, v * 1.15, f"{v:,}", ha="center", fontsize=7.5)
ax[2].set_ylim(top=k.max() * 4)
ax[2].set(title="(c) Encounters per patient", xlabel="Encounters in file",
          ylabel="Patients (log scale)")

fig.suptitle("Data audit: missingness, class balance, and repeat patients",
             fontweight="bold", y=1.03)
plt.tight_layout()
save(fig, "fig_audit.png")
''')

md(r'''
**Reading the audit.** `weight` is almost entirely missing and cannot be rescued.
`medical_specialty` and `payer_code` are missing for roughly half and two-fifths of
encounters: too many to drop rows, and probably not missing at random (an unrecorded
specialty plausibly signals a different admission pathway). The target is imbalanced, with
about one encounter in nine followed by a readmission within 30 days. Nearly half of all
encounters belong to patients seen more than once, so a random row split would put the
same patient on both sides of the train–test boundary.
''')

md(r'''
### Distributions and correlations of the numeric features
Hint 3 asks for the value distributions to be visualized. Histograms compare each count
feature between readmitted and non-readmitted encounters, and a Spearman correlation
heatmap (rank-based, because the counts are skewed) checks for redundant features.
''')

code(r'''
NUM_RAW = ["time_in_hospital", "num_lab_procedures", "num_procedures", "num_medications",
           "number_outpatient", "number_emergency", "number_inpatient", "number_diagnoses"]
LABEL = {"time_in_hospital": "Length of stay", "num_lab_procedures": "Lab tests",
         "num_procedures": "Procedures", "num_medications": "Medications",
         "number_outpatient": "Prior outpatient", "number_emergency": "Prior emergency",
         "number_inpatient": "Prior inpatient", "number_diagnoses": "Diagnoses",
         "readmit_30": "Readmitted <30d"}
eda = raw.assign(readmit_30=(raw["readmitted"] == "<30").astype(int))
eda["Outcome"] = eda["readmit_30"].map({0: "Not readmitted <30d", 1: "Readmitted <30d"})

fig = plt.figure(figsize=(13, 5.6))
grid = fig.add_gridspec(2, 4, width_ratios=[1, 1, 1.2, 1.2], wspace=0.35, hspace=0.45)
for i, c in enumerate(["time_in_hospital", "num_medications", "num_lab_procedures",
                       "number_inpatient"]):
    a = fig.add_subplot(grid[i // 2, i % 2])
    sns.histplot(data=eda, x=c, hue="Outcome", stat="density", common_norm=False,
                 discrete=c != "num_lab_procedures", bins=40, element="step", alpha=0.35,
                 palette={"Not readmitted <30d": STEEL, "Readmitted <30d": RED},
                 legend=i == 0, ax=a)
    if c == "number_inpatient":
        a.set_xlim(-0.6, 10.6)
    a.set(title=f"({'abcd'[i]}) {LABEL[c]}", xlabel="Count", ylabel="Density")
    if i == 0:
        sns.move_legend(a, "upper right", title=None, fontsize=7)

corr = eda[NUM_RAW + ["readmit_30"]].corr(method="spearman")
hm = fig.add_subplot(grid[:, 2:])
sns.heatmap(corr, mask=np.triu(np.ones_like(corr, dtype=bool)), annot=True, fmt=".2f",
            cmap="RdBu_r", center=0, vmin=-1, vmax=1, annot_kws={"size": 7.5},
            xticklabels=[LABEL[c] for c in corr.columns],
            yticklabels=[LABEL[c] for c in corr.index],
            cbar_kws={"label": "Spearman ρ", "shrink": 0.75}, ax=hm)
hm.grid(False)
hm.set_title("(e) Spearman correlations among numeric features and the outcome")
fig.suptitle("Distributions of count features by outcome, and their correlations",
             fontweight="bold", y=1.0)
save(fig, "fig_numeric.png")

feat = corr.loc[NUM_RAW, NUM_RAW].where(~np.eye(len(NUM_RAW), dtype=bool)).abs()
pair = feat.stack().idxmax()
R.update(skew_counts={c: float(eda[c].skew()) for c in NUM_RAW},
         corr_max_pair=[LABEL[pair[0]], LABEL[pair[1]]], corr_max=float(corr.loc[pair]),
         corr_outcome={LABEL[c]: float(corr.loc[c, "readmit_30"]) for c in NUM_RAW})
print(f"strongest feature pair: {pair} rho = {R['corr_max']:.2f}")
print("rho with outcome:", {k: round(v, 3) for k, v in R["corr_outcome"].items()})
''')

md(r'''
**Reading the distributions.** The prior-visit counts are extremely right-skewed (most
patients have zero; prior emergency visits reach a skew above 20), which motivates the
`log(1 + count)` transform in Section 5. Lab tests and diagnoses, by contrast, are roughly
symmetric. Readmitted encounters sit to the right on prior inpatient visits and,
more weakly, on medications and length of stay. No pair of features is close to redundant:
the strongest correlation is moderate, so all numeric features are kept and L2
regularization absorbs the overlap. Prior inpatient visits has the strongest rank
correlation with the outcome, but it is still weak in absolute terms, a first sign that no
single feature will separate the classes.
''')

# ── 4. Cleaning ─────────────────────────────────────────────────────────────
md(r'''
## 4. Clean: duplicates, exclusions, missing values, and the target
Hint 3 suggests `drop_duplicates()` and `fillna(method='ffill')`. Duplicates are checked and
dropped (none exist). **Forward fill is not used.** Each row is a different patient's
encounter, so forward fill would copy one patient's specialty or race into the next
patient's record, and pandas 3 has removed `fillna(method=...)` in any case. Missing values
are handled per column instead:

| Column | Missing | Treatment |
|---|---|---|
| `weight` | 96.9% | Dropped: too sparse to use or impute |
| `payer_code` | 39.6% | Excluded from predictors; kept for the fairness audit |
| `medical_specialty` | 49.1% | Explicit `Missing` category (missingness is informative) |
| `race` | 2.2% | Not a predictor; `Missing` category in the audit |
| `diag_1`–`diag_3` | ≤ 1.4% | `Missing` diagnosis group |
| `A1Cresult`, `max_glu_serum` | coded `None` | `Not measured` category |
| numeric columns | 0% | No treatment needed |

Rows are removed only where the outcome is undefined, and each step is logged with its
effect on size and on the readmission rate.
''')

code(r'''
NO_RISK = [11, 13, 14, 19, 20, 21]     # discharge codes: expired or hospice

def step(frame, label):
    return {"step": label, "encounters": len(frame),
            "patients": frame["patient_nbr"].nunique(),
            "rate_30d": (frame["readmitted"] == "<30").mean()}

ledger = [step(raw, "Raw UCI file")]
df = raw.drop_duplicates()                                  # hint 3
ledger.append(step(df, "Drop exact duplicate rows"))
df = df[~df["discharge_disposition_id"].isin(NO_RISK)].copy()
ledger.append(step(df, "Remove deaths and hospice discharges"))
df = df[df["gender"] != "Unknown/Invalid"].copy()
ledger.append(step(df, "Remove invalid gender codes"))

# Binary target; the 3-class source column is dropped so it cannot leak into X.
df["readmit_30"] = (df["readmitted"] == "<30").astype(int)
df = df.drop(columns="readmitted")

ledger = pd.DataFrame(ledger)
R["ledger"] = ledger.round(4).to_dict(orient="records")
R["n_clean"], R["n_patients_clean"] = len(df), int(df["patient_nbr"].nunique())
R["prevalence"] = float(df["readmit_30"].mean())
R["numeric_missing"] = int(raw.select_dtypes("number").isna().sum().sum())
print(ledger.to_string(index=False, formatters={"rate_30d": "{:.2%}".format}))
print("missing values in numeric columns:", R["numeric_missing"])
''')

# ── 5. Feature engineering ──────────────────────────────────────────────────
md(r'''
## 5. Feature engineering
* **Diagnoses.** More than 900 distinct ICD-9 codes are collapsed into the nine clinical
  groups used by Strack et al. (2014).
* **Administrative IDs.** Admission type, source, and discharge disposition are integer codes
  with no numeric meaning. They are mapped to a few interpretable categories, and the
  `NULL`, `Not Mapped`, and `Not Available` codes are pooled as unknown.
* **Age.** Ten-year bands become an ordinal midpoint (e.g., `[70-80)` → 75).
* **Prior utilization.** Outpatient, emergency, and inpatient visit counts in the prior year
  are heavily right-skewed, so they enter the model as `log(1 + count)`.
* **Medications.** Drugs used in under 1% of encounters are dropped. One engineered count,
  the number of diabetes drugs whose dose changed (`Up`/`Down`), summarizes the regimen.
''')

code(r'''
def icd9_group(code):
    """Map one ICD-9 code to the nine groups of Strack et al. (2014)."""
    if pd.isna(code):
        return "Missing"
    if code[0] in "VE":
        return "Other"
    v = float(code)
    if 390 <= v < 460 or int(v) == 785: return "Circulatory"
    if 460 <= v < 520 or int(v) == 786: return "Respiratory"
    if 520 <= v < 580 or int(v) == 787: return "Digestive"
    if int(v) == 250:                   return "Diabetes"
    if 800 <= v < 1000:                 return "Injury"
    if 710 <= v < 740:                  return "Musculoskeletal"
    if 580 <= v < 630 or int(v) == 788: return "Genitourinary"
    if 140 <= v < 240:                  return "Neoplasms"
    return "Other"

for k in ["diag_1", "diag_2", "diag_3"]:
    df[f"{k}_group"] = df[k].map(icd9_group)

DISCHARGE = {1: "Home", 6: "Home health", 8: "Home health", 7: "Left AMA",
             18: "Unknown", 25: "Unknown", 26: "Unknown"}
df["discharge"] = df["discharge_disposition_id"].map(DISCHARGE).fillna("Facility transfer")
SOURCE = {7: "Emergency room", 1: "Referral", 2: "Referral", 3: "Referral",
          **{c: "Transfer" for c in [4, 5, 6, 10, 18, 22, 25, 26]}}
df["admission_source"] = df["admission_source_id"].map(SOURCE).fillna("Other/unknown")
df["admission_type"] = (df["admission_type_id"]
                        .map({1: "Emergency", 2: "Urgent", 3: "Elective"})
                        .fillna("Other/unknown"))
df["age_years"] = df["age"].str.extract(r"\[(\d+)", expand=False).astype(float) + 5
for c in ["A1Cresult", "max_glu_serum"]:
    df[c] = df[c].replace({"None": "Not measured"})
for c in ["number_outpatient", "number_emergency", "number_inpatient"]:
    df[f"log_{c}"] = np.log1p(df[c])

DRUGS = ["metformin", "repaglinide", "nateglinide", "chlorpropamide", "glimepiride",
         "acetohexamide", "glipizide", "glyburide", "tolbutamide", "pioglitazone",
         "rosiglitazone", "acarbose", "miglitol", "troglitazone", "tolazamide", "examide",
         "citoglipton", "insulin", "glyburide-metformin", "glipizide-metformin",
         "glimepiride-pioglitazone", "metformin-rosiglitazone", "metformin-pioglitazone"]
df["n_med_changes"] = df[DRUGS].isin(["Up", "Down"]).sum(axis=1)
use = (df[DRUGS] != "No").mean()
KEPT_DRUGS = use[use >= 0.01].index.tolist()

R["n_drugs"], R["kept_drugs"] = len(DRUGS), KEPT_DRUGS
R["diag1_groups"] = df["diag_1_group"].value_counts(normalize=True).round(4).to_dict()
R["skew_inpatient"] = float(df["number_inpatient"].skew())
R["skew_log_inpatient"] = float(df["log_number_inpatient"].skew())
print("primary-diagnosis groups:", df["diag_1_group"].value_counts().to_dict())
print(f"kept {len(KEPT_DRUGS)} of {len(DRUGS)} drug columns:", KEPT_DRUGS)
print(f"skew of prior inpatient visits: {R['skew_inpatient']:.2f} raw -> "
      f"{R['skew_log_inpatient']:.2f} after log1p")
''')

# ── 6. EDA ──────────────────────────────────────────────────────────────────
md(r'''
## 6. Explore: which encounter characteristics track readmission?
Each panel shows the observed 30-day readmission rate with a 95% Wilson confidence
interval, against the overall rate (dashed). These are descriptive, unadjusted
comparisons. They guide feature selection but do not establish independent effects.
''')

code(r'''
def rates(key, order=None, z=1.96):
    """Readmission rate per level with a 95% Wilson interval (stays inside [0, 1])."""
    g = df.groupby(key, observed=True)["readmit_30"].agg(["mean", "size"])
    g = g.reindex(order) if order is not None else g
    p, n = g["mean"], g["size"]
    center = (p + z**2 / (2 * n)) / (1 + z**2 / n)
    half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / (1 + z**2 / n)
    g["lo"], g["hi"] = p - (center - half), (center + half) - p
    return g

inpatient = rates(df["number_inpatient"].clip(upper=5))
inpatient.index = [str(i) if i < 5 else "5+" for i in inpatient.index]
disch = rates("discharge", ["Home", "Home health", "Facility transfer", "Left AMA", "Unknown"])
ages = rates("age")
ages.index = [a.strip("[)").replace("-", "–") for a in ages.index]
a1c = rates("A1Cresult", ["Not measured", "Norm", ">7", ">8"])
a1c.index = ["Not measured", "Normal", ">7%", ">8%"]

measured = df["A1Cresult"] != "Not measured"
chi2, p_a1c, *_ = chi2_contingency(pd.crosstab(measured, df["readmit_30"]))
R.update(rate_by_inpatient=inpatient["mean"].round(4).to_dict(),
         n_by_inpatient=inpatient["size"].to_dict(),
         rate_by_discharge=disch["mean"].round(4).to_dict(),
         rate_by_age=ages["mean"].round(4).to_dict(),
         rate_by_a1c=a1c["mean"].round(4).to_dict(),
         a1c_measured_share=float(measured.mean()),
         rate_a1c_measured=float(df.loc[measured, "readmit_30"].mean()),
         rate_a1c_not=float(df.loc[~measured, "readmit_30"].mean()),
         a1c_chi2=float(chi2), a1c_p=float(p_a1c))

fig, ax = plt.subplots(2, 2, figsize=(10.5, 6.8))
panels = [(inpatient, "(a) Prior-year inpatient admissions", "Admissions"),
          (disch, "(b) Discharge destination", ""),
          (ages, "(c) Age band (years)", "Age"),
          (a1c, "(d) HbA1c result during the stay", "")]
for a, (g, title, xlab) in zip(ax.flat, panels):
    a.bar(g.index, g["mean"], yerr=[g["lo"], g["hi"]], color=NAVY, width=0.65,
          error_kw={"ecolor": "#555555", "capsize": 2, "lw": 0.8})
    a.axhline(R["prevalence"], color=RED, ls="--", lw=1.0)
    a.yaxis.set_major_formatter(PCT_AXIS)
    a.set(title=title, xlabel=xlab, ylabel="30-day readmission rate")
    a.tick_params(axis="x", rotation=0 if len(g) < 7 else 30)
fig.suptitle("Observed 30-day readmission rates with 95% CIs "
             f"(dashed red line = overall rate, {R['prevalence']:.1%})",
             fontweight="bold", y=1.01)
plt.tight_layout()
save(fig, "fig_rates.png")
print(f"HbA1c measured in {R['a1c_measured_share']:.1%} of encounters; readmission "
      f"{R['rate_a1c_measured']:.1%} if measured vs {R['rate_a1c_not']:.1%} if not "
      f"(chi-square p = {R['a1c_p']:.1e})")
''')

md(r'''
**Reading the rates.** Prior inpatient use is the steepest gradient: the readmission rate
climbs steadily from zero to five or more admissions in the prior year, a pattern that
established readmission indices (e.g., LACE) build on. Discharge to another care facility
carries a higher rate than discharge home, consistent with greater illness severity. Age
has a modest gradient. HbA1c was measured in under a fifth of encounters, and measured
encounters were readmitted slightly *less* often, replicating the association Strack
et al. (2014) reported. Here it is a marker of care process, not a causal effect.
''')

# ── 7. Feature set and split ────────────────────────────────────────────────
md(r'''
## 7. Feature set, train–test split, and preprocessing pipeline
* **Predictors** are restricted to information available by discharge.
* **Race, gender, and payer code are excluded from the predictors** and retained for the
  fairness checks in Section 13 and Deliverable 2. Payer is a socioeconomic proxy, and
  race-based risk scores in care management have been shown to encode access disparities.
* **Split before fitting anything (hint 5).** The split uses hint 5's 75/25 ratio and
  `random_state=42`, but it is **grouped by patient**, so no patient contributes encounters
  to both training and test data.
* **Encode and scale after the split (hint 4).** Hint 4 applies `get_dummies` and
  `StandardScaler` to the full data before splitting, which would let test-set means,
  standard deviations, and category lists leak into training. Here `OneHotEncoder`, the
  pipeline-safe equivalent of `get_dummies`, and `StandardScaler` sit inside a scikit-learn
  `Pipeline`, so they are fit on training folds only. All dummy levels are kept, because
  L2 regularization handles the collinearity that `drop_first` exists to avoid.
''')

code(r'''
NUM = ["time_in_hospital", "num_lab_procedures", "num_procedures", "num_medications",
       "number_diagnoses", "log_number_outpatient", "log_number_emergency",
       "log_number_inpatient", "age_years", "n_med_changes"]
CAT = ["admission_type", "admission_source", "discharge", "medical_specialty",
       "diag_1_group", "diag_2_group", "diag_3_group", "max_glu_serum", "A1Cresult",
       "change", "diabetesMed"] + KEPT_DRUGS
AUDIT_ONLY = ["race", "gender", "payer_code"]       # not predictors; used for fairness checks

X, y, groups = df[NUM + CAT], df["readmit_30"], df["patient_nbr"]
split = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=SEED)
tr, te = next(split.split(X, y, groups))
X_tr, X_te, y_tr, y_te = X.iloc[tr], X.iloc[te], y.iloc[tr], y.iloc[te]
assert set(groups.iloc[tr]).isdisjoint(groups.iloc[te])   # no patient on both sides

prep = ColumnTransformer([
    ("num", StandardScaler(), NUM),
    ("cat", Pipeline([
        ("fill", SimpleImputer(strategy="constant", fill_value="Missing")),
        ("onehot", OneHotEncoder(handle_unknown="infrequent_if_exist",
                                 min_frequency=0.01)),
    ]), CAT),
])
logreg = Pipeline([
    ("prep", prep),
    ("clf", LogisticRegression(solver="liblinear", C=1.0, class_weight="balanced",
                               max_iter=1000)),
])
n_cols = clone(prep).fit(X_tr).transform(X_tr[:5]).shape[1]
print(f"train: {len(tr):,} encounters, {groups.iloc[tr].nunique():,} patients, "
      f"rate {y_tr.mean():.2%}")
print(f"test : {len(te):,} encounters, {groups.iloc[te].nunique():,} patients, "
      f"rate {y_te.mean():.2%}")
print(f"{len(NUM)} numeric + {len(CAT)} categorical inputs -> {n_cols} model columns")
''', shot="pipeline")

code(r'''
R.update(n_num=len(NUM), n_cat=len(CAT), n_model_cols=int(n_cols),
         n_train=int(len(tr)), n_test=int(len(te)),
         n_train_patients=int(groups.iloc[tr].nunique()),
         n_test_patients=int(groups.iloc[te].nunique()),
         prev_train=float(y_tr.mean()), prev_test=float(y_te.mean()))
''')

# ── 8. Train models ─────────────────────────────────────────────────────────
md(r'''
## 8. Train the initial models and read their classification reports
Two models share the same preprocessing pipeline (hint 6). The **logistic regression** is
the chosen initial model. It is the standard for clinical risk scores, it is interpretable,
and `class_weight="balanced"` makes it attend to the rare class. The
**`RandomForestClassifier`**, run at its defaults as the hints suggest, is the nonlinear
comparison. `classification_report` gives precision, recall, and F1 at the default 0.5
threshold.
''')

code(r'''
N_JOBS = -1 if "google.colab" in sys.modules else 1      # parallel trees in Colab only
rf = Pipeline([("prep", clone(prep)),
               ("clf", RandomForestClassifier(random_state=SEED, n_jobs=N_JOBS))])
MODELS = {"Logistic regression": logreg, "Random forest": rf}
NAMES = ["Not readmitted", "Readmitted <30d"]

for name, model in MODELS.items():
    model.fit(X_tr, y_tr)
    print(f"=== {name} ===")
    print(classification_report(y_te, model.predict(X_te), target_names=NAMES, digits=3))
''', shot="models")

md(r'''
**Reading the reports.** The default forest posts the higher *accuracy* only because it
almost never predicts a readmission. Its recall for the readmitted class is near zero, and
its accuracy equals that of a model that answers "no" for everyone. The logistic regression
gives up accuracy to find more than half of the readmissions. This is why accuracy is not
used to select or tune models here, including in the grid search of Section 12.
''')

# ── 9. Cross-validation ─────────────────────────────────────────────────────
md(r'''
## 9. Cross-validation on the training set
Five-fold `StratifiedGroupKFold` keeps each patient within one fold and preserves the class
ratio. Both models are compared with two reference points: a **prior-rate dummy**, which
predicts the base rate for everyone, and a **one-variable clinical heuristic**, which ranks
patients by prior-year inpatient admissions alone. A model that cannot beat the heuristic
adds complexity without value.
''')

code(r'''
cv = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEED)
scores = {k: [] for k in ["Logistic regression", "Random forest",
                          "Prior-admissions heuristic", "Dummy (prior rate)"]}
for f_tr, f_va in cv.split(X_tr, y_tr, groups.iloc[tr]):
    yv = y_tr.iloc[f_va]
    for name, model in MODELS.items():
        p = clone(model).fit(X_tr.iloc[f_tr], y_tr.iloc[f_tr]).predict_proba(X_tr.iloc[f_va])[:, 1]
        scores[name].append((roc_auc_score(yv, p), average_precision_score(yv, p)))
    h = X_tr["log_number_inpatient"].iloc[f_va]
    scores["Prior-admissions heuristic"].append((roc_auc_score(yv, h),
                                                 average_precision_score(yv, h)))
    scores["Dummy (prior rate)"].append((0.5, yv.mean()))
R["cv"] = {k: {"auc_mean": float(np.mean([s[0] for s in v])),
               "auc_sd": float(np.std([s[0] for s in v], ddof=1)),
               "ap_mean": float(np.mean([s[1] for s in v])),
               "ap_sd": float(np.std([s[1] for s in v], ddof=1))} for k, v in scores.items()}
pd.DataFrame(R["cv"]).T.round(4)
''')

# ── 10. Holdout ─────────────────────────────────────────────────────────────
md(r'''
## 10. Holdout evaluation
Both models were fit on the full training set in Section 8. They are scored once on the
untouched, patient-disjoint test set. The metrics are chosen for an imbalanced screening
problem:
* **ROC-AUC** measures ranking quality.
* **PR-AUC** is read against the prevalence baseline.
* **Accuracy, recall, and precision** are reported at the default threshold. Accuracy is
  included to show why it misleads.
* **Top-decile lift** is the readmission rate among the 10% highest-risk encounters,
  divided by the overall rate. This is the number a care-transition program with fixed
  capacity would act on.
''')

code(r'''
p_lr = logreg.predict_proba(X_te)[:, 1]
p_rf = rf.predict_proba(X_te)[:, 1]
p_rule = X_te["log_number_inpatient"].to_numpy()             # heuristic risk score
p_dummy = DummyClassifier(strategy="prior").fit(X_tr, y_tr).predict_proba(X_te)[:, 1]
yt = y_te.to_numpy()

def lift_at(score, q, idx=slice(None)):
    """Rate among the top q of encounters by risk / overall rate (ties share credit)."""
    s, t = score[idx], yt[idx]
    k = q * len(s)
    cut = np.sort(s)[::-1][int(k) - 1]
    above, tied = s > cut, s == cut
    hits = t[above].sum() + (k - above.sum()) * t[tied].mean()
    return hits / k / t.mean()

def evaluate(score, flag):
    """Ranking and threshold metrics for one risk score on the test set."""
    return {"roc_auc": roc_auc_score(y_te, score),
            "pr_auc": average_precision_score(y_te, score),
            "accuracy": accuracy_score(y_te, flag),
            "recall": recall_score(y_te, flag, zero_division=0),
            "precision": precision_score(y_te, flag, zero_division=0),
            "f1": f1_score(y_te, flag, zero_division=0),
            "flagged": float(np.mean(flag)),
            "lift_top10": lift_at(score, 0.10)}

holdout = {"Logistic regression": evaluate(p_lr, logreg.predict(X_te)),
           "Random forest": evaluate(p_rf, rf.predict(X_te)),
           "Prior-admissions heuristic": evaluate(p_rule, p_rule > 0),   # >= 1 admission
           "Dummy (prior rate)": evaluate(p_dummy, np.zeros(len(yt), dtype=int))}
R["holdout"] = {k: {m: float(v) for m, v in d.items()} for k, d in holdout.items()}
print(pd.DataFrame(holdout).T.round(3).to_string())
''')

code(r'''
# Patient-level (cluster) bootstrap: 95% CIs that keep each patient's encounters together.
rng = np.random.default_rng(SEED)
g_te = groups.iloc[te].to_numpy()
uniq, inv = np.unique(g_te, return_inverse=True)
rows_of = np.split(np.argsort(inv), np.cumsum(np.bincount(inv))[:-1])
auc_lr, gain, gain_rf, d10 = [], [], [], []
for _ in range(500):
    idx = np.concatenate([rows_of[i] for i in rng.integers(0, len(uniq), len(uniq))])
    a = roc_auc_score(yt[idx], p_lr[idx])
    auc_lr.append(a)
    gain.append(a - roc_auc_score(yt[idx], p_rule[idx]))
    gain_rf.append(a - roc_auc_score(yt[idx], p_rf[idx]))
    d10.append(lift_at(p_lr, 0.10, idx) - lift_at(p_rule, 0.10, idx))
ci = lambda v: (float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5)))
R["boot"] = dict(zip(["auc_lo", "auc_hi"], ci(auc_lr)))
R["boot"].update(zip(["gain_lo", "gain_hi"], ci(gain)))
R["boot"].update(zip(["gain_rf_lo", "gain_rf_hi"], ci(gain_rf)))
R["boot"].update(zip(["lift10_diff_lo", "lift10_diff_hi"], ci(d10)))

# Lift at program capacity: how much richer in readmissions is the flagged group?
CAPS = [0.05, 0.10, 0.20, 0.30]
R["lift_curve"] = {f"{q:.0%}": {"lr": float(lift_at(p_lr, q)), "rf": float(lift_at(p_rf, q)),
                                "rule": float(lift_at(p_rule, q))} for q in CAPS}
cm = confusion_matrix(y_te, logreg.predict(X_te))
R["confusion"] = {"tn": int(cm[0, 0]), "fp": int(cm[0, 1]),
                  "fn": int(cm[1, 0]), "tp": int(cm[1, 1])}
R["mean_pred_prob"] = float(p_lr.mean())
print(R["boot"])
print(pd.DataFrame(R["lift_curve"]).T.round(2).to_string())
''')

code(r'''
fig, ax = plt.subplots(2, 2, figsize=(11, 8.2))
H = R["holdout"]
curves = [(p_lr, "Logistic regression", NAVY, "-"), (p_rf, "Random forest", TEAL, "-"),
          (p_rule, "Prior-admissions heuristic", GOLD, "--")]
for score, name, col, ls in curves:
    fpr, tpr, _ = roc_curve(y_te, score)
    ax[0, 0].plot(fpr, tpr, color=col, ls=ls, lw=1.5,
                  label=f"{name} (AUC {H[name]['roc_auc']:.3f})")
    prec, rec, _ = precision_recall_curve(y_te, score)
    ax[0, 1].plot(rec, prec, color=col, ls=ls, lw=1.3,
                  label=f"{name} (AP {H[name]['pr_auc']:.3f})")
ax[0, 0].plot([0, 1], [0, 1], color=GRAY, ls=":", lw=1, label="Chance (AUC 0.500)")
ax[0, 0].set(title="(a) ROC curves, patient-disjoint test set",
             xlabel="False positive rate", ylabel="True positive rate")
ax[0, 0].legend(loc="lower right")
ax[0, 1].axhline(y_te.mean(), color=RED, ls=":", lw=1,
                 label=f"Prevalence baseline ({y_te.mean():.3f})")
ax[0, 1].set(title="(b) Precision-recall curves", xlabel="Recall", ylabel="Precision",
             ylim=(0, 0.6))
ax[0, 1].legend(loc="upper right")

# (c)-(d) confusion matrices as seaborn heatmaps (hint 6)
for a, (name, model), tag in zip(ax[1], MODELS.items(), "cd"):
    cmx = confusion_matrix(y_te, model.predict(X_te))
    share = cmx / cmx.sum(axis=1, keepdims=True)
    text = np.array([[f"{cmx[i, j]:,}\n({share[i, j]:.0%} of row)" for j in range(2)]
                     for i in range(2)])
    sns.heatmap(share, annot=text, fmt="", cmap="Blues", vmin=0, vmax=1, cbar=False,
                xticklabels=["Not flagged", "Flagged"],
                yticklabels=["Not readmitted", "Readmitted <30d"], annot_kws={"size": 9}, ax=a)
    a.set(title=f"({tag}) {name}: confusion matrix at the default threshold",
          xlabel="Model decision", ylabel="Actual")
fig.suptitle("Initial models on the held-out test set", fontweight="bold", y=1.0)
plt.tight_layout()
save(fig, "fig_performance.png")
''')

md(r'''
**Reading the results.** The logistic regression ranks encounters better than both the
default forest and the one-variable heuristic, and the patient-level bootstrap intervals for
both gains exclude zero. The gain over the heuristic is not uniform, though. Among the very
highest-risk encounters (top 5–10%) the heuristic is statistically indistinguishable from
the model, because a long admission history already identifies those patients. The model's
advantage appears at larger program capacities (20–30%). At the default threshold, the
class-weighted model flags over a third of all encounters, more than a care-transition team
could follow up, so threshold choice is a Deliverable 2 decision.
''')

code(r'''
# Which inputs drive the score?  Coefficients shown as odds ratios: per 1 SD for numeric
# features; for categories (one-hot, no reference level, L2-shrunk) relative to the
# model intercept, so they rank direction and size rather than give adjusted effects.
names = logreg.named_steps["prep"].get_feature_names_out()
coef = pd.Series(logreg.named_steps["clf"].coef_[0], index=names)
enc = logreg.named_steps["prep"].named_transformers_["cat"].named_steps["onehot"]
RARE = {c: "/".join(map(str, lv)) for c, lv in zip(CAT, enc.infrequent_categories_)
        if lv is not None}

def pretty(n):
    n = n.replace("num__", "").replace("cat__", "")
    swaps = {"log_number_inpatient": "Prior inpatient admissions (log, per SD)",
             "log_number_emergency": "Prior emergency visits (log, per SD)",
             "log_number_outpatient": "Prior outpatient visits (log, per SD)",
             "number_diagnoses": "Number of diagnoses (per SD)",
             "time_in_hospital": "Length of stay (per SD)",
             "num_medications": "Number of medications (per SD)",
             "num_procedures": "Number of procedures (per SD)",
             "num_lab_procedures": "Number of lab tests (per SD)",
             "age_years": "Age (per SD)", "n_med_changes": "Dose changes (per SD)"}
    if n in swaps:
        return swaps[n]
    if n.endswith("_infrequent_sklearn"):
        col = n[: -len("_infrequent_sklearn")]
        level = f"{RARE.get(col, 'rare')} (pooled rare)" if col in KEPT_DRUGS else "other (pooled)"
    else:
        col, _, level = n.rpartition("_")
    col = (col.replace("discharge", "Discharge").replace("admission_source", "Admission source")
              .replace("admission_type", "Admission type")
              .replace("medical_specialty", "Specialty")
              .replace("diag_1_group", "Primary dx").replace("diag_2_group", "Secondary dx")
              .replace("diag_3_group", "Tertiary dx").replace("A1Cresult", "HbA1c")
              .replace("max_glu_serum", "Serum glucose").replace("diabetesMed", "Diabetes med")
              .replace("change", "Regimen change"))
    return f"{col}: {level}"

top = pd.concat([coef.nlargest(9), coef.nsmallest(7)]).sort_values()
R["top_coef"] = {pretty(k): float(np.exp(v)) for k, v in top.items()}
R["or_inpatient"] = float(np.exp(coef["num__log_number_inpatient"]))

fig, ax = plt.subplots(figsize=(8.2, 5.2))
ax.barh([pretty(k) for k in top.index], np.exp(top.values) - 1, left=1,
        color=[RED if v > 0 else STEEL for v in top.values], height=0.65)
ax.axvline(1, color="#333333", lw=0.8)
ax.set_xscale("log")
ax.set_xlim(0.6, 1.6)
ax.set_xticks([0.6, 0.7, 0.8, 0.9, 1, 1.2, 1.4, 1.6],
              ["0.6", "0.7", "0.8", "0.9", "1", "1.2", "1.4", "1.6"])
ax.xaxis.set_minor_formatter(NullFormatter())
ax.set(title="Largest logistic-regression effects (odds ratios, log scale)",
       xlabel="Odds ratio for 30-day readmission (red = raises risk, blue = lowers risk)")
plt.tight_layout()
save(fig, "fig_coefficients.png")
''')

md(r'''
**Reading the model.** Prior inpatient use carries the largest standardized effect,
followed by discharge to another facility and specific clinical groupings, which are the
same gradients Section 6 found. Large odds ratios on rare categories are estimated
imprecisely.
''')

# ── 11. Split check ─────────────────────────────────────────────────────────
md(r'''
## 11. Sanity check: does the grouped split change the answer?
Both models are refit on hint 5's conventional *random* split (`train_test_split`,
`test_size=0.25`, `random_state=42`). When a patient's encounters straddle the boundary, a
model can partly recognize the patient, and the random-split score would be optimistic.
''')

code(r'''
r_tr, r_te = train_test_split(np.arange(len(X)), test_size=0.25, random_state=SEED,
                              stratify=y)
shared = np.intersect1d(groups.iloc[r_tr].unique(), groups.iloc[r_te].unique())
R["random_split_shared_patients"] = int(len(shared))
R["random_split_test_rows_shared"] = float(groups.iloc[r_te].isin(shared).mean())
R["random_split_auc"] = {}
for name, model in MODELS.items():
    p = clone(model).fit(X.iloc[r_tr], y.iloc[r_tr]).predict_proba(X.iloc[r_te])[:, 1]
    R["random_split_auc"][name] = float(roc_auc_score(y.iloc[r_te], p))
    print(f"{name}: random-split AUC {R['random_split_auc'][name]:.3f} vs grouped "
          f"{R['holdout'][name]['roc_auc']:.3f}")
print(f"{len(shared):,} patients on both sides ({R['random_split_test_rows_shared']:.1%} "
      f"of random-split test rows)")
''')

md(r'''
For both models the random split is only slightly optimistic, so patient overlap is a minor
source of bias in this dataset. The grouped split is kept anyway: it answers the
deployment question (how does the model do on *new* patients?) and costs nothing.
''')

# ── 12. Preliminary tuning ──────────────────────────────────────────────────
md(r'''
## 12. Preliminary hyperparameter tuning (hint 7)
Hint 7's grid search is applied with two changes:
* **Scoring is ROC-AUC, not accuracy.** Section 8 showed that accuracy rewards a model that
  never flags anyone.
* **The three folds are grouped by patient** (`StratifiedGroupKFold`), so tuning cannot
  exploit repeat patients.

The random-forest grid is the hint's own; the logistic-regression grid tunes the
regularization strength `C`. Full optimization (calibration, capacity-based thresholds,
and a gradient-boosting challenger) is the work of Deliverable 2.
''')

code(r'''
cv3 = StratifiedGroupKFold(n_splits=3, shuffle=True, random_state=SEED)
GRIDS = {"Logistic regression": {"clf__C": [0.01, 0.1, 1, 10]},
         "Random forest": {"clf__n_estimators": [100, 200],
                           "clf__max_depth": [10, 20, None]}}
R["tuning"], P_TUNED = {}, {}
for name, grid in GRIDS.items():
    search = GridSearchCV(clone(MODELS[name]), grid, cv=cv3, scoring="roc_auc")
    search.fit(X_tr, y_tr, groups=groups.iloc[tr])
    P_TUNED[name] = p = search.predict_proba(X_te)[:, 1]
    R["tuning"][name] = {
        "best_params": {k.replace("clf__", ""): v for k, v in search.best_params_.items()},
        "cv_auc": float(search.best_score_), "test_auc": float(roc_auc_score(y_te, p)),
        "test_pr_auc": float(average_precision_score(y_te, p)),
        "lift_top10": float(lift_at(p, 0.10)), "lift_top20": float(lift_at(p, 0.20))}
    t = R["tuning"][name]
    print(f"{name}: best {t['best_params']}")
    print(f"   grouped CV AUC {t['cv_auc']:.3f} | test AUC "
          f"{R['holdout'][name]['roc_auc']:.3f} (default) -> {t['test_auc']:.3f} (tuned)")
''', shot="tuning")

code(r'''
diff = []
for _ in range(500):
    idx = np.concatenate([rows_of[i] for i in rng.integers(0, len(uniq), len(uniq))])
    diff.append(roc_auc_score(yt[idx], P_TUNED["Random forest"][idx])
                - roc_auc_score(yt[idx], P_TUNED["Logistic regression"][idx]))
R["boot"].update(zip(["tuned_rf_minus_lr_lo", "tuned_rf_minus_lr_hi"], ci(diff)))
print("tuned RF minus tuned LR, AUC 95% CI:",
      [round(v, 3) for v in ci(diff)])
''')

md(r'''
**Reading the tuning.** The grid search changes the random forest substantially: limiting
tree depth stops the fully grown trees from memorizing training encounters, and its test
AUC rises accordingly. The logistic regression barely moves, because its discrimination is
nearly flat across the penalty grid. The bootstrap interval in the cell above shows whether the
tuned forest now differs from the logistic regression. If it does not, the interpretable
model is preferred, which is the question Deliverable 2 settles with calibration and
threshold analysis.
''')

# ── 13. Ethics ──────────────────────────────────────────────────────────────
md(r'''
## 13. Ethical Considerations
**What potential biases exist in the dataset?**
- *Utilization as a proxy for need.* Prior inpatient use, the strongest predictor, measures
  access to care as well as illness. Patients who face barriers to admission can look
  lower-risk than they are, the mechanism Obermeyer et al. (2019) documented in a
  commercial care-management algorithm.
- *Representation.* Race is missing for 2.2% of encounters, and the Hispanic, Asian, and
  Other groups are small, so their subgroup estimates are imprecise.
- *Age of the data.* The records end in 2008. Coding practices, diabetes drugs, and
  discharge pathways have changed since, so performance on current data must be re-checked.

**How would the model perform across different demographic groups?** The cell below gives
a first answer on the test set (discrimination, flag rate, and recall by race, gender, and
age). Deliverable 2 adds confidence intervals, calibration by group, and mitigation.

**Is the model interpretable and fair?** The logistic regression's coefficients can be read
directly (Section 10), which supports clinical review. Race, gender, and payer are excluded
as predictors, but excluding a protected attribute does not make a model fair, because
proxies remain. Fairness is therefore judged on outcomes by group, not on the inputs alone.

**Is user data protected?** The public file contains no names, addresses, or dates. Patient
and encounter numbers are pseudonymous and are used only to group the split, never as
predictors. A deployed version would run inside the hospital's systems under HIPAA, with
access limited to the care-transition team.
''')

code(r'''
test = df.iloc[te].assign(p=p_lr, flag=logreg.predict(X_te),
                          age_group=np.where(df["age_years"].iloc[te] >= 65, "65+", "<65"))

def by_group(col):
    rows = {}
    for level, g in test.groupby(col, dropna=False):
        if g["readmit_30"].sum() < 30:                       # too few events to estimate
            continue
        rows["Missing" if pd.isna(level) else level] = {
            "n": len(g), "base_rate": g["readmit_30"].mean(),
            "auc": roc_auc_score(g["readmit_30"], g["p"]), "flag_rate": g["flag"].mean(),
            "recall": recall_score(g["readmit_30"], g["flag"])}
    return pd.DataFrame(rows).T

R["subgroups"] = {}
for col in ["race", "gender", "age_group"]:
    t = by_group(col)
    R["subgroups"][col] = t.astype(float).round(4).to_dict(orient="index")
    print(f"--- {col}\n{t.round(3).to_string()}\n")
''')

md(r'''
**Reading the subgroup check.** Discrimination is nearly identical for the two largest
race groups, which is reassuring but not sufficient. Two gaps stand out. At the default
threshold the flag rate differs between women and men even though their readmission rates
are nearly identical, so the same threshold gives the two groups different chances of
receiving follow-up. And discrimination is clearly weaker for patients 65 and older, the
Medicare population the readmissions penalty program targets. Whether these gaps reflect
real differences in risk factors or miscalibration is a Deliverable 2 question.
''')

# ── 14. Foundations for D2 ──────────────────────────────────────────────────
md(r'''
## 14. Foundations carried into Deliverable 2
1. **Tuning.** Widen the grids (leaf size, features per split), add a gradient-boosting
   challenger, and keep ROC-AUC and PR-AUC under grouped cross-validation as the criteria.
2. **Threshold and calibration.** `class_weight="balanced"` inflates predicted probabilities
   above the true rate. Deliverable 2 calibrates the scores and sets the decision threshold
   from program capacity (e.g., top 10%), not from 0.5.
3. **Ethical evaluation.** Group-level recall, flag rate, and calibration with confidence
   intervals, plus a mitigation test such as group-specific thresholds.
4. **Explanation.** Permutation importance for the final model, so the drivers of each flag
   can be explained to clinicians.
''')

code(r'''
# Persist every scalar quoted in the report so the document cannot drift from the code.
with open(OUTDIR / "results.json", "w") as fh:
    json.dump(R, fh, indent=2, default=float)
print(f"saved {len(R)} result keys and {len(list(FIGDIR.glob('fig_*.png')))} figures")
''')


# ─────────────────────────────────────────────────────────────────────────────
def build():
    nb = nbf.v4.new_notebook()
    cells = []
    for kind, src, tags in C:
        cell = nbf.v4.new_markdown_cell(src) if kind == "md" else nbf.v4.new_code_cell(src)
        if tags:
            cell.metadata["tags"] = tags
        cells.append(cell)
    nb.cells = cells
    nb.metadata = {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"},
        "colab": {"provenance": [], "toc_visible": True},
    }
    print(f"assembled {len(nb.cells)} cells; executing…")
    NotebookClient(nb, timeout=900, kernel_name="python3",
                   resources={"metadata": {"path": str(HERE)}}).execute()
    nbf.write(nb, NB_PATH)
    print(f"wrote {NB_PATH.name}")


if __name__ == "__main__":
    build()
