# Шаблон: User Story з трасуванням (Traceability)

> Призначення: кожна User Story простежувана — від вимоги/епіка до FS, API і тест-кейсів.  
> Skill: `pmo-manage-user-stories` · QG: `pmo-qg-review-user-stories`  
> Якщо є BA repo (`config/linked-repos.json` → `ba_repos`) — SoT stories/FS у `knowledge/ba/`, не дублювати в `docs/functional-specs/`.

---

## Структура ID

| Рівень | Формат ID | Приклад |
|---|---|---|
| Epic | `EPIC-N` або Jira Epic key | `EPIC-2` / `PROJ-100` |
| Requirement | `REQ-N` | `REQ-14` |
| User Story | `US-N` або Jira Story key | `US-23` / `PROJ-201` |
| Functional Spec | `FS-N` | `FS-23` |
| API endpoint | `API-N.M` | `API-23.1` |
| Test Case | `TC-N.M` | `TC-23.1` |
| Change Request | `CR-N` | `CR-015` |

---

## Шаблон однієї User Story

### US-[N]: [Короткий заголовок]

| Поле трасування | Значення |
|---|---|
| **Epic** | [EPIC-N / Jira key — назва] |
| **Requirement** | [REQ-N] або "—" якщо з CR |
| **Change Request** | [CR-N] або "—" |
| **Functional Spec** | [FS-N — посилання] |
| **API endpoints** | [API-N.1, …] |
| **Test Cases** | [TC-N.1, …] |
| **Sprint** | [номер / Jira sprint] |
| **Depends on** | [US-M / BLK-N / —] |
| **Blocks** | [US-K / —] |
| **Track** | [Web / Mobile / Backend / …] |

**As a:** [роль]  
**I want to:** [дія]  
**So that:** [цінність]

**Acceptance Criteria:**
- AC1: …
- AC2: …
- AC3: …

**Scope note:** [що явно НЕ входить]  
**Estimated complexity:** [XS / S / M / L / XL або SP]  
**Out-of-scope flag:** [YES / NO]

---

## Матриця трасування (рівень епіка)

| Requirement | Epic | User Story | Functional Spec | API | Test Case | Статус |
|---|---|---|---|---|---|---|
| REQ-N | EPIC-N | US-N | FS-N | API-N.1 | TC-N.1 | Not started / In progress / Done |

**Правило повноти:** порожня клітинка = розірване трасування.

---

## Правила

1. Кожна US посилається на Epic (або явний CR без epic — виняток з обґрунтуванням).
2. US поза baseline → обов’язкове поле `Change Request`.
3. Depends on / Blocks — у обидва боки.
4. Ready for Dev лише з існуючим FS (якщо BA SoT — посилання на BA mirror).
5. Мінімум один Test Case на AC.
6. Зміна scope/AC після старту dev → Change Log / CR.

---

*Devlight PMO · User Story Traceability · `templates/tl-user-story.md`*
