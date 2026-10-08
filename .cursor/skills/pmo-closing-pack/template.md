# Template — Closing Pack

## `docs/closing/README.md`

```markdown
# Closing Pack — {{PROJECT_NAME}}

| ID | Артефакт | Статус | Файл |
|---|---|---|---|
| F1 | Final Report | Draft / Ready / Signed | f1-final-report.md |
| F2 | Final Acceptance | Draft / Sent / Signed | f2-final-acceptance.md |
| F6 | Lessons Learned Final | Draft / Ready | f6-lessons-learned-final.md |
| F7 | Handover | Draft / Walkthrough done / Accepted | f7-handover.md |

Billing triggered: Yes/No · Дата:
```

## F1 — Final Report (скорочено)

```markdown
# F1 Final Report — {{PROJECT_NAME}}
## Executive summary
## Scope delivered vs baseline
## Schedule / Cost (SPI, CPI, EAC якщо є)
## Ключові ризики і issues — підсумок
## Рішення / CR — підсумок
## Рекомендації для DM / OPAs (high-level)
## Додатки (посилання на реєстри)
```

## F2 — Final Acceptance

```markdown
# F2 Final Acceptance — {{PROJECT_NAME}}
| Deliverable | Критерій прийняття | Статус | Дата |
|---|---|---|---|
| | | Accepted / Pending | |

Винятки / warranty / known limitations:
…

Підписи:
| Роль | Ім'я | Дата | Підпис |
|---|---|---|---|
| Decision Maker (клієнт) | | | |
| PO (якщо окремо) | | | |
| PM Devlight | | | |
| DM (за потреби) | | | |

> Після підпису Decision Maker — billing того ж дня.
```

## F6 — Lessons Learned Final

```markdown
# F6 Lessons Learned Final — {{PROJECT_NAME}}
> Упорядковано з docs/lessons-learned-registry.md (див. pmo-generate-lessons-learned).

| # | Ситуація | Урок | Рекомендація для OPAs | Джерело (LL-ID) |
|---|---|---|---|---|
| 1 | | | | LL-… |
```

## F7 — Handover

```markdown
# F7 Handover Package — {{PROJECT_NAME}}
| Документ | Зміст | Отримувач | Дата |
|---|---|---|---|
| ADR | | CTO / техконтакт | |
| API docs | | | |
| Deployment guide | | | |
| User guide | | PO / users | |
| Repo / access transfer | | | |

## Walkthrough
Дата · Учасники · Порядок денний · Підтвердження приймання
```
