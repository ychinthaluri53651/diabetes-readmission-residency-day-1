# Team Tasks — Residency Project (PhDAI-733-M20)

| Member | Student ID | GitHub | Leads in Deliverable 1 | Leads in Deliverable 2 |
|---|---|---|---|---|
| Yogananda Atreya Chinthaluri | 53651 | `ychinthaluri53651` | Dataset exploration, model development, preliminary tuning | Ethics and fairness audit, real-world cost and capacity analysis |
| Anil Kumar Abburi | 53405 | `Anil9618` | Problem definition, ethics and impact, real-world application, Colab reproduction | Optimization and evaluation: tuning, boosting, calibration, thresholds |

**Equal shares.** Each member leads three rubric criteria and reviews the other's three.
The roles **rotate** between deliverables, so each member leads the core modeling once.
Teamwork, documentation, and writing are shared.

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

## Deliverable 1 — before submission

| # | Owner | Task | Evidence it leaves |
|---|---|---|---|
| 1 | Abburi | Run the notebook in Colab from GitHub (Runtime → Run all) and confirm the results match report Tables 3 and 4 | Comment on the issue with the numbers obtained |
| 2 | Abburi | Review the Deliverable 1 pull request (grouped split, no forward fill, ROC-AUC scoring); approve it or request changes | Pull-request review under `Anil9618`; sign-offs in `DECISIONS.md` |
| 3 | Abburi | Revise the sections he leads, the Introduction and the Ethical Considerations and Real-World Application section, on branch `abburi/framing-and-ethics` | His commits; his pull request |
| 4 | Chinthaluri | Review Abburi's pull request and merge it | Pull-request review |
| 5 | Abburi | APA proofread of the full report (title page, citations, references, tables, figures) | Issue comments or commits |
| 6 | Both | Hold the first weekly check-in and log it with date and decisions | Dated entry in `DECISIONS.md` |

## Deliverable 2 — roles rotate

| Criterion | Lead | Reviewer | Work |
|---|---|---|---|
| Optimization and evaluation | **Abburi** | Chinthaluri | Wider grids, a gradient-boosting challenger, calibration, and a capacity-based threshold |
| Ethics and impact | **Chinthaluri** | Abburi | Subgroup recall, flag rate, and calibration with confidence intervals; a mitigation test |
| Real-world application | **Chinthaluri** | Abburi | Cost and capacity analysis; deployment and monitoring plan |
| Problem definition update | **Abburi** | Chinthaluri | Refine the framing with the Deliverable 1 findings |
| Model explanation | **Abburi** | Chinthaluri | Permutation importance for the final model |
| Report | Both | Both | Each drafts the sections he leads and reviews the other's; final APA pass shared |

## Working agreement

- One branch per task, named `owner/short-task` (e.g., `abburi/framing-and-ethics`).
- Nothing reaches `main` without the other member's pull-request approval.
- Each task is a GitHub issue assigned to its owner; pull requests close their issues
  (`Closes #N`).
- Commits are made under each member's own Git identity.
- The notebook opens in Colab from GitHub; GitHub is the single source of truth.
- Methodological decisions go in `DECISIONS.md` with proposer, reviewer, and date.
