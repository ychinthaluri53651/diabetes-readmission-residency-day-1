# Team Tasks — Residency Project (PhDAI-733-M20)

| Member | Student ID | GitHub | Leads in Deliverable 1 | Leads in Deliverable 2 |
|---|---|---|---|---|
| Yogananda Atreya Chinthaluri | 53651 | `ychinthaluri53651` | Data audit and cleaning, feature engineering, modeling, preliminary tuning | Fairness audit and mitigation, cost and capacity analysis |
| Anil Kumar Abburi | 53405 | `Anil9618` | Introduction, ethical analysis, deployment scenario, Colab reproduction, APA proofread | Model tuning, boosting, calibration, and thresholds |

**Equal shares.** Each member leads part of the work and reviews the other's.
The roles **rotate** between deliverables, so each member leads the core modeling once.
We write the report together.

The report's Team Collaboration Process section describes the Deliverable 1 tasks below as
done. **Each must actually be done by the named member before submission.** When one is
finished, set its flag to `True` in `TEAM_TASKS` in `generate_report.py`. The build warns
until all are `True`. Each task is also a GitHub issue.

## Getting started (Anil)

1. Accept the collaborator invitation (GitHub email or <https://github.com/notifications>).
2. Clone the repo: `git clone https://github.com/ychinthaluri53651/diabetes-readmission-residency-day-1.git`
3. Set your Git identity **once**, so your commits show under your name:
   `git config user.name "Anil Kumar Abburi"` and `git config user.email "<your GitHub email>"`
4. Open the notebook in Colab straight from GitHub: in Colab, File → Open notebook → GitHub →
   paste the repo URL → choose the notebook on the PR branch.

**No Git install needed.** Every task can be committed from the browser while signed in as
`Anil9618`, and the commit is recorded under that account:

1. Open the file on GitHub (e.g., `DECISIONS.md`) and click the pencil icon (**Edit**).
2. Make the change, then click **Commit changes…**.
3. Choose **Create a new branch** and name it `abburi/<task>` (e.g., `abburi/decision-signoffs`).
4. Click **Propose changes** and open the pull request, with `Closes #N` in its description.

## Deliverable 1 — before submission

| # | Owner | Task | Evidence it leaves |
|---|---|---|---|
| 1 | Abburi | Run the notebook in Colab from GitHub (Runtime → Run all) and confirm the results match report Tables 3 and 4 | Comment on the issue with the numbers obtained |
| 2 | Abburi | Review the Deliverable 1 pull request (grouped split, no forward fill, ROC-AUC scoring); approve it or request changes | Pull-request review under `Anil9618`; sign-offs in `DECISIONS.md` |
| 3 | Abburi | Revise the sections he leads, the Introduction and the Ethical Considerations section, on branch `abburi/framing-and-ethics` | His commits; his pull request |
| 4 | Chinthaluri | Review Abburi's pull request and merge it | Pull-request review |
| 5 | Abburi | APA proofread of the full report (title page, citations, references, tables, figures) | Issue comments or commits |
| 6 | Both | Hold the first weekly check-in and log it with date and decisions | Dated entry in `DECISIONS.md` |

### Before submitting Deliverable 1

1. Finish tasks 1–6 above and set each flag in `TEAM_TASKS` (`generate_report.py`) to
   `True` only once it is actually done.
2. Set `COLAB_URL` in `generate_report.py`: upload the `.ipynb` to Colab, choose Share →
   "Anyone with the link can view", and paste the link.
3. Rebuild with `python3 generate_report.py`. It prints a WARNING while either step is
   incomplete.

## Deliverable 2 — roles rotate

| Area | Lead | Reviewer | Work |
|---|---|---|---|
| Model tuning and evaluation | **Abburi** | Chinthaluri | Wider grids, a gradient-boosting challenger, calibration, and a capacity-based threshold |
| Fairness audit | **Chinthaluri** | Abburi | Subgroup recall, flag rate, and calibration with confidence intervals; a mitigation test |
| Cost and capacity | **Chinthaluri** | Abburi | Cost and capacity analysis; deployment and monitoring plan |
| Updated framing | **Abburi** | Chinthaluri | Refine the framing with the Deliverable 1 findings |
| Model explanation | **Abburi** | Chinthaluri | Permutation importance for the final model |
| Report | Both | Both | Each drafts the sections he leads and reviews the other's; final APA pass shared |

## Working agreement

- One branch per task, named `owner/short-task` (e.g., `abburi/framing-and-ethics`).
- Nothing reaches `main` without the other member's pull-request approval.
- Each task is a GitHub issue assigned to its owner; pull requests close their issues
  (`Closes #N`).
- Commits are made under each member's own Git identity. When both members write a change
  together, the committer adds a `Co-authored-by:` line for the other, so GitHub credits both.
- The notebook opens in Colab from GitHub; GitHub is the single source of truth.
- Methodological decisions go in `DECISIONS.md` with proposer, reviewer, and date.
