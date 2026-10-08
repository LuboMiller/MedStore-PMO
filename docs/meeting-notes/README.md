# Meeting notes

Сирі та оброблені протоколи зустрічей.

## Fireflies sync

Якщо налаштовано `FIREFLIES_API_KEY`:

```bash
make fireflies-sync
# або
python3 scripts/integrations/cli.py fireflies sync-pull --keyword "{{PROJECT_NAME}}"
```

Кожна зустріч → папка:

```
docs/meeting-notes/{YYYY-MM-DD}-{slug}/
  transcript_raw.md
  summary.md
  audio.mp3
  fireflies-meta.json
```

Далі структурований протокол: skill `pmo-extract-meeting-notes`
(`transcript.md` + `followup.md` у тій самій папці).

Див. `.cursor/skills/pmo-fireflies-ops/SKILL.md`.
