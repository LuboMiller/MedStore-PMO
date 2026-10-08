# Шаблон: Functional Specification

> Заповнюється для фічі/модуля так, щоб розробка могла йти без додаткових уточнень.  
> Skill: `pmo-manage-functional-spec` · QG: `pmo-qg-review-functional-spec`  
> BA SoT (якщо є): `knowledge/ba/{id}/` — не дублювати FS у `docs/functional-specs/`.

---

## 1. Overview

**Назва фічі:** …  
**Пов'язана User Story / Epic:** US-N / EPIC-N / Jira key  
**Короткий опис:** 1–2 речення  
**Контракт:** Fixed Price / T&M / …

---

## 2. Actors / Users

| Роль | Опис |
|---|---|
| … | … |

---

## 3. Preconditions

- …

---

## 4. Main Flow (Happy Path)

1. [Користувач] → [Система]
2. …

---

## 5. Alternative Flows / Edge Cases

| Сценарій | Поведінка системи |
|---|---|
| … | … |

---

## 6. UI/UX References

- Figma / wireframe: …

---

## 7. Business Rules / Validation

- …

---

## 8. Data Requirements

| Поле | Тип | Джерело | Обов'язкове |
|---|---|---|---|
| … | … | … | так/ні |

---

## 9. API Contract

### 9.1 [Назва операції]

| Параметр | Значення |
|---|---|
| **Метод** | `GET` / `POST` / … |
| **Endpoint** | `/api/v1/…` |
| **Авторизація** | Bearer / Public / … |
| **Content-Type** | `application/json` |

**Request — Body / Query**

| Поле | Тип | Обов'язкове | Опис |
|---|---|---|---|
| … | … | … | … |

```json
{ "field": "example" }
```

**Response — Success**

```json
{ "id": "uuid" }
```

**Response — Errors**

| Код | Коли | Тіло |
|---|---|---|
| `400` | … | `{ "error": "validation_error" }` |
| `401` | … | `{ "error": "unauthorized" }` |

---

## 10. Non-functional notes

- …

---

## 11. Dependencies

- Внутрішні: …
- Зовнішні: …

---

## 12. Out of Scope

- …

---

## 13. Acceptance Criteria

- Given …, When …, Then …

---

*Devlight PMO · Functional Spec · `templates/tl-functional-spec.md`*
