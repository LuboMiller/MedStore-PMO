---
name: pmo-weekly-rhythm
description: Orchestrates the Devlight weekly PM cadence — Monday EWS for DM and Friday client weekly status with consistency QG. Use at week start/end or when PM asks for the weekly operating rhythm.
---

# Weekly Rhythm — Orchestrator

## When to use

- Понеділок / п'ятниця — стандартний ритм Devlight
- PM просить «зробити тижневий цикл»
- Після оновлення sprint tracker / risks / CR

## Cadence

| Коли | Skill | Аудиторія |
|---|---|---|
| **Пн ≤ 09:00** | `pmo-generate-ews-report` | DM (внутрішнє) |
| Щодня / ранок | `pmo-daily-pm-actions` | PM inbox · `docs/daily-actions/` |
| За потреби в тижні | `pmo-manage-issue-log`, `pmo-manage-risk-register`, `pmo-manage-decision-log` | внутрішнє |
| Amber/Red per matrix | `pmo-generate-escalation-memo` | DM/CEO |
| **Пт ≤ 17:00** | `pmo-generate-weekly-status` → (опційно `google gmail-draft`) → `pmo-qg-review-status-consistency` | клієнт · артефакти в `docs/weekly-status/{{YYYY-MM-DD}}/` · email style: явный path → `docs/weekly-status/email-style.md` → `templates/tl-weekly-status-email.md` · Gmail: `--file …/email.md` (`pmo-google-ops`) |
| Раз на місяць | `pmo-generate-client-health-report` | DM |
| Раз на квартал | `pmo-generate-qbr` | C-level (через DM) |

## Instructions

1. Уточни день тижня / що потрібно зараз (Пн EWS / Пт client / full week).
2. Якщо потрібні **live** Jira/Tempo дані — спочатку `pmo-integrations-health` / `make integrations-check`.
3. Збери канонічні джерела: `CONTEXT.md`, sprint tracker, risk register, CR, meeting follow-ups, EVM; за можливості підтягни Jira status-counts / Tempo hours через `scripts/integrations/cli.py`.
4. Запусти відповідні skills; **не змішуй** EWS і client weekly в один документ.
5. Перед клієнтським статусом — обов'язково QG consistency.
6. Якщо Traffic Light ≠ Green — перевір Escalation Matrix і чи потрібен memo.

## Rules

1. No Surprises: Amber/Red клієнт дізнається від PM у Friday status (або earlier), DM — у EWS/memo.
2. Чесність EWS > оптимізм.
3. Не публікувати статус-пакет з блокерами QG.

## Company methodology

D11 / D12 / E11 у `knowledge/pmo-kb/` · `AGENTS.md`
