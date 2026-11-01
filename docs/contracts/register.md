# Contract register

> Локальний SoT дедлайнів контрактів / етапів. PDF/Docs — у Drive `google-directories` → `contracts`. Оновлення: `python3 scripts/integrations/cli.py google contracts-status --write`.

- **As of:** 2026-11-02
- **Generated (UTC):** 2026-11-01T22:07:33Z
- **Warn / critical windows:** ≤14д 🟡 / ≤7д 🔴
- **Config:** `config/contracts.json`
- **Playbook:** [operating-playbook.md](./operating-playbook.md)

## Traffic light

| Light | Meaning |
|---|---|
| 🟢 | On track or closed |
| 🟡 | Due within 14 days |
| 🔴 | Due within 7 days, overdue, or expired/terminated |
| ⚪ | No end_date set |

## Contracts & stages

| Light | Kind | ID | Title | Status | End | Days left | Drive |
|---|---|---|---|---|---|---|---|
| ⚪ | contract | CTR-001 | Framework Agreement №150626 — Добробут × Devlight | active | — | — | `1myV946kpmKQNQXAIqioVaLQr7XbAvlOD` |
| 🟢 | stage | STG-01 | Framework Agreement №150626 — Добробут × Devlight · Додаток №3 / Discovery–Pilot MedStore (T&M) | active | 2026-11-30 | 28 | — |

## Action needed (≤ warn / overdue)

_Немає відкритих дедлайнів у вікні попередження._

## Contract details

### CTR-001 — Framework Agreement №150626 — Добробут × Devlight

| Field | Value |
|---|---|
| Type | Master |
| Status | active |
| Signed | 2026-07-28 |
| Start | 2026-07-28 |
| End | — |
| Value (USD) | — |
| Owner | PM |
| Drive file name | РАМКОВИЙ ДОГОВІР Добробут.docx – копія.docx |
| Drive link | https://docs.google.com/document/d/1myV946kpmKQNQXAIqioVaLQr7XbAvlOD/edit |
| Notes | PM 2026-10-08: угода давно підписана, delivery активний. Підписанти: Devlight — Ігор Поліч; Dobrobut — Сергій Орел. |

| Stage | Status | Start | End | Acceptance | Notes |
|---|---|---|---|---|---|
| STG-01 Додаток №3 / Discovery–Pilot MedStore (T&M) | active | 2026-08-20 | 2026-11-30 | — | Drive PDF: Dodatkova uhoda 3 do dohovoru 150626 (1kg_BX995…). Target Pilot кін. листопада 2026. Baseline cost Overview €70 633,50. |

---

_Не зберігайте підписані PDF у git — лише метадані + Drive file id. Після upload: `google sync-pull --dir contracts`, потім оновіть `drive_file_id` у `config/contracts.json`._
