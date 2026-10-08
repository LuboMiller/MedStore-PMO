---
name: pmo-fireflies-ops
description: Pulls Fireflies.ai meeting recordings into the repo as transcript markdown, AI summary, and MP3 audio. Use after client/team calls, before pmo-extract-meeting-notes, or on weekly cadence to sync meetings.
---

# Fireflies.ai operations

## When to use

- Після дзвінка з клієнтом / командою, записаного у Fireflies
- Перед `pmo-extract-meeting-notes` (спочатку сирий pull, потім структурований протокол)
- Щотижневий sync зустрічей у `docs/meeting-notes/`
- Коли потрібен локальний transcript + summary + mp3 у репо

## Setup

1. Fireflies → **Integrations → Fireflies API** → створити API key
2. У `.env`:

```bash
FIREFLIES_API_KEY=...
# Optional filter for project meetings (title search)
FIREFLIES_KEYWORD={{PROJECT_NAME}}
FIREFLIES_KEYWORD_SCOPE=title
FIREFLIES_DOWNLOAD_AUDIO=1
```

3. Перевірка:

```bash
python3 scripts/integrations/cli.py fireflies ping
make integrations-check   # fireflies = optional ✅/⚠️/skipped
```

## Output layout

```
docs/meeting-notes/{YYYY-MM-DD}-{slug}/
  transcript_raw.md    ← повний транскрипт (MD)
  summary.md           ← AI summary / action items
  audio.mp3            ← запис (Pro+; audio_url)
  fireflies-meta.json  ← id, urls, synced_at

registry/fireflies/
  index.json
  transcripts/{id}.json
```

`fireflies-meta.json → id` є ключем ідентичності зустрічі. Sync повторно
використовує вже наявну читабельну папку з тим самим ID. Суфікс із ID додається
лише тоді, коли інша зустріч уже займає таку саму пару дата + назва.

`audio_url` потребує **Pro+** план Fireflies; без нього MD все одно пишуться, mp3 пропускається з `audio_error`.

## Commands

```bash
python3 scripts/integrations/cli.py fireflies ping
python3 scripts/integrations/cli.py fireflies list --limit 20
python3 scripts/integrations/cli.py fireflies list --keyword {{PROJECT_NAME}} --from-date 2026-01-01T00:00:00.000Z
python3 scripts/integrations/cli.py fireflies pull --id <transcript_id>
python3 scripts/integrations/cli.py fireflies sync-pull
python3 scripts/integrations/cli.py fireflies sync-pull --force --no-audio
make fireflies-sync
```

## Instructions

1. `fireflies ping` — ключ валідний.
2. `list` — знайти потрібні мітинги (keyword / дати).
3. `pull --id` або `sync-pull` — записати MD + mp3 у `docs/meeting-notes/`.
4. Далі: skill `pmo-extract-meeting-notes` на `transcript_raw.md` → `transcript.md` + `followup.md`.
5. Рішення з дзвінка ≤ 4h → `pmo-manage-decision-log`.

## Rules

1. Інтеграція **опційна** (як Google) — відсутність ключа не валить mandatory health.
2. REST/GraphQL лише через `scripts/integrations/` — **не MCP**.
3. `transcript_raw.md` / `summary.md` з Fireflies — джерело; не «прикрашати» перед extract.
4. Секрети лише в `.env` (gitignored).
5. Великі `audio.mp3` — нормально в репо за запитом PM; за потреби Git LFS.

## Related

- `pmo-extract-meeting-notes` · `pmo-manage-decision-log` · `pmo-integrations-health`
- CLI: `scripts/integrations/README.md`
