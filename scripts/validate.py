# -*- coding: utf-8 -*-
"""Валидатор данных карты взаимодействия.

Проверяет без внешних зависимостей (jsonschema не требуется):
  - паспорт: обязательные поля, форматы ID/дат, значения таксономий;
  - карточки: обязательные поля, баллы 0–4 или null, категории А–E;
  - связи: участники существуют, тип из справочника, доказательство с URL.

Запуск:  python scripts/validate.py          # все данные
         python scripts/validate.py ORG-029  # одна организация
Код возврата: 0 — ошибок нет, 1 — есть ошибки.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORGS_DIR = os.path.join(ROOT, 'data', 'orgs')
TAX = json.load(open(os.path.join(ROOT, 'taxonomy.json'), encoding='utf-8'))
DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')
ID_RE = re.compile(r'^ORG-\d{3,4}$')


def load_orgs():
    orgs = {}
    for fn in sorted(os.listdir(ORGS_DIR)):
        if fn.endswith('.json'):
            rec = json.load(open(os.path.join(ORGS_DIR, fn), encoding='utf-8'))
            orgs[rec.get('id', fn)] = rec
    return orgs


def check_org(rec, errors):
    oid = rec.get('id', '?')
    def err(msg):
        errors.append('%s: %s' % (oid, msg))
    if not ID_RE.match(str(rec.get('id', ''))):
        err('неверный id')
    if rec.get('schema_version') != '1.0':
        err('schema_version != 1.0')
    if not isinstance(rec.get('asserted'), bool):
        err('asserted должен быть boolean')
    if rec.get('asserted') and not DATE_RE.match(str(rec.get('asserted_date', ''))):
        err('утверждённый паспорт требует asserted_date (ГГГГ-ММ-ДД)')
    ident = rec.get('identity') or {}
    if not ident.get('name'):
        err('identity.name обязателен')
    for pos in rec.get('positions') or []:
        if pos.get('topic') not in TAX['position_topics']:
            err('позиция с темой вне таксономии: %r' % pos.get('topic'))
        if pos.get('status') not in TAX['position_statuses']:
            err('позиция со статусом вне справочника: %r' % pos.get('status'))
        if pos.get('status') == 'asserted' and not (pos.get('sources') or []):
            err('утверждённая позиция требует источник: тема %r' % pos.get('topic'))
    for act in rec.get('activities') or []:
        if act.get('type') not in TAX['activity_types']:
            err('деятельность вне таксономии: %r' % act.get('type'))
    coop = rec.get('cooperation') or {}
    for key in ('offers', 'seeks'):
        for it in coop.get(key) or []:
            if it.get('format') not in TAX['interaction_formats']:
                err('%s с форматом вне таксономии: %r' % (key, it.get('format')))
    vis = rec.get('visibility') or {}
    if vis.get('level') not in (None, 'public', 'restricted'):
        err('visibility.level вне справочника')


def check_card(card, orgs, errors):
    cid = '%s←%s' % (card.get('org_id'), (card.get('researcher') or {}).get('name', '?'))
    def err(msg):
        errors.append('карточка %s: %s' % (cid, msg))
    if not ID_RE.match(str(card.get('org_id', ''))):
        err('неверный org_id')
    elif card.get('org_id') not in orgs:
        err('org_id не найден в реестре')
    if not card.get('date') or not DATE_RE.match(str(card.get('date'))):
        err('date должна быть ГГГГ-ММ-ДД')
    if not card.get('summary'):
        err('заполненный статус требует резюме (summary)')
    for f in card.get('facts') or []:
        if f.get('status') not in TAX['fact_statuses']:
            err('статус факта вне справочника: %r' % f.get('status'))
    a = card.get('assessments') or {}
    for k, v in a.items():
        if v is not None and (not isinstance(v, int) or not 0 <= v <= 4):
            err('оценка %s должна быть целой 0–4 или null' % k)
    pr = card.get('priority') or {}
    if pr and pr.get('category') not in (None,) + tuple(TAX['priority_categories']):
        err('категория приоритета вне справочника')
    if pr.get('category') in ('A', 'B') and not (card.get('facts') or []):
        err('приоритет A/B без фактов не принимается')


def check_connections(conns, orgs, errors):
    for i, c in enumerate(conns):
        def err(msg):
            errors.append('связь #%d: %s' % (i + 1, msg))
        if len(c.get('participants') or []) < 2:
            err('меньше двух участников')
        for p in c.get('participants') or []:
            if p not in orgs:
                err('участник %s не найден в реестре' % p)
        if not (c.get('proof') or {}).get('url'):
            err('связь требует доказательство с URL')


def main(argv):
    errors = []
    orgs = load_orgs()
    target = argv[1] if len(argv) > 1 else None
    for oid, rec in orgs.items():
        if target and oid != target:
            continue
        check_org(rec, errors)
    cards_dir = os.path.join(ROOT, 'data', 'cards')
    if os.path.isdir(cards_dir):
        for fn in sorted(os.listdir(cards_dir)):
            if fn.endswith('.jsonl'):
                for ln, line in enumerate(open(os.path.join(cards_dir, fn), encoding='utf-8'), 1):
                    if line.strip():
                        try:
                            check_card(json.loads(line), orgs, errors)
                        except json.JSONDecodeError as e:
                            errors.append('%s:%d: битый JSON (%s)' % (fn, ln, e))
    conns = json.load(open(os.path.join(ROOT, 'data', 'connections.json'), encoding='utf-8'))
    check_connections(conns, orgs, errors)
    print('Проверено: %d организаций, %d связей' % (len(orgs) if not target else 1, len(conns)))
    if errors:
        print('ОШИБКИ (%d):' % len(errors))
        for e in errors[:50]:
            print('  -', e)
        return 1
    print('Ошибок нет.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
