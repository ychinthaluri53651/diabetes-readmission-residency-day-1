## Summary

<!-- What this pull request changes and why. -->

Closes #

## Checklist (author)

- [ ] The notebook runs top to bottom (Runtime → Run all in Colab)
- [ ] `outputs/results.json` and `figures/` are regenerated if any number or figure changed
- [ ] The report's tables and figures match `outputs/results.json`
- [ ] Methodological changes are explained in this description

## Review (other member)

- [ ] No patient appears in both training and test data
- [ ] Preprocessing is fit after the split, inside the `Pipeline`
- [ ] Metrics are appropriate for an 11% outcome (ROC-AUC, PR-AUC, recall, lift), not accuracy alone
- [ ] Report text matches the results and follows APA 7th
