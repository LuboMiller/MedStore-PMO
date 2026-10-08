# Hydrate / live exports

Тимчасові зрізи з Jira / Confluence / Google (`project hydrate`, `google export-sheets`, SETUP_STATUS).
Не коміть секрети. Типово gitignored (`docs/_hydrate/**`), окрім цього README.

```bash
python3 scripts/integrations/cli.py project hydrate --jira-key KEY --space SPACE
python3 scripts/integrations/cli.py google export-sheets
```
