# Fireflies registry

Mirror of synced Fireflies transcripts.

| Path | Purpose |
|---|---|
| `index.json` | Map transcript id → local folder |
| `transcripts/{id}.json` | Per-meeting metadata + file paths |

Source of meeting content: `docs/meeting-notes/`.  
Sync: `python3 scripts/integrations/cli.py fireflies sync-pull` · skill `pmo-fireflies-ops`.
