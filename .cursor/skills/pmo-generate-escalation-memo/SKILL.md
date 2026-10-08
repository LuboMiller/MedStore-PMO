---
name: pmo-generate-escalation-memo
description: Drafts an E13 Escalation Memo for Red/Critical situations before the DM/CEO call. Use when Escalation Matrix hits Level 2 or 3, never as a Slack substitute.
---

# Escalation Memo (E13)

## When to use

- Level 2 (Red) або Level 3 (Critical) за `docs/escalation-matrix.md`
- Перед ескалаційним дзвінком з DM / CEO
- Не для Amber (достатньо EWS + action plan)

## Role

Готуєш структурований briefing **до** дзвінка. Після відправки: Slack «Red situation — Escalation Memo attached» + слот Zoom 30 хв.

## Instructions

1. Зібери факти з Issue Log, Risk Register, EVM, CR, останнього EWS.
2. Заповни 8 розділів (див. [template.md](template.md)) — факти без емоцій.
3. Збережи `docs/escalations/ESC-{{YYYY-MM-DD}}-{{slug}}.md`.
4. Онови Issue Log / Decision Log після дзвінка (окремими skills).

## Rules

1. Memo ≠ заміна дзвінка.
2. Options A/B/C з pros/cons + явна Recommendation.
3. «What I Need From You» — конкретна дія і дедлайн.
4. Не ескалювати клієнту C-level без DM (див. C23).

## Company methodology

`knowledge/pmo-kb/05-monitoring-controlling/e13-escalation-memo.md`  
`knowledge/pmo-kb/03-planning/c23-escalation-matrix.md`
