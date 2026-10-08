# Operating playbook — клієнтські контракти (Google Drive + локальний реєстр)

> SoT **файлів**: Drive папка з key `contracts` у `config/google-directories.json` (часто `commercial` → **Договір / Contracts**).
> SoT **дедлайнів / етапів**: `config/contracts.json` → `docs/contracts/register.md`.
> CLI: `google contracts-status` · skill: `pmo-google-ops`.

## Навіщо

- Бачити, **коли закінчується контракт** (end_date) і чи потрібна пролонгація.
- Стежити за **дедлайнами етапів** (Discovery, MVP, acceptance) поруч із EWS / daily actions.
- Не тримати підписані PDF у git — лише метадані + `drive_file_id`.

## Setup

1. У Drive створити (або взяти існуючу) папку **Договір / Contracts**.
2. Додати key `contracts` у `config/google-directories.json` з `folder_id`.
3. Скопіювати `config/contracts.example.json` → `config/contracts.json`, заповнити CTR/STG.
4. Залити PDF/Doc у папку → `google sync-pull --dir contracts` → проставити `drive_file_id`.

```bash
python3 scripts/integrations/cli.py google sync-pull --dir contracts
python3 scripts/integrations/cli.py google contracts-status --write
```

## Поля контракту

| Поле | Призначення |
|---|---|
| `id` | `CTR-NNN` |
| `type` | SOW / MSA / Amendment / NDA / Other |
| `status` | `draft` · `active` · `expired` · `terminated` · `renewed` |
| `start_date` / `end_date` | Період дії (ISO) |
| `stages[]` | Етапи з власними `end_date` + `acceptance_date` |
| `drive_file_id` | Файл у Drive (не папка) |

## Traffic light (CLI)

| Light | Правило (default) |
|---|---|
| 🟢 | Закритий етап/контракт або > `warn_days` до end |
| 🟡 | ≤ `warn_days` (14) до end |
| 🔴 | ≤ `critical_days` (7), overdue, або status expired/terminated |
| ⚪ | Немає `end_date` |

## Каденція PM

| Коли | Дія |
|---|---|
| Після підпису / амендменту | Upload у Drive → оновити `contracts.json` → `--write` |
| Щотижня (Пн з EWS) | `contracts-status` — якщо 🟡/🔴 → Action Item / Issue Log |
| Щоденний morning sync | Читати `docs/contracts/register.md` у `pmo-daily-pm-actions` |
| Close-out | `end_date` / acceptance → F2 (`pmo-closing-pack`); billing same day після підпису |

## Hard rules

1. Підписані контракти — **конфіденційно**; не в клієнтський weekly status без потреби.
2. Зміна `contract_value` / термінів — через CR / комерційний процес, не «тихо» в реєстрі.
3. EWS Budget Amber, якщо burn → CV без формального extension, а `end_date` близько.
4. `google sync-pull --dir contracts` = metadata файлів; дедлайни — лише з `contracts.json`.

## Related

- Drive dirs: `config/google-directories.json` · registry `registry/google/contracts/`
- Monthly acts: `docs/acts/` · `pmo-prepare-monthly-act`
- Closing: `pmo-closing-pack` (F2)
- CONTEXT §6 Budget / margin
