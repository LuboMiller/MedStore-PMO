# CONTEXT.md — шаблон контексту проєкту

> Єдине джерело правди про поточний проєкт для AI-асистента PMO.
> Заповни перед стартом сесії. Не дублюй сюди корпоративну методологію — вона в `knowledge/pmo-kb/`.

---

## 0. Ідентифікація

| Параметр | Значення |
|---|---|
| **Назва проєкту** | {{PROJECT_NAME}} |
| **Клієнт** | {{CLIENT}} |
| **Тип контракту** | Fixed / T&M / Mixed — {{CONTRACT_TYPE}} |
| **PM** | {{PM_NAME}} |
| **DM** | {{DM_NAME}} |
| **BA** | {{BA_NAME}} |
| **Дата kick-off** | {{KICKOFF_DATE}} |
| **Планова тривалість** | {{DURATION}} |
| **Decision Maker (клієнт)** | {{CLIENT_DM}} |

---

## 1. Business case (коротко)

{{BUSINESS_CASE}}

---

## 2. Цілі / успіх (SMART)

| # | Ціль | Метрика | Дедлайн |
|---|---|---|---|
| 1 | | | |

---

## 3. Scope (high-level)

| IN scope | OUT of scope |
|---|---|
| | |

---

## 4. Команда і FTE

| Роль | Ім'я | FTE |
|---|---|---|
| | | |

---

## 5. Стейкхолдери клієнта

| Ім'я | Роль | Power / Interest | Нотатки |
|---|---|---|---|
| | | | |

Конфіденційний детальний реєстр — `docs/stakeholder-register.md`.

---

## 6. Бюджет / margin (внутрішнє)

| Параметр | Значення |
|---|---|
| Contract value | |
| Margin target | |
| Contingency | |

---

## 7. Топ-ризики

| # | Ризик | Ймовірність | Вплив | Митигація |
|---|---|---|---|---|
| 1 | | | | |

---

## 8. Канонічні посилання проєкту

| Тема | Шлях |
|---|---|
| Charter | `docs/project-charter.md` |
| WBS | `docs/wbs.md` |
| Glossary | `docs/glossary.md` |
| Risk register | `docs/risk-register.md` |
| Open questions | `docs/open-questions.md` |
| Sprint tracker | `dashboards/sprint-tracker.md` |
| EVM log | `docs/evm-log.md` |
| Jira project | `{{JIRA_KEY}}` |
| Confluence space | `{{CONFLUENCE_SPACE}}` · MD mirror: `knowledge/confluence-spaces/{{CONFLUENCE_SPACE}}/` |
| Google Drive folders | `config/google-directories.json` · registry: `registry/google/` |
| Client contracts / SOW | `config/contracts.json` · `docs/contracts/` · `google contracts-status --write` |
| Time Report (monthly act) | `config/time-report.json` · `docs/acts/` · skill `pmo-prepare-monthly-act` |
| Client Project status sheet | `config/client-status-sheet.json` · playbook `docs/client-status-sheet/operating-playbook.md` |
| CHANGE REQUESTS (D4) | `docs/change-requests/README.md` |
| Fireflies | optional — `FIREFLIES_API_KEY` → `docs/meeting-notes/` · skill `pmo-fireflies-ops` |
| BA linked repos | `config/linked-repos.json` → `knowledge/ba/` |
| Codebase linked repos | `config/linked-repos.json` → `knowledge/codebases/` |

> Якщо проєкт уже існує в Atlassian / Google — спочатку `pmo-hydrate-project` (+ `pmo-google-ops`), потім дозаповни цей файл.
> BA/code репо — опційно через `pmo-ba-repos` / `pmo-codebase-context`. Гайд: `docs/pm-playbook.md`.

---

## 9. Нотатки сесії

{{SESSION_NOTES}}
