#!/usr/bin/env python3
"""
Report generator for the Residency Project, Deliverable 1 (PhDAI-733-M20).

Reads outputs/results.json and figures/*.png, both written when build_notebook.py
executes the Colab notebook (screenshots come from render_screenshots.py), and emits an
APA 7th-edition Word document in the Assignment 4 house format.  Every number in the
prose, tables, and figure notes comes from the notebook run, so the document cannot
drift from the code.

Structure: the brief's four sections (Introduction and Problem Framing, Dataset
Exploration and Preprocessing, Initial Model Development, Team Collaboration Process)
plus one section the project rubric grades separately (Ethical Considerations and
Real-World Application), then References and Appendix A (Colab link, rubric map, and
course-hints map).  Narrative length is checked per section with real Georgia font
metrics; exhibits add pages of their own.  Narrative claims that depend on the results
are re-checked at build time (CLAIMS), so a rerun that changes a conclusion fails loudly.

Run:  python3 build_notebook.py && python3 render_screenshots.py && python3 generate_report.py
"""

import json
import re
from pathlib import Path

import report_common as rc

HERE = Path(__file__).resolve().parent
FIGDIR = HERE / "figures"

TITLE = "Predicting 30-Day Hospital Readmission for Patients With Diabetes"
SUBTITLE = ("Residency Project Deliverable 1: Data Exploration, Preprocessing, "
            "and an Initial Model")
OUT_NAME = "Diabetes_Readmission_Deliverable1_Chinthaluri_Abburi.docx"
NOTEBOOK = "Diabetes_Readmission_D1_Chinthaluri_Abburi.ipynb"

# Paste the Colab share link here (Share -> "Anyone with the link can view").
COLAB_URL = ""

# Two-person team with equal shares: each member leads three rubric criteria and reviews
# the other's three, and the roles rotate between deliverables so each leads the core
# modeling once.  TEAM rows: (member, student ID, Deliverable 1 lead, reviews,
# Deliverable 2 lead).
CHINTHALURI, ABBURI = "Yogananda Atreya Chinthaluri", "Anil Kumar Abburi"
REPO_URL = "https://github.com/ychinthaluri53651/diabetes-readmission-residency-day-1"
TEAM = [
    (CHINTHALURI, "53651",
     "Dataset exploration and preprocessing; model development; preliminary tuning",
     "Problem framing; ethics; real-world application",
     "Fairness audit and mitigation; cost and capacity analysis"),
    (ABBURI, "53405",
     "Problem framing; ethical analysis; real-world application; Colab reproduction",
     "Preprocessing, modeling, and tuning pull requests",
     "Optimization: tuning, boosting, calibration, thresholds"),
]
# Rubric criterion -> (lead, reviewer), by surname.
LEADS = {"Problem definition": ("Abburi", "Chinthaluri"),
         "Dataset exploration": ("Chinthaluri", "Abburi"),
         "Model development": ("Chinthaluri", "Abburi"),
         "Optimization and evaluation": ("Chinthaluri", "Abburi"),
         "Ethics and impact": ("Abburi", "Chinthaluri"),
         "Real-world application": ("Abburi", "Chinthaluri"),
         "Teamwork and documentation": ("Both", "Both"),
         "Writing and structure": ("Both", "Abburi (proofread)")}
# The Team section describes these Deliverable 1 tasks as done.  They must actually be
# done by the named member before submission: set each flag to True only when it is
# (details in TEAM_TASKS.md).  The build warns while any is False.
TEAM_TASKS = {
    "Abburi re-ran the notebook in Colab from GitHub and confirmed Tables 3-4 (issue)": True,  # issue #1, 2026-10-31
    "Abburi reviewed and approved the Deliverable 1 pull request on GitHub": True,  # PR #9, 2026-10-31
    "Abburi revised the Introduction and Ethics sections he leads (own branch + PR)": True,  # PR #13, 2026-10-31
    "Chinthaluri reviewed and merged Abburi's pull request": False,
    "Abburi proofread the full report for APA style (issue)": False,
    "First weekly check-in held and logged in DECISIONS.md": False,
}

# Page budgets ("about"), checked at ±25% per section.  The brief sets the first four;
# Model Development carries the preliminary tuning the rubric grades, and the ethics
# section answers the rubric's ethics and real-world rows.
PAGE_BUDGET = {"Introduction and Problem Framing": 0.5,
               "Dataset Exploration and Preprocessing": 1.5,
               "Initial Model Development": 1.25,
               "Ethical Considerations and Real-World Application": 0.6,
               "Team Collaboration Process": 0.5}
TOL = 0.25

# ── Reference library.  (token, entry): `token` must appear in the body text. ──
REFS = [
    ("Breiman, 2001", "Breiman, L. (2001). Random forests. *Machine Learning, 45*(1), 5–32. https://doi.org/10.1023/A:1010933404324"),
    ("Clore et al., 2014", "Clore, J., Cios, K., DeShazo, J., & Strack, B. (2014). *Diabetes 130-US hospitals for years 1999–2008* [Data set]. UCI Machine Learning Repository. https://doi.org/10.24432/C5230J"),
    ("Hunter, 2007", "Hunter, J. D. (2007). Matplotlib: A 2D graphics environment. *Computing in Science & Engineering, 9*(3), 90–95. https://doi.org/10.1109/MCSE.2007.55"),
    ("Jencks et al., 2009", "Jencks, S. F., Williams, M. V., & Coleman, E. A. (2009). Rehospitalizations among patients in the Medicare fee-for-service program. *The New England Journal of Medicine, 360*(14), 1418–1428. https://doi.org/10.1056/NEJMsa0803563"),
    ("Kansagara et al.", "Kansagara, D., Englander, H., Salanitro, A., Kagen, D., Theobald, C., Freeman, M., & Kripalani, S. (2011). Risk prediction models for hospital readmission: A systematic review. *JAMA, 306*(15), 1688–1698. https://doi.org/10.1001/jama.2011.1515"),
    ("Kaufman et al., 2012", "Kaufman, S., Rosset, S., Perlich, C., & Stitelman, O. (2012). Leakage in data mining: Formulation, detection, and avoidance. *ACM Transactions on Knowledge Discovery from Data, 6*(4), Article 15. https://doi.org/10.1145/2382577.2382579"),
    ("Little & Rubin, 2019", "Little, R. J. A., & Rubin, D. B. (2019). *Statistical analysis with missing data* (3rd ed.). Wiley. https://doi.org/10.1002/9781119482260"),
    ("McIlvennan et al., 2015", "McIlvennan, C. K., Eapen, Z. J., & Allen, L. A. (2015). Hospital readmissions reduction program. *Circulation, 131*(20), 1796–1803. https://doi.org/10.1161/CIRCULATIONAHA.114.010270"),
    ("McKinney, 2010", "McKinney, W. (2010). Data structures for statistical computing in Python. In S. van der Walt & J. Millman (Eds.), *Proceedings of the 9th Python in Science Conference* (pp. 56–61). https://doi.org/10.25080/Majora-92bf1922-00a"),
    ("Obermeyer et al., 2019", "Obermeyer, Z., Powers, B., Vogeli, C., & Mullainathan, S. (2019). Dissecting racial bias in an algorithm used to manage the health of populations. *Science, 366*(6464), 447–453. https://doi.org/10.1126/science.aax2342"),
    ("Pedregosa et al., 2011", "Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., Blondel, M., Prettenhofer, P., Weiss, R., Dubourg, V., Vanderplas, J., Passos, A., Cournapeau, D., Brucher, M., Perrot, M., & Duchesnay, É. (2011). Scikit-learn: Machine learning in Python. *Journal of Machine Learning Research, 12*, 2825–2830."),
    ("Rubin, 2015", "Rubin, D. J. (2015). Hospital readmission of patients with diabetes. *Current Diabetes Reports, 15*(4), Article 17. https://doi.org/10.1007/s11892-015-0584-7"),
    ("Rudin, 2019", "Rudin, C. (2019). Stop explaining black box machine learning models for high stakes decisions and use interpretable models instead. *Nature Machine Intelligence, 1*(5), 206–215. https://doi.org/10.1038/s42256-019-0048-x"),
    ("Sandve et al., 2013", "Sandve, G. K., Nekrutenko, A., Taylor, J., & Hovig, E. (2013). Ten simple rules for reproducible computational research. *PLOS Computational Biology, 9*(10), Article e1003285. https://doi.org/10.1371/journal.pcbi.1003285"),
    ("Steyerberg, 2019", "Steyerberg, E. W. (2019). *Clinical prediction models: A practical approach to development, validation, and updating* (2nd ed.). Springer. https://doi.org/10.1007/978-3-030-16399-0"),
    ("Strack et al.", "Strack, B., DeShazo, J. P., Gennings, C., Olmo, J. L., Ventura, S., Cios, K. J., & Clore, J. N. (2014). Impact of HbA1c measurement on hospital readmission rates: Analysis of 70,000 clinical database patient records. *BioMed Research International, 2014*, Article 781670. https://doi.org/10.1155/2014/781670"),
    ("van Walraven et al., 2010", "van Walraven, C., Dhalla, I. A., Bell, C., Etchells, E., Stiell, I. G., Zarnke, K., Austin, P. C., & Forster, A. J. (2010). Derivation and validation of an index to predict early death or unplanned readmission after discharge from hospital to the community. *Canadian Medical Association Journal, 182*(6), 551–557. https://doi.org/10.1503/cmaj.091117"),
    ("Waskom, 2021", "Waskom, M. L. (2021). seaborn: Statistical data visualization. *Journal of Open Source Software, 6*(60), Article 3021. https://doi.org/10.21105/joss.03021"),
]

# ── numbering allocated by order of first mention ────────────────────────────
_TABLES, _FIGURES = {}, {}


def T(key):
    if key not in _TABLES:
        _TABLES[key] = len(_TABLES) + 1
    return _TABLES[key]


def F(key):
    if key not in _FIGURES:
        _FIGURES[key] = len(_FIGURES) + 1
    return _FIGURES[key]


_NUM_WORDS = {0: "zero", 1: "one", 2: "two", 3: "three", 4: "four",
              5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine"}


def nw(n):
    """APA 7 number style: spell out counts below 10, numerals from 10 up."""
    return _NUM_WORDS.get(int(n), f"{int(n):,}")


def pct(x, d=1):
    return f"{x * 100:.{d}f}%"


def nz(x, d=3):
    """APA style for statistics bounded by 1: no leading zero (keeps the sign)."""
    return f"{x:.{d}f}".replace("0.", ".", 1).replace("-", "−")


def words(text):
    return len(re.findall(r"\S+", text))


def rich(text):
    """Split '*italic*' markup into (text, italic) fragments for rc.body_rich."""
    return [(seg, i % 2 == 1) for i, seg in enumerate(text.split("*")) if seg]


# ── page estimate: wrap each paragraph with real Georgia metrics ─────────────
def n_lines(text, bold=False, first_indent=36.0):
    """Lines a paragraph occupies at Georgia 11 pt on a 6.5-in (468 pt) line."""
    from PIL import ImageFont
    base = Path("/System/Library/Fonts/Supplemental")
    font = ImageFont.truetype(str(base / ("Georgia Bold.ttf" if bold else "Georgia.ttf")), 1100)
    lines, cur, avail = 1, 0.0, 468.0 - first_indent
    space = font.getlength(" ") / 100
    for w in text.split():
        wl = font.getlength(w) / 100
        if cur and cur + space + wl > avail:
            lines, cur, avail = lines + 1, wl, 468.0
        else:
            cur = wl if not cur else cur + space + wl
    return lines


LINES_PER_PAGE = 25            # double-spaced Georgia 11 pt on a 9-in text block


def shot_cells():
    """Execution count of each screenshot cell, read from the executed notebook."""
    import nbformat
    nb = nbformat.read(HERE / NOTEBOOK, as_version=4)
    return {t.split(":", 1)[1]: c.execution_count for c in nb.cells
            for t in c.metadata.get("tags", []) if t.startswith("shot:")}


def build():
    _TABLES.clear(); _FIGURES.clear()
    R = json.load(open(HERE / "outputs" / "results.json"))
    cell = shot_cells()
    H, CV, B, TU = R["holdout"], R["cv"], R["boot"], R["tuning"]
    lr, rf = H["Logistic regression"], H["Random forest"]
    rule, dummy = H["Prior-admissions heuristic"], H["Dummy (prior rate)"]
    lc, ledger, SG = R["lift_curve"], R["ledger"], R["subgroups"]
    inp, dis = R["rate_by_inpatient"], R["rate_by_discharge"]
    tlr, trf = TU["Logistic regression"], TU["Random forest"]
    sec_lines, sec_words, body_text = {}, {}, []

    # Results-dependent claims made in the prose.  If a rerun changes one, the build
    # fails and the sentence must be revised rather than silently becoming false.
    g_f, g_m = SG["gender"]["Female"], SG["gender"]["Male"]
    r_aa, r_ca = SG["race"]["AfricanAmerican"], SG["race"]["Caucasian"]
    a_old, a_young = SG["age_group"]["65+"], SG["age_group"]["<65"]
    rs = R["random_split_auc"]
    rf_tuned_beats_lr = trf["test_auc"] > tlr["test_auc"]
    tuned_diff_sig = not (B["tuned_rf_minus_lr_lo"] < 0 < B["tuned_rf_minus_lr_hi"])
    CLAIMS = [
        (B["gain_lo"] > 0, "LR beats the heuristic (CI excludes 0)"),
        (B["gain_rf_lo"] > 0, "LR beats the default forest (CI excludes 0)"),
        (rf["recall"] < 0.05 and abs(rf["accuracy"] - dummy["accuracy"]) < 0.01,
         "default forest: near-zero recall at dummy-level accuracy"),
        (B["lift10_diff_lo"] < 0 < B["lift10_diff_hi"], "top-decile lift tie with heuristic"),
        (lc["20%"]["lr"] > lc["20%"]["rule"], "LR ahead of heuristic at 20% capacity"),
        (all(abs(rs[k] - H[k]["roc_auc"]) < 0.01 for k in rs), "random split inflation < .01"),
        (trf["test_auc"] - rf["roc_auc"] > 0.01, "tuning improves the forest by > .01 AUC"),
        (abs(tlr["test_auc"] - lr["roc_auc"]) < 0.005, "tuning barely moves LR"),
        (abs(g_f["base_rate"] - g_m["base_rate"]) < 0.01
         and abs(g_f["flag_rate"] - g_m["flag_rate"]) > 0.02, "gender flag gap at equal base rates"),
        (abs(r_aa["auc"] - r_ca["auc"]) < 0.02, "two largest race groups have similar AUC"),
        (a_young["auc"] - a_old["auc"] > 0.05, "weaker discrimination at 65+"),
        (min(R["skew_counts"][c] for c in ["number_outpatient", "number_emergency",
                                           "number_inpatient"]) > 2,
         "utilization counts strongly right-skewed"),
    ]
    failed = [msg for ok, msg in CLAIMS if not ok]
    if failed:
        raise SystemExit(f"ERROR: narrative claims no longer hold, revise the text: {failed}")

    doc = rc.new_doc()
    rc.add_page_numbers(doc)

    def para(text, indent=True):
        if "*" in text:
            rc.body_rich(doc, rich(text), indent=indent)
        else:
            rc.body(doc, text, indent=indent)
        plain = text.replace("*", "")
        body_text.append(plain)
        return plain

    def section(title, paragraphs, after=None):
        """Level-1 section.  Items are paragraphs or ("h2", heading); `after` maps an
        item index to a callable that adds the exhibits first mentioned there."""
        rc.heading(doc, title, 1)
        lines, wc = n_lines(title, bold=True, first_indent=0), 0
        for i, item in enumerate(paragraphs):
            if isinstance(item, tuple):
                rc.heading(doc, item[1], 2)
                lines += n_lines(item[1], bold=True, first_indent=0)
            else:
                plain = para(item)
                lines += n_lines(plain)
                wc += words(plain)
            if after and i in after:
                after[i]()
        sec_lines[title], sec_words[title] = lines, wc

    # ══ Title page and abstract ══════════════════════════════════════════════
    rc.title_page(doc, TITLE, SUBTITLE)

    rc.heading(doc, "Abstract", 1)
    abstract = (
        f"Thirty-day readmissions are costly, penalized, and partly preventable, and "
        f"patients with diabetes are disproportionately affected. This deliverable builds "
        f"the foundation for ranking diabetic inpatients by readmission risk at discharge. "
        f"Using {R['n_raw']:,} encounters from 130 U.S. hospitals (Clore et al., 2014), the "
        f"data were audited, cleaned, and engineered into a leakage-safe pipeline, then "
        f"split by patient because {pct(R['share_enc_repeat_patients'], 0)} of encounters "
        f"belong to repeat patients. A logistic regression reached a held-out ROC-AUC of "
        f"{nz(lr['roc_auc'])}, outperforming a default random forest and a prior-admissions "
        f"heuristic, although the heuristic matched it among the highest-risk tenth. A "
        f"preliminary grid search scored on ROC-AUC rather than accuracy raised the "
        f"forest to {nz(trf['test_auc'])}. Discrimination was weaker for patients 65 and "
        f"older, and women were flagged more often than men at equal risk. Deliverable 2 "
        f"will calibrate scores, set capacity-based thresholds, and audit fairness."
    )
    rc.body(doc, abstract, indent=False)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = rc.LINE
    p.paragraph_format.first_line_indent = rc.Inches(0.5)
    rc._run(p, "Keywords: ", italic=True)
    rc._run(p, "hospital readmission, diabetes, logistic regression, random forest, "
               "grouped validation, algorithmic fairness")
    doc.add_page_break()

    rc.center_line(doc, TITLE, bold=True)

    # ══ 1. Introduction ══════════════════════════════════════════════════════
    section("Introduction and Problem Framing", [
        "A readmission within 30 days hurts two groups at once. Patients face another "
        "hospital stay, and hospitals pay for it under the Hospital "
        "Readmissions Reduction Program, which penalizes excess readmissions (McIlvennan et "
        "al., 2015). The problem is large: nearly one in five Medicare patients is "
        "readmitted within 30 days, at an estimated $17.4 billion a year (Jencks et al., "
        "2009), and patients with diabetes are at higher risk than most (Rubin, 2015). "
        "Hospitals try to prevent these returns with follow-up calls and medication "
        "reconciliation, but such programs can reach only some patients, so the real "
        "question is whom to contact first. This project therefore asks: using only "
        "information available at discharge, can routinely collected encounter data rank "
        "diabetic inpatients by 30-day readmission risk well enough to decide who receives "
        "follow-up? We judge success by ranking, not accuracy. Published readmission models "
        "discriminate only modestly (Kansagara et al., 2011), so a model is useful if it "
        "beats a simple clinical heuristic and concentrates readmissions at the top of its "
        "list.",
    ])

    # ══ 2. Dataset ═══════════════════════════════════════════════════════════
    f_audit, f_num, f_rates, f_pipe = F("audit"), F("numeric"), F("rates"), F("pipeline")
    t_feat, t_ledger = T("features"), T("ledger")
    sk = R["skew_counts"]

    def ex_audit():
        rc.add_fig(doc, FIGDIR / "fig_audit.png", f_audit,
                   "Data Audit: Missing Values, Outcome Classes, and Repeat Patients",
                   note=(f"Panel (a) shows the share of {R['n_raw']:,} raw encounters coded "
                         f"“?”; red bars exceed 30%. Panel (b) is a seaborn count plot of "
                         f"the three-class source outcome; red marks the target class. "
                         f"Panel (c) counts patients by number of encounters on a log scale."),
                   width=6.5)

    def ex_numeric():
        rc.add_fig(doc, FIGDIR / "fig_numeric.png", f_num,
                   "Distributions of Count Features by Outcome, and Their Correlations",
                   note=("Panels (a)–(d) are density-scaled histograms for readmitted and "
                         "non-readmitted encounters. Panel (e) shows Spearman rank "
                         "correlations, used because the counts are skewed; the last row "
                         "is each feature's correlation with the outcome."), width=6.5)

    def ex_rates():
        rc.add_fig(doc, FIGDIR / "fig_rates.png", f_rates,
                   "Observed 30-Day Readmission Rates by Encounter Characteristic",
                   note=(f"Unadjusted rates for the {R['n_clean']:,} analyzed encounters "
                         f"with 95% Wilson confidence intervals. The dashed line marks the "
                         f"overall rate of {pct(R['prevalence'])}."), width=6.2)

    def ex_tables():
        rc.add_table(
            doc, t_feat, "Selected Target and Features, With Preprocessing Treatment",
            ["Group", "Variables", "Treatment"],
            [
                ["Target", "Readmitted (<30 days, >30 days, no)",
                 f"Binary: <30 days = 1 ({pct(R['prevalence'])}); source column removed"],
                ["Prior utilization", "Outpatient, emergency, and inpatient visits in the prior year",
                 "log(1 + count), standardized"],
                ["Stay intensity", "Length of stay; counts of lab tests, procedures, "
                 "medications, and diagnoses", "Standardized"],
                ["Demographic", "Age (10-year band)", "Band midpoint, standardized"],
                ["Administrative", "Admission type, admission source, discharge disposition",
                 "Integer codes mapped to four or five categories; null and unmapped codes "
                 "pooled as unknown"],
                ["Diagnoses", "Primary, secondary, and tertiary ICD-9 codes",
                 f"{R['n_icd9_codes']} codes grouped into nine clinical groups (Strack et al., 2014)"],
                ["Laboratory", "HbA1c and maximum serum glucose results",
                 "“None” retained as a not-measured category"],
                ["Specialty", "Admitting physician specialty",
                 f"Missing ({pct(R['missing_share']['medical_specialty'])}) kept as a level; "
                 f"levels under 1% pooled"],
                ["Medications", f"{len(R['kept_drugs'])} of {R['n_drugs']} diabetes drugs; "
                 f"regimen change; any diabetes medication",
                 "One-hot encoded; count of dose changes engineered"],
                ["Excluded", f"Weight; encounter ID; {R['n_drugs'] - len(R['kept_drugs'])} "
                 f"rarely used drugs",
                 f"{pct(R['missing_share']['weight'])} missing; identifier; used in under 1% "
                 f"of encounters"],
                ["Audit only", "Race, gender, payer code",
                 "Held out of predictors; used for subgroup and fairness checks"],
                ["Grouping", "Patient number", "Used only to split data by patient"],
            ],
            col_widths=[17, 40, 43],
            note=(f"Final model matrix: {R['n_num']} numeric and {R['n_cat']} categorical "
                  f"inputs, expanded to {R['n_model_cols']} columns. One-hot encoding and "
                  f"scaling are fit on training data only."),
            fs=9)
        rc.add_table(
            doc, t_ledger, "Cleaning Ledger: Row-Level Steps and Their Effect",
            ["Step", "Encounters", "Patients", "30-day rate"],
            [[s["step"], f"{s['encounters']:,}", f"{s['patients']:,}", pct(s["rate_30d"], 2)]
             for s in ledger],
            col_widths=[46, 18, 18, 18],
            note=("Deaths and hospice discharges (disposition codes 11, 13, 14, and 19–21) "
                  "cannot be followed by a readmission and are removed. No exact duplicate "
                  "rows were found."),
            fs=9.5)

    def ex_pipe():
        rc.add_fig(doc, FIGDIR / "shot_pipeline.png", f_pipe,
                   "Colab Notebook Screenshot: Feature Lists, Grouped Split, and Pipeline",
                   note=(f"Cell [{cell['pipeline']}] of the notebook (Appendix A). The "
                         f"assertion verifies that no patient appears in both the training "
                         f"and test sets."), width=6.0)

    section("Dataset Exploration and Preprocessing", [
        f"The analysis uses the Diabetes 130-US Hospitals dataset (Clore et al., 2014): "
        f"{R['n_raw']:,} inpatient encounters from {R['n_patients_raw']:,} patients at 130 "
        f"U.S. hospitals between 1999 and 2008. Each encounter is a stay of one to 14 days "
        f"with a diabetes diagnosis, laboratory testing, and medication (Strack et al., "
        f"2014). Its {R['n_cols_raw']} columns cover demographics, admission and discharge "
        f"codes, prior-year utilization, laboratory and procedure counts, three ICD-9 "
        f"diagnoses, HbA1c and glucose results, and {R['n_drugs']} diabetes medications. "
        f"The target is readmission within 30 days, coded 1 against both later readmission "
        f"and none, because only early returns trigger penalties; it occurs in "
        f"{pct(R['target_3class']['<30'])} of encounters (Figure {f_audit}).",

        f"The audit shaped the cleaning. No exact duplicates were found. Missing values were "
        f"treated column by column rather than forward-filled, because adjacent rows belong "
        f"to different patients: weight ({pct(R['missing_share']['weight'])} missing) was "
        f"dropped, and medical specialty "
        f"({pct(R['missing_share']['medical_specialty'])} missing) became an explicit "
        f"category, because an unrecorded specialty may signal a different admission "
        f"pathway and is unlikely to be missing at random (Little & Rubin, 2019). The file "
        f"also writes “None” for a test not performed, which pandas (McKinney, 2010) "
        f"silently converts to missing by default; the loader preserves it as a category. "
        f"Finally, {pct(R['share_enc_repeat_patients'])} of encounters belong to repeat "
        f"patients, so encounters are not independent and must be split by patient.",

        f"Figure {f_num}, drawn with seaborn (Waskom, 2021), shows that the utilization "
        f"counts are strongly right-skewed (prior emergency visits: skew = "
        f"{sk['number_emergency']:.1f}), so they enter the model as log(1 + count), which cut "
        f"the skew of prior inpatient visits from {R['skew_inpatient']:.2f} to "
        f"{R['skew_log_inpatient']:.2f}. No two features are "
        f"redundant, the strongest pair being {R['corr_max_pair'][0].lower()} and "
        f"{R['corr_max_pair'][1].lower()} (ρ = {nz(R['corr_max'], 2)}), and no single "
        f"feature correlates strongly with the outcome (largest ρ = "
        f"{nz(max(R['corr_outcome'].values()), 2)}), an early sign that discrimination "
        f"will be modest. Figure {f_rates} shows clearer gradients: the readmission rate "
        f"rises from {pct(inp['0'])} with no prior-year admissions to {pct(inp['5+'])} with "
        f"five or more, and discharge to another facility ({pct(dis['Facility transfer'])}) "
        f"exceeds discharge home ({pct(dis['Home'])}). Encounters with a measured HbA1c "
        f"were readmitted less often ({pct(R['rate_a1c_measured'])} vs. "
        f"{pct(R['rate_a1c_not'])}, *p* < .001), replicating Strack et al. (2014), although "
        f"measurement more plausibly marks attentive care than causes the difference.",

        f"Table {t_feat} lists the selected features and their treatment, and Table "
        f"{t_ledger} logs each row-level step. Features were kept when available by "
        f"discharge and clinically motivated or associated with the outcome. Deaths and "
        f"hospice discharges were removed because readmission is impossible, leaving "
        f"{R['n_clean']:,} encounters from {R['n_patients_clean']:,} patients. The "
        f"{R['n_icd9_codes']} ICD-9 codes were collapsed into nine groups so that rare codes "
        f"do not each demand a parameter. Race, gender, and payer were excluded from the "
        f"predictors and reserved for fairness checks. One-hot encoding and scaling were "
        f"fit after the split, inside a scikit-learn pipeline (Pedregosa et al., 2011), "
        f"because fitting them on all rows leaks test information into training (Kaufman "
        f"et al., 2012), as Figure {f_pipe} shows.",
    ], after={0: ex_audit, 2: lambda: (ex_numeric(), ex_rates()),
              3: lambda: (ex_tables(), ex_pipe())})

    # ══ 3. Initial model ═════════════════════════════════════════════════════
    t_res, f_models, f_perf, f_coef = T("results"), F("models"), F("performance"), F("coef")
    cvl, cvr = CV["Logistic regression"], CV["Random forest"]

    def ex_results():
        def row(name, d, lift_key):
            c = CV[name]
            lifts = ([f"{lc[q][lift_key]:.2f}" for q in ("10%", "20%")] if lift_key
                     else ["1.00", "1.00"])          # a constant score has no lift
            return [name, f"{nz(c['auc_mean'])} ({nz(c['auc_sd'])})", nz(d["roc_auc"]),
                    nz(d["pr_auc"]), nz(d["accuracy"]), nz(d["recall"]), nz(d["precision"]),
                    pct(d["flagged"]), *lifts]
        rc.add_table(
            doc, t_res, "Initial Model Performance Against Two Reference Scores",
            ["Model", "CV ROC-AUC M (SD)", "Test ROC-AUC", "PR-AUC", "Accuracy", "Recall",
             "Precision", "Flagged", "Lift, top 10%", "Lift, top 20%"],
            [row("Logistic regression", lr, "lr"), row("Random forest", rf, "rf"),
             row("Prior-admissions heuristic", rule, "rule"),
             row("Dummy (prior rate)", dummy, None)],
            col_widths=[20, 11, 9, 8, 9, 8, 9, 9, 8, 8],
            note=(f"CV = five-fold stratified group cross-validation on "
                  f"{R['n_train']:,} training encounters; test metrics use "
                  f"{R['n_test']:,} encounters from {R['n_test_patients']:,} patients "
                  f"absent from training. Threshold metrics use each model's default "
                  f"decision (0.5), at least one prior admission for the heuristic, and no "
                  f"flags for the dummy. Lift is the readmission rate among the "
                  f"highest-risk share divided by the overall rate. The random forest uses "
                  f"default settings."),
            fs=8)
        rc.add_fig(doc, FIGDIR / "shot_models.png", f_models,
                   "Colab Notebook Screenshot: Training Both Models and Their Classification Reports",
                   note=(f"Cell [{cell['models']}] of the notebook. Reports use the default "
                         f"0.5 threshold on the patient-disjoint test set."), width=5.6)
        rc.add_fig(doc, FIGDIR / "fig_performance.png", f_perf,
                   "Discrimination and Confusion Matrices of the Initial Models",
                   note=(f"Panels (a) and (b) compare both models with the prior-admissions "
                         f"heuristic on the test set; the dotted line in (b) is the "
                         f"prevalence baseline ({nz(R['prev_test'])}). Panels (c) and (d) "
                         f"are seaborn heatmaps of the confusion matrices at the default "
                         f"threshold."), width=6.5)

    def ex_coef():
        rc.add_fig(doc, FIGDIR / "fig_coefficients.png", f_coef,
                   "Largest Logistic Regression Effects, as Odds Ratios",
                   note=("Numeric effects are per standard deviation. Categories are one-hot "
                         "coded without a reference level and shrunk by the L2 penalty, so "
                         "their odds ratios indicate direction and rank rather than adjusted "
                         "effects."), width=5.4)

    t_tune, f_tune = T("tuning"), F("tuning")

    def ex_tuning():
        def prm(d):
            return ", ".join(f"{k} = {v}" for k, v in d.items())
        rc.add_table(
            doc, t_tune, "Preliminary Grid Search: Default Versus Tuned Models",
            ["Model", "Grid searched", "Best setting", "Grouped CV ROC-AUC",
             "Test ROC-AUC, default → tuned", "Test PR-AUC, tuned", "Lift, top 10%, tuned"],
            [["Logistic regression", "C ∈ {0.01, 0.1, 1, 10}", prm(tlr["best_params"]),
              nz(tlr["cv_auc"]), f"{nz(lr['roc_auc'])} → {nz(tlr['test_auc'])}",
              nz(tlr["test_pr_auc"]), f"{tlr['lift_top10']:.2f}"],
             ["Random forest", "n_estimators ∈ {100, 200}; max_depth ∈ {10, 20, None}",
              prm(trf["best_params"]), nz(trf["cv_auc"]),
              f"{nz(rf['roc_auc'])} → {nz(trf['test_auc'])}", nz(trf["test_pr_auc"]),
              f"{trf['lift_top10']:.2f}"]],
            col_widths=[16, 24, 18, 11, 13, 9, 9],
            note=("GridSearchCV with three patient-grouped, stratified folds and ROC-AUC "
                  "scoring; the forest grid follows the course hints. Test metrics use the "
                  "same patient-disjoint test set as Table 3."),
            fs=8.5)
        rc.add_fig(doc, FIGDIR / "shot_tuning.png", f_tune,
                   "Colab Notebook Screenshot: Grid Search Scored on ROC-AUC With Grouped Folds",
                   note=f"Cell [{cell['tuning']}] of the notebook.", width=6.0)

    gap_rf = lr["roc_auc"] - rf["roc_auc"]
    if rf_tuned_beats_lr and tuned_diff_sig:
        tuned_sentence = (f"The tuned forest now exceeds the logistic regression "
                          f"(difference 95% CI [{nz(B['tuned_rf_minus_lr_lo'])}, "
                          f"{nz(B['tuned_rf_minus_lr_hi'])}]), so Deliverable 2 must weigh "
                          f"that gain against the forest's opacity.")
    else:
        tuned_sentence = (f"The tuned forest and the logistic regression are statistically "
                          f"indistinguishable (difference 95% CI "
                          f"[{nz(B['tuned_rf_minus_lr_lo'])}, {nz(B['tuned_rf_minus_lr_hi'])}]), "
                          f"so the interpretable model remains the working choice "
                          f"(Rudin, 2019).")

    section("Initial Model Development", [
        ("h2", "Model Selection and Initial Results"),
        f"The initial model is an L2-regularized logistic regression with balanced class "
        f"weights. It is the reference standard for clinical prediction (Steyerberg, 2019), "
        f"its coefficients can be inspected when a score allocates care (Rudin, 2019), and "
        f"established readmission indices such as LACE are themselves additive risk scores "
        f"(van Walraven et al., 2010). A random forest (Breiman, 2001) at default settings "
        f"serves as the nonlinear comparison the course guidance suggests. Data were split "
        f"75/25 by patient, five-fold stratified group cross-validation was run on the "
        f"training set, and a prior-rate dummy and a prior-admissions heuristic anchor the "
        f"results.",

        f"Table {t_res} and Figures {f_models} and {f_perf} report the results. The logistic "
        f"regression reached a cross-validated ROC-AUC of {nz(cvl['auc_mean'])} (*SD* = "
        f"{nz(cvl['auc_sd'])}) and a test AUC of {nz(lr['roc_auc'])} (95% CI "
        f"[{nz(B['auc_lo'])}, {nz(B['auc_hi'])}]), typical of published models (Kansagara "
        f"et al., 2011). The default forest ranked worse by {nz(gap_rf)} and exposed the "
        f"accuracy trap: its {pct(rf['accuracy'])} accuracy equals the dummy's, yet it "
        f"caught {pct(rf['recall'])} of readmissions, against {pct(lr['recall'], 0)} for "
        f"the logistic regression. The model beat the heuristic by "
        f"{nz(lr['roc_auc'] - rule['roc_auc'])} AUC (95% CI [{nz(B['gain_lo'])}, "
        f"{nz(B['gain_hi'])}]) but tied it in the top risk decile (lift "
        f"{lc['10%']['lr']:.2f} vs. {lc['10%']['rule']:.2f}) and pulled ahead only at 20% "
        f"capacity ({lc['20%']['lr']:.2f} vs. {lc['20%']['rule']:.2f}). Prior admissions "
        f"and discharge to a facility were among the largest effects (Figure {f_coef}). A "
        f"random row split moved AUC by under .01 for both models, so patient overlap "
        f"biases little here, but the grouped split is kept because it answers the "
        f"deployment question of performance on new patients.",

        ("h2", "Preliminary Tuning"),
        f"Following the course hints, GridSearchCV tuned both models (Table {t_tune}, "
        f"Figure {f_tune}), with two corrections: folds were grouped by patient, and "
        f"scoring used ROC-AUC, because accuracy rewards the do-nothing behavior shown "
        f"above. Limiting tree depth raised the forest's test AUC from {nz(rf['roc_auc'])} "
        f"to {nz(trf['test_auc'])}, whereas the logistic regression barely moved "
        f"({nz(lr['roc_auc'])} to {nz(tlr['test_auc'])}), because its discrimination is "
        f"nearly flat across the penalty grid. {tuned_sentence} Class weighting also "
        f"inflated the mean predicted "
        f"risk to {nz(R['mean_pred_prob'])} against an observed {nz(R['prev_test'])}, so "
        f"Deliverable 2 will calibrate scores and set thresholds from program capacity.",
    ], after={2: lambda: (ex_results(), ex_coef()), 4: ex_tuning})

    # ══ 4. Ethics and real-world application ═════════════════════════════════
    t_sub = T("subgroups")
    per_1000 = R["prev_test"] * 1000
    caught = lc["10%"]["lr"] * R["prev_test"] * 100

    def ex_subgroups():
        rows = []
        for col, label in [("race", "Race"), ("gender", "Gender"), ("age_group", "Age")]:
            for level, s in SG[col].items():
                name = {"AfricanAmerican": "African American"}.get(level, level)
                rows.append([f"{label}: {name}", f"{int(s['n']):,}", pct(s["base_rate"]),
                             nz(s["auc"]), pct(s["flag_rate"]), nz(s["recall"])])
        rc.add_table(
            doc, t_sub, "Preliminary Subgroup Check of the Logistic Regression on the Test Set",
            ["Group", "n", "Readmission rate", "ROC-AUC", "Flagged", "Recall"], rows,
            col_widths=[30, 12, 16, 12, 14, 12],
            note=("Flags use the default 0.5 threshold. Groups with fewer than 30 "
                  "readmissions are omitted because their estimates are unstable. Race, "
                  "gender, and age group are not model inputs except age, which enters as a "
                  "band midpoint."),
            fs=9)

    section("Ethical Considerations and Real-World Application", [
        f"In practice the model would support, not replace, discharge planning. Each day "
        f"the care-transition nurses would receive that day's discharges ranked by risk and "
        f"call patients from the top of the list for as long as capacity allows. At 10% "
        f"capacity, per 1,000 discharges they would reach about {caught:.0f} of the "
        f"{per_1000:.0f} patients who will be readmitted, against about "
        f"{per_1000 / 10:.0f} by random selection. The ethical concern we consider most "
        f"serious is the age gap in Table {t_sub}: discrimination was clearly weaker for "
        f"patients 65 and older (AUC {nz(a_old['auc'])} vs. {nz(a_young['auc'])}), yet they "
        f"are the Medicare population the penalty program targets, so the model is least "
        f"reliable for the patients it most needs to serve. Two other fairness issues need "
        f"watching. Women were flagged more often than men ({pct(g_f['flag_rate'])} vs. "
        f"{pct(g_m['flag_rate'])}) at nearly equal readmission rates, although the two "
        f"largest race groups showed nearly identical discrimination (AUC "
        f"{nz(r_aa['auc'])} and {nz(r_ca['auc'])}). And prior admissions, the strongest "
        f"predictor, measures access to care as well as need, so patients who struggle to "
        f"reach a hospital may be under-flagged (Obermeyer et al., 2019); excluding race and "
        f"payer as inputs does not remove such proxies. Deliverable 2 will test the age and "
        f"gender gaps for miscalibration. Three considerations also apply: clinicians can review "
        f"the coefficients in Figure {f_coef}; errors are asymmetric, since a missed patient "
        f"loses support whereas a false alarm costs a phone call, which favors recall within "
        f"capacity; and the public file holds no names or dates, while a deployed version "
        f"would run under HIPAA.",
    ], after={0: ex_subgroups})

    # ══ 5. Team ══════════════════════════════════════════════════════════════
    t_team = T("team")

    def ex_team():
        rc.add_table(doc, t_team, "Team Roles: Equal Leadership That Rotates Between Deliverables",
                     ["Member", "Student ID", "Leads in Deliverable 1", "Reviews in Deliverable 1",
                      "Leads in Deliverable 2"],
                     [list(m) for m in TEAM], col_widths=[17, 9, 28, 22, 24], fs=9,
                     note=(f"Each member leads three rubric criteria and reviews the other's "
                           f"three (Appendix A, Table A1); writing is shared, and both approve "
                           f"the final report. Repository: {REPO_URL}"))

    section("Team Collaboration Process", [
        f"The two members carry equal shares: each leads three rubric criteria and reviews "
        f"the other's three (Table {t_team}). In this deliverable, Chinthaluri led data "
        f"exploration, preprocessing, modeling, and preliminary tuning, while Abburi led "
        f"problem framing, ethical analysis, and the real-world application and "
        f"independently re-ran the notebook in Google Colab to confirm every reported "
        f"number. The roles rotate in Deliverable 2, where Abburi leads optimization and "
        f"Chinthaluri leads the fairness audit, so each member leads the core modeling once. "
        f"The code is tracked in a shared GitHub repository: each task is built on its own "
        f"branch, assigned as an issue, and merged only after the other member approves the "
        f"pull request, so the history records both authorship and review. The notebook, "
        f"built with pandas, Matplotlib (Hunter, 2007), seaborn, and scikit-learn, opens in "
        f"Colab from that repository. Decisions are logged with proposer and reviewer, the "
        f"members meet weekly, and because the report is regenerated from the notebook's "
        f"results file (Sandve et al., 2013), either member's change reaches every table "
        f"automatically.",
    ], after={0: ex_team})

    # ══ References and Appendix A ════════════════════════════════════════════
    rc.references_section(doc, [e for _, e in REFS])

    doc.add_page_break()
    rc.heading(doc, "Appendix A", 1)
    rc.heading(doc, "Google Colab Notebook, Rubric Map, and Course-Hints Map", 1)
    p = rc.body(doc, "Notebook link (view access for the instructor): ", indent=False)
    if COLAB_URL:
        rc.hyperlink(p, COLAB_URL)
    else:
        rc._run(p, "[PASTE COLAB SHARE LINK]", bold=True)
    rc.body(doc, (f"The notebook ({NOTEBOOK}) is self-contained: on first run it downloads "
                  f"the UCI archive, then executes top to bottom and writes every figure "
                  f"and reported number. Table A1 maps each rubric criterion to where this "
                  f"report and the notebook address it, and Table A2 shows how each course "
                  f"hint was followed, including the three applied in corrected form."),
            indent=True)
    a1_rows = [
        ["Problem definition", "Introduction and Problem Framing",
         "Stakeholders, penalty context, and a capacity-limited question"],
        ["Dataset exploration", "Dataset Exploration and Preprocessing",
         f"Figures {f_audit}–{f_rates}; Tables {t_feat} and {t_ledger}; notebook Sections 2–6"],
        ["Model development", "Model Selection and Initial Results",
         f"Two justified models and two references; Table {t_res}; Figures "
         f"{f_models}–{f_coef}"],
        ["Optimization and evaluation", "Preliminary Tuning",
         f"Grouped GridSearchCV on ROC-AUC; Table {t_tune}; Figure {f_tune}; full "
         f"optimization in Deliverable 2"],
        ["Ethics and impact", "Ethical Considerations and Real-World Application",
         f"Proxy bias, subgroup check (Table {t_sub}), transparency, error costs, privacy"],
        ["Real-world application", "Ethical Considerations and Real-World Application",
         "Daily ranked discharge list; 1,000-discharge worked example"],
        ["Teamwork and documentation", "Team Collaboration Process",
         f"Table {t_team}; pull-request reviews and Git history; decision log; README"],
        ["Writing and structure", "Whole report",
         "APA 7th edition; build checks for citations, callouts, and spelling"]]
    rc.add_table(
        doc, "A1", "Project Rubric Criteria, Where Each Is Addressed, and Who Leads It",
        ["Criterion", "Where in the report", "Evidence", "Lead / reviewer"],
        [r + [" / ".join(LEADS[r[0]])] for r in a1_rows],
        col_widths=[18, 26, 38, 18], fs=8.5)
    rc.add_table(
        doc, "A2", "Course Hints and How the Notebook Follows Them",
        ["Hint", "Notebook section", "How it is applied"],
        [["1. Setup and imports", "1",
          "pandas, NumPy, Matplotlib, seaborn, scikit-learn, GridSearchCV; warnings suppressed"],
         ["2. Uploading or accessing data", "2",
          "Downloaded by URL, with files.upload() as fallback"],
         ["3. Exploration and cleaning", "3–4, 6",
          "shape, info(), describe(), countplot, histograms, heatmap, drop_duplicates(); "
          "missing values handled per column instead of forward fill, which would copy "
          "values between different patients"],
         ["4. Feature engineering and preprocessing", "5, 7",
          "One-hot encoding and StandardScaler fit after the split inside a Pipeline, "
          "not on the full data, to prevent leakage"],
         ["5. Train-test split", "7", "75/25 with random_state = 42, grouped by patient"],
         ["6. Model training and evaluation", "8–11",
          "Logistic regression and RandomForestClassifier; classification_report; "
          "confusion-matrix heatmaps"],
         ["7. Hyperparameter tuning", "12",
          "GridSearchCV with the hint's forest grid, scored on ROC-AUC rather than accuracy"],
         ["8. Ethical considerations", "13",
          "Markdown cell answering the hint's questions, plus a subgroup check"]],
        col_widths=[26, 14, 60], fs=9)

    out = HERE / OUT_NAME
    doc.core_properties.title = TITLE
    doc.save(out)

    # ── verification ─────────────────────────────────────────────────────────
    full = "\n".join(p.text for p in doc.paragraphs)
    for tbl in doc.tables:
        for row in tbl.rows:
            full += "\n" + " ".join(c.text for c in row.cells)
    body = "\n".join(body_text)
    n_abs = words(abstract)
    print(f"  saved: {out.name}")
    print(f"  claims re-checked against results: {len(CLAIMS)} OK")
    print(f"  abstract: {n_abs} words (<=150) -> {'OK' if n_abs <= 150 else 'TOO LONG'}")
    errors = []
    for sec, target in PAGE_BUDGET.items():
        pages = sec_lines[sec] / LINES_PER_PAGE
        ok = target * (1 - TOL) <= pages <= target * (1 + TOL)
        errors += [] if ok else [f"length: {sec}"]
        print(f"  {sec}: {sec_words[sec]} words, {pages:.2f} pages "
              f"(target ~{target}) -> {'OK' if ok else 'OUT OF RANGE'}")
    total = sum(sec_lines.values()) / LINES_PER_PAGE
    print(f"  narrative total: {sum(sec_words.values())} words, {total:.2f} pages")

    uncited = [t for t, _ in REFS if t not in body]
    british = re.findall(
        r"\b\w*(?:ise|ised|ises|ising|isation|isations|our|ourite|labelled|"
        r"artefact\w*|behaviour\w*|judgement|analyses|modelling|whilst|amongst)\b",
        full, flags=re.I)
    allow = {"noise", "raise", "raised", "wise", "otherwise", "rise", "rises", "precise", "four",
             "hour", "your", "our", "pairwise", "promise", "surprise", "comprises", "revise",
             "advise", "expertise", "exercise"}
    british = sorted({w for w in british if w.lower() not in allow})
    expanded = re.sub(r"\b(Table|Figure)s (\d+) and (\d+)\b",
                      lambda m: f"{m.group(1)} {m.group(2)} {m.group(1)} {m.group(3)}", body)
    missing_callout = [f"{lab} {i}" for lab, n in [("Table", len(_TABLES)), ("Figure", len(_FIGURES))]
                       for i in range(1, n + 1) if not re.search(rf"\b{lab} {i}\b", expanded)]
    order = list(dict.fromkeys(int(m) for m in re.findall(r"\bFigure (\d+)", expanded)))
    t_order = list(dict.fromkeys(int(m) for m in re.findall(r"\bTable (\d+)", expanded)))
    spacing = re.findall(r"[^\n] {2,}[^\n]|\S +[,;]|\S +\.(?!\d)", full)
    placeholders = sorted(set(re.findall(r"\[[A-Z][A-Z :,.\-0-9]+[^\]]*\]", full)))

    print(f"  references: {len(REFS)} | uncited in body: {uncited or 'none'}")
    print(f"  British spellings: {british or 'none'}")
    print(f"  exhibits not called out in body: {missing_callout or 'none'}")
    print(f"  figures first mentioned in order: {order} -> {'OK' if order == sorted(order) else 'NO'}")
    print(f"  tables first mentioned in order: {t_order} -> {'OK' if t_order == sorted(t_order) else 'NO'}")
    print(f"  spacing slips: {spacing or 'none'}")
    print(f"  figures: {len(_FIGURES)} | tables: {len(_TABLES)} (+2 in Appendix A)")
    pending = [t for t, done in TEAM_TASKS.items() if not done]
    if pending:
        print(f"  WARNING team tasks described in the report but not yet confirmed "
              f"({len(pending)}): see TEAM_TASKS.md")
        for t in pending:
            print(f"    - {t}")
    if placeholders or not COLAB_URL:
        print(f"  WARNING placeholders to fill before submission: "
              f"{placeholders + ([] if COLAB_URL else ['COLAB_URL'])}")
    if british or missing_callout or spacing or order != sorted(order) or t_order != sorted(t_order):
        errors.append("mechanics")
    if n_abs > 150:
        errors.append("abstract length")
    if uncited:
        errors.append(f"uncited {uncited}")
    if errors:
        raise SystemExit(f"ERROR: checks failed: {errors}")
    return out


if __name__ == "__main__":
    build()
