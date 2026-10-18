# -*- coding: utf-8 -*-
"""Конвертер данных-посева из снимка thinkred.ru/cooperation (2026-10-17).

Читает data/source/cooperation-snapshot-2026-10-17.json (снимок 209 карточек)
и генерирует data/orgs/ORG-001..ORG-209 — черновики паспортов (asserted=false).
ОРГ-000 (ThinkRed) пишется вручную и этим скриптом не трогается.

Запуск:  python scripts/seed_from_coop.py
"""
import json
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAPSHOT = os.path.join(ROOT, 'data', 'source', 'cooperation-snapshot-2026-10-17.json')
ORGS_DIR = os.path.join(ROOT, 'data', 'orgs')

CAT = {'green': 'A', 'yellow': 'B', 'orange': 'C', 'blue': 'D', 'gray': 'D', 'red': 'E'}


def norm_date(s):
    return s.replace('.', '-') if s else s


def main():
    cards = json.load(open(SNAPSHOT, encoding='utf-8'))
    if os.path.isdir(ORGS_DIR):
        for f in os.listdir(ORGS_DIR):
            if re.match(r'^ORG-(0[1-9]|[1-9][0-9])[0-9]\.json$', f):
                os.remove(os.path.join(ORGS_DIR, f))
    n = 0
    for i, c in enumerate(cards, 1):
        oid = 'ORG-%03d' % i
        link = (c.get('links') or [''])[0]
        rec = {
            'schema_version': '1.0',
            'id': oid,
            'asserted': False,
            'identity': {
                'name': c.get('name') or '',
                'status': '',
            },
            'channels': ({'site': link} if link else {}),
            'positions': [],
            'activities': [],
            'cooperation': {},
            'visibility': {'level': 'public', 'contacts_public': False},
            'meta': {
                'list_section': c.get('section') or '',
                'page_status': re.sub(r'^[^\wА-Яа-я]+', '', c.get('status_text') or '')[:80],
                'page_category': CAT.get(c.get('status')),
                'date_checked': norm_date('11.10.2026' if (c.get('name') or '').lower().startswith('redstarter') else '17.10.2026'),
                'source': 'thinkred.ru/cooperation (снимок 2026-10-17), карточка №%d' % i,
                'notes': (c.get('why') or '')[:600],
            },
        }
        if c.get('type'):
            rec['identity']['legal_form'] = (c.get('type') or '')[:160]
        if c.get('desc'):
            rec['identity']['status'] = (c.get('desc') or '')[:200]
        with open(os.path.join(ORGS_DIR, oid + '.json'), 'w', encoding='utf-8') as f:
            json.dump(rec, f, ensure_ascii=False, indent=1)
            f.write('\n')
        n += 1
    print('seed: %d черновиков → %s' % (n, ORGS_DIR))


if __name__ == '__main__':
    sys.exit(main())
