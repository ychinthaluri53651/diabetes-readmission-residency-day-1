## Summary

<!-- What this pull request changes and why. -->

Closes #

## Checklist (author)

- [ ] The notebook runs top to bottom (`python3 build_notebook.py`, or Runtime → Run all in Colab)
- [ ] `outputs/results.json` and `figures/` are regenerated if any number or figure changed
- [ ] `python3 generate_report.py` passes every check
- [ ] Methodological changes are logged in `DECISIONS.md`

## Review (other member)

- [ ] No patient appears in both training and test data
- [ ] Preprocessing is fit after the split, inside the `Pipeline`
- [ ] Metrics are appropriate for an 11% outcome (ROC-AUC, PR-AUC, recall, lift), not accuracy alone
- [ ] Report text matches the results and follows APA 7th
