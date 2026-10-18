# -*- coding: utf-8 -*-
"""Валидатор данных карты взаимодействия.

Проверяет по JSON-схемам из schema/ (мини-валидатор draft-07 без внешних
зависимостей; поддержано подмножество, которое используют схемы проекта:
type, required, additionalProperties, enum, const, pattern, maxLength,
minItems, items, $ref на taxonomy.json и внутренние ссылки).

Плюс перекрёстные проверки, которые схемой не выражаются:
  - уникальность id, имя файла == id, «нумерологические» дубли ORG-001/ORG-0001;
  - asserted => asserted_date; утверждённая позиция => источник с url;
  - уникальность пары в connections.json;
  - карточка: date, summary; приоритет A/B => есть facts.

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
CARDS_DIR = os.path.join(ROOT, 'data', 'cards')
SCHEMA_DIR = os.path.join(ROOT, 'schema')
CONNECTIONS = os.path.join(ROOT, 'data', 'connections.json')

TAX = json.load(open(os.path.join(ROOT, 'taxonomy.json'), encoding='utf-8'))
DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')

_TAX_REF = re.compile(r'^file:taxonomy\.json#/(.+)$')


def load_schema(name):
    return json.load(open(os.path.join(SCHEMA_DIR, name), encoding='utf-8'))


def _resolve_pointer(root, pointer):
    node = root
    for raw in pointer.lstrip('#/').split('/'):
        part = raw.replace('~1', '/').replace('~0', '~')
        node = node[part]
    return node


def _check(node, schema, path, errors, root):
    ref = schema.get('$ref')
    if ref:
        m = _TAX_REF.match(ref)
        if m:
            allowed = TAX.get(m.group(1))
            if isinstance(allowed, list) and node not in allowed:
                errors.append('%s: %r нет в taxonomy.%s' % (path, node, m.group(1)))
            return
        if ref.startswith('#/'):
            _check(node, _resolve_pointer(root, ref), path, errors, root)
            return
        errors.append('%s: неразрешимая ссылка %r' % (path, ref))
        return

    t = schema.get('type')
    if t:
        ok = {
            'object': isinstance(node, dict),
            'array': isinstance(node, list),
            'string': isinstance(node, str),
            'boolean': isinstance(node, bool),
            'integer': isinstance(node, int) and not isinstance(node, bool),
            'number': isinstance(node, (int, float)) and not isinstance(node, bool),
            'null': node is None,
        }.get(t, True)
        if not ok:
            errors.append('%s: ожидался %s, получен %s' % (path, t, type(node).__name__))
            return

    if 'const' in schema and node != schema['const']:
        errors.append('%s: ожидалось %r, получено %r' % (path, schema['const'], node))
    if 'enum' in schema and node not in schema['enum']:
        errors.append('%s: %r не входит в %r' % (path, node, schema['enum']))

    if isinstance(node, str):
        if 'pattern' in schema and not re.search(schema['pattern'], node):
            errors.append('%s: %r не соответствует %r' % (path, node, schema['pattern']))
        if 'maxLength' in schema and len(node) > schema['maxLength']:
            errors.append('%s: длина %d > %d' % (path, len(node), schema['maxLength']))

    if isinstance(node, dict):
        for req in schema.get('required', []):
            if req not in node:
                errors.append('%s: отсутствует обязательное поле %r' % (path, req))
        props = schema.get('properties', {})
        if schema.get('additionalProperties') is False:
            for key in node:
                if key not in props:
                    errors.append('%s: неизвестное поле %r' % (path, key))
        for key, sub in props.items():
            if key in node:
                _check(node[key], sub, '%s.%s' % (path, key) if path else key, errors, root)

    if isinstance(node, list):
        if 'minItems' in schema and len(node) < schema['minItems']:
            errors.append('%s: элементов %d < %d' % (path, len(node), schema['minItems']))
        item = schema.get('items')
        if item:
            for i, val in enumerate(node):
                _check(val, item, '%s[%d]' % (path, i), errors, root)


def load_orgs(errors=None):
    """Читает паспорта: битый JSON и дубликаты id — ошибки, а не падение.

    errors необязателен: build_site.py и match.py вызывают load_orgs() без него.
    """
    if errors is None:
        errors = []
    orgs, files = {}, {}
    for fn in sorted(os.listdir(ORGS_DIR)):
        if not fn.endswith('.json'):
            continue
        try:
            rec = json.load(open(os.path.join(ORGS_DIR, fn), encoding='utf-8'))
        except json.JSONDecodeError as e:
            errors.append('%s: битый JSON (%s)' % (fn, e))
            continue
        oid = rec.get('id')
        if not isinstance(oid, str):
            errors.append('%s: id отсутствует или не строка' % fn)
            continue
        if oid in orgs:
            errors.append('%s: дубликат id %s (уже объявлен в %s)' % (fn, oid, files[oid]))
            continue
        if fn[:-len('.json')] != oid:
            errors.append('%s: имя файла не совпадает с id %s' % (fn, oid))
        orgs[oid] = rec
        files[oid] = fn

    # ORG-001 и ORG-0001 — один и тот же номер в разной ширине
    seen = {}
    for oid in orgs:
        m = re.match(r'^ORG-(\d+)$', oid)
        if not m:
            continue
        num = int(m.group(1))
        if num in seen:
            errors.append('%s и %s: один номер %d в разной ширине' % (seen[num], oid, num))
        else:
            seen[num] = oid
    return orgs


def check_org(rec, errors, schema):
    oid = rec.get('id', '?')
    _check(rec, schema, oid, errors, schema)
    if rec.get('asserted') and not DATE_RE.match(str(rec.get('asserted_date', ''))):
        errors.append('%s: утверждённый паспорт требует asserted_date (ГГГГ-ММ-ДД)' % oid)
    for i, pos in enumerate(rec.get('positions') or []):
        if pos.get('status') == 'asserted' and not (pos.get('sources') or []):
            errors.append('%s: позиция %d (%r) утверждена без источника'
                          % (oid, i, pos.get('topic')))
        for j, src in enumerate(pos.get('sources') or []):
            if not str((src or {}).get('url') or '').strip():
                errors.append('%s: позиция %d, источник %d — пустой url' % (oid, i, j))


def check_card(card, orgs, errors, schema):
    cid = '%s←%s' % (card.get('org_id'), (card.get('researcher') or {}).get('name', '?'))
    _check(card, schema, 'карточка %s' % cid, errors, schema)
    if card.get('org_id') not in orgs:
        errors.append('карточка %s: org_id не найден в реестре' % cid)
    if not DATE_RE.match(str(card.get('date', ''))):
        errors.append('карточка %s: date должна быть ГГГГ-ММ-ДД' % cid)
    pr = card.get('priority') or {}
    if pr.get('category') in ('A', 'B') and not (card.get('facts') or []):
        errors.append('карточка %s: приоритет A/B без фактов не принимается' % cid)


def check_connections(conns, orgs, errors, schema):
    seen_pairs = {}
    for i, c in enumerate(conns):
        path = 'связь #%d' % (i + 1)
        _check(c, schema, path, errors, schema)
        parts = c.get('participants') or []
        for p in parts:
            if p not in orgs:
                errors.append('%s: участник %s не найден в реестре' % (path, p))
        if len(set(parts)) != len(parts):
            errors.append('%s: участник указан дважды' % path)
        key = tuple(sorted(parts))
        if len(key) == 2:
            if key in seen_pairs:
                errors.append('%s: дубликат пары (уже есть связь #%d)' % (path, seen_pairs[key]))
            else:
                seen_pairs[key] = i + 1


def main(argv):
    errors = []
    org_schema = load_schema('orgpass.schema.json')
    conn_schema = load_schema('connection.schema.json')
    card_schema = load_schema('research-card.schema.json')

    orgs = load_orgs(errors)
    target = argv[1] if len(argv) > 1 else None

    checked = 0
    for oid, rec in orgs.items():
        if target and oid != target:
            continue
        check_org(rec, errors, org_schema)
        checked += 1

    if os.path.isdir(CARDS_DIR):
        for fn in sorted(os.listdir(CARDS_DIR)):
            if not fn.endswith('.jsonl'):
                continue
            for ln, line in enumerate(open(os.path.join(CARDS_DIR, fn), encoding='utf-8'), 1):
                if not line.strip():
                    continue
                try:
                    check_card(json.loads(line), orgs, errors, card_schema)
                except json.JSONDecodeError as e:
                    errors.append('%s:%d: битый JSON (%s)' % (fn, ln, e))

    try:
        conns = json.load(open(CONNECTIONS, encoding='utf-8'))
    except json.JSONDecodeError as e:
        errors.append('connections.json: битый JSON (%s)' % e)
        conns = []
    if not isinstance(conns, list):
        errors.append('connections.json: ожидался массив')
        conns = []
    check_connections(conns, orgs, errors, conn_schema)

    print('Проверено: %d организаций, %d связей' % (checked, len(conns)))
    if errors:
        print('ОШИБКИ (%d):' % len(errors))
        for e in errors[:80]:
            print('  -', e)
        if len(errors) > 80:
            print('  … ещё %d (показаны первые 80)' % (len(errors) - 80))
        return 1
    print('Ошибок нет.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
