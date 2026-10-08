---
name: pmo-google-ops
description: Operates Google Workspace (Drive folder listing including contracts/SOW directory, Docs export, multi-directory registry sync, Gmail draft creation for weekly status, monthly Time Report / act Sheets create-fill, and client contract deadline register) with user OAuth or service account credentials. Use when project docs live in Google Drive/Docs/Sheets, PM tracks SOW/contract end dates or stage deadlines, needs private folder access, creating a Gmail draft from weekly-status email markdown, or preparing the monthly T&M act Time Report.
---

# Google Workspace operations

## When to use

- Документи проєкту в Google Drive / Docs / Sheets
- Папки **закриті** для service account → user OAuth своїми кредсами
- Кілька директорій (contracts / commercial / client-share) одночасно
- **Контракти / SOW** — Drive папка `contracts` + дедлайни етапів у `config/contracts.json`
- **Gmail draft** клієнтського weekly status з `docs/weekly-status/{{YYYY-MM-DD}}/email.md` (не send)
- **Monthly Time Report / акт** — Tempo bill → вкладка місяця в Sheets (`google time-report`; skill `pmo-prepare-monthly-act`)

## Setup (user credentials — recommended)

```bash
pip install -r scripts/integrations/requirements-google.txt

# 1) OAuth Desktop client JSON → secrets/google-oauth-client.json
#    Enable: Drive API, Gmail API, Sheets API
#    Details: secrets/README.md

# 2) .env
GOOGLE_AUTH_MODE=oauth
GOOGLE_OAUTH_CLIENT_SECRETS=./secrets/google-oauth-client.json
GOOGLE_OAUTH_TOKEN=./secrets/google-oauth-token.json

# 3) Browser login
python3 scripts/integrations/cli.py google auth --gmail
# For monthly act write:
python3 scripts/integrations/cli.py google auth --sheets --write-scope

# 4) Named directories (Drive)
python3 scripts/integrations/cli.py google init-dirs
# edit config/google-directories.json

# 5) Default mail recipients (optional)
cp config/weekly-status-mail.example.json config/weekly-status-mail.json

# 6) Time Report people/rates (monthly act)
cp config/time-report.example.json config/time-report.json

# 7) Client contracts / SOW deadlines
cp config/contracts.example.json config/contracts.json
# set google-directories key `contracts` → Drive Договір folder
```

Service account (`GOOGLE_APPLICATION_CREDENTIALS`) досі для Drive; для **Gmail draft** надійніше **user OAuth** (або SA + domain-wide delegation на mailbox).

## Commands

```bash
python3 scripts/integrations/cli.py google auth
python3 scripts/integrations/cli.py google auth --gmail          # + compose + settings.basic
python3 scripts/integrations/cli.py google auth --sheets --write-scope
python3 scripts/integrations/cli.py google init-dirs
python3 scripts/integrations/cli.py google directories
python3 scripts/integrations/cli.py google ping
python3 scripts/integrations/cli.py google list --dir finance
python3 scripts/integrations/cli.py google list --dir contracts
python3 scripts/integrations/cli.py google list --folder-id RAW_ID
python3 scripts/integrations/cli.py google sync-pull --dir main
python3 scripts/integrations/cli.py google sync-pull --dir contracts
python3 scripts/integrations/cli.py google sync-pull --all-dirs
python3 scripts/integrations/cli.py google export-doc --file-id ID --out docs/_hydrate/from-gdoc.txt
# Client status spreadsheet → local hydrate (daily morning; read-only tabs)
python3 scripts/integrations/cli.py google auth --sheets-readonly   # once, if token lacks Sheets
python3 scripts/integrations/cli.py google export-sheets            # → docs/_hydrate/google/sheets/client-status-live-YYYY-MM-DD/
python3 scripts/integrations/cli.py google export-sheets --all-tabs # full book (heavy)

# Contract / stage deadline register (local config; no Google auth required for status)
python3 scripts/integrations/cli.py google contracts-status --init
python3 scripts/integrations/cli.py google contracts-status
python3 scripts/integrations/cli.py google contracts-status --write
python3 scripts/integrations/cli.py google contracts-status --write --snapshot

# Inspect Gmail Settings signature (HTML footer)
python3 scripts/integrations/cli.py google gmail-signature

# Weekly status → Gmail draft (does NOT send; appends Settings signature by default)
python3 scripts/integrations/cli.py google gmail-draft \
  --file docs/weekly-status/2026-09-12/email.md \
  --dry-run
python3 scripts/integrations/cli.py google gmail-draft \
  --file docs/weekly-status/2026-09-12/email.md
# optional overrides:
#   --to a@x.com,b@y.com --cc c@z.com --subject "…"
#   --no-signature          # skip Gmail Settings footer
#   --send-as you@co.com    # non-default sendAs alias

# Monthly act Time Report (Tempo bill → Sheets month tab; creates spreadsheet if missing)
python3 scripts/integrations/cli.py google time-report --month 2026-08 --dry-run
python3 scripts/integrations/cli.py google time-report --month 2026-08
python3 scripts/integrations/cli.py google time-report --month 2026-08 --force
```

Recipients: `--to` / `--cc` або `config/weekly-status-mail.json` → `default_to` / `default_cc`.  
Signature: `append_gmail_signature` (default true) — HTML з Gmail Settings через `users.settings.sendAs` (API-чернетки **не** підставляють підпис самі).  
Registry запису: `registry/google/gmail-drafts/`.
Weekly packs: `docs/weekly-status/{{YYYY-MM-DD}}/` · style override: `docs/weekly-status/email-style.md`.
Acts: `docs/acts/{{YYYY-MM}}/` · config `config/time-report.json` · skill `pmo-prepare-monthly-act`.
Contracts: `docs/contracts/` · config `config/contracts.json` · Drive dir `contracts`.

## Policy

1. REST/API через `scripts/integrations/` — **не MCP**.
2. Секрети лише в `secrets/` + `.env` (gitignored).
3. Google — **optional** у health, доки немає credentials.
4. `gmail-draft` створює **чернетку**, не відправляє лист; за замовчуванням multipart HTML + Settings signature.
5. `time-report` пише лише **Tempo bill**; не overwrite непорожньої вкладки без `--force`; після fill застосовує July/August formatting (див. `pmo-prepare-monthly-act`).
6. Підписані контракти — у Drive `contracts`; у git лише метадані дедлайнів (`contracts.json` / `register.md`).
7. Після export Drive — проганяй контент через відповідний `pmo-*` skill.
8. Weekly status email MD → спочатку `pmo-generate-weekly-status`, потім `google gmail-draft`.

## Related

- `secrets/README.md` · `config/google-directories.example.json` · `config/weekly-status-mail.example.json` · `config/time-report.example.json` · `config/contracts.example.json`
- Registry: `registry/google/` · `registry/google/gmail-drafts/` · `registry/google/contracts/`
- Email style: `templates/tl-weekly-status-email.md` · `docs/weekly-status/email-style.md` · packs `docs/weekly-status/{{YYYY-MM-DD}}/`
- Client Project status spreadsheet (CR / NEW features / SETUP): `pmo-manage-client-status-sheet` · `docs/client-status-sheet/operating-playbook.md`
- Monthly act: `pmo-prepare-monthly-act` · `docs/acts/operating-playbook.md`
- Contracts: `docs/contracts/operating-playbook.md` · `docs/contracts/register.md`