# Google credentials (local only)

Ця папка в `.gitignore`. Сюди кладеш **свої** кредси.

## Варіант A — OAuth (рекомендовано, якщо доки «доступ закритий» для service account)

1. Google Cloud Console → APIs & Services → Credentials → **Create OAuth client ID** (Desktop app).
2. Увімкни **Google Drive API** (+ Docs API якщо треба export; **Gmail API** якщо треба `gmail-draft`; **Google Sheets API** якщо треба `time-report` / місячний акт).
3. Завантаж JSON клієнта → збережи як:

```
secrets/google-oauth-client.json
```

4. У `.env`:

```
GOOGLE_AUTH_MODE=oauth
GOOGLE_OAUTH_CLIENT_SECRETS=./secrets/google-oauth-client.json
GOOGLE_OAUTH_TOKEN=./secrets/google-oauth-token.json
```

5. Один раз авторизуйся своїм Google-акаунтом (той, у якого є доступ до папок / з якого шлеш статуси):

```bash
# Drive only
python3 scripts/integrations/cli.py google auth

# Drive + Gmail compose + settings.basic (чернетки + підпис з Settings)
python3 scripts/integrations/cli.py google auth --gmail
```

Токен з’явиться в `secrets/google-oauth-token.json` (теж gitignored).

### Gmail draft (weekly status)

```bash
cp config/weekly-status-mail.example.json config/weekly-status-mail.json
# заповни default_to / default_cc; append_gmail_signature: true (default)

# перевірити HTML-підпис з Gmail Settings
python3 scripts/integrations/cli.py google gmail-signature

python3 scripts/integrations/cli.py google gmail-draft \
  --file docs/weekly-status/YYYY-MM-DD/email.md \
  --dry-run

python3 scripts/integrations/cli.py google gmail-draft \
  --file docs/weekly-status/YYYY-MM-DD/email.md
```

Створює **чернетку** в Gmail (не send). Тіло — multipart (plain + HTML); футер береться з **Gmail Settings → Signature** (API сам його не підставляє).  
`--no-signature` — без футера. Registry: `registry/google/gmail-drafts/`.  
Weekly packs: `docs/weekly-status/{{YYYY-MM-DD}}/` (див. `docs/weekly-status/README.md`).

## Варіант B — Service account

```
secrets/google-sa.json
```

```
GOOGLE_AUTH_MODE=service_account
GOOGLE_APPLICATION_CREDENTIALS=./secrets/google-sa.json
GOOGLE_DELEGATED_USER=you@devlight.io   # якщо domain-wide delegation
```

Кожну Drive-папку треба **шарити** на email service account (або delegation).

## Кілька директорій

Редагуй `config/google-directories.json` (скопіюй з `.example.json`):

```bash
cp config/google-directories.example.json config/google-directories.json
# заповни folder_id для main / finance / …
```

```bash
python3 scripts/integrations/cli.py google directories
python3 scripts/integrations/cli.py google list --dir finance
python3 scripts/integrations/cli.py google sync-pull --all-dirs
```
