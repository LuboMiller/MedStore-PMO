# Template — RACI / DACI (B4)

```markdown
# RACI Matrix — {{PROJECT_NAME}}

> Правило: **один Accountable (A) на рядок**.

| Deliverable / процес | PM | TL | BE | FE | QA | BA | PO (клієнт) | DM | …
|---|---|---|---|---|---|---|---|---|---|
| Project Charter | A | I | -- | -- | -- | -- | -- | C | |
| Requirements / Stories | C | C | C | C | C | R | A | -- | |
| Sprint Backlog | C | C | R | R | C | R | A | -- | |
| Release | C | A | R | R | R | -- | I | I | |
| Scope Change (CR) | A | C | C | C | C | C | R | C | |
| Escalation Red | R | C | -- | -- | -- | -- | C | A | |
| Weekly Status (client) | A | C | -- | -- | -- | C | I | I | |
| EWS (PM→DM) | R | C | -- | -- | -- | -- | -- | A | |

## Легенда
| Код | Значення |
|---|---|
| R | Responsible — виконує |
| A | Accountable — один власник результату |
| C | Consulted — консультація до рішення |
| I | Informed — інформується після |
| -- | Не залучений |

## DACI (за потреби — окрема секція для рішень)
| Рішення | Driver | Approver | Consulted | Informed |
|---|---|---|---|---|
| | | | | |

## Audit «один A»
| Рядок | Кількість A | OK? |
|---|---|---|
| | | |
```
