# Google Workspace registry

Дзеркало проєктних Google Drive folders (одна або кілька іменованих директорій).

```
registry/google/
  index.json                 # optional aggregate / main
  {dir_key}/index.json       # per directory from sync-pull --dir / --all-dirs
  contracts/                 # SOW / Договір folder mirror (when key configured)
  gmail-drafts/              # Gmail draft create log
  README.md
```

## Auth

Особисті кредси (OAuth) або service account — див. `secrets/README.md`.

```bash
pip install -r scripts/integrations/requirements-google.txt
python3 scripts/integrations/cli.py google auth
python3 scripts/integrations/cli.py google init-dirs   # → config/google-directories.json
```

## Commands

```bash
python3 scripts/integrations/cli.py google directories
python3 scripts/integrations/cli.py google list --dir finance
python3 scripts/integrations/cli.py google list --dir contracts
python3 scripts/integrations/cli.py google sync-pull --all-dirs
python3 scripts/integrations/cli.py google export-doc --file-id ID --out ./tmp.txt
python3 scripts/integrations/cli.py google export-sheets
# → docs/_hydrate/google/sheets/client-status-live-YYYY-MM-DD/ (config/client-status-sheet.json)
python3 scripts/integrations/cli.py google contracts-status --write
# → docs/contracts/register.md (config/contracts.json)
```

Config: `config/client-status-sheet.json` (from `client-status-sheet.example.json`).  
Contracts: `config/contracts.json` · playbook `docs/contracts/operating-playbook.md`.  
`sync-pull` = folder metadata only; **cell content** потребує `export-sheets`; **дедлайни контрактів** — з `contracts.json`, не з Drive.

Skill: `pmo-google-ops`.
