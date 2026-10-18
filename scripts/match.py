# -*- coding: utf-8 -*-
"""Матч-отчёт: с чем две организации могут взаимодействовать прямо сейчас.

Сопоставляет два паспорта и выдаёт: взаимодополняемость (offers × seeks),
позиции по общим темам (только где обе стороны их заявили), общие типы
деятельности, рекомендованные форматы и черновик первого обращения.
Система не выносит вердиктов: расхождения показываются, а не оцениваются.

Запуск:  python scripts/match.py ORG-000 ORG-029            # текст
         python scripts/match.py ORG-000 ORG-029 --json     # JSON
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate import load_orgs, ROOT  # noqa: E402
from interop_common import acts_of, shared_acts, hypothetical_formats  # noqa: E402

TAX = json.load(open(os.path.join(ROOT, 'taxonomy.json'), encoding='utf-8'))
TOPIC = TAX['position_topic_labels']
FMT = TAX['interaction_format_labels']
ACT = TAX['activity_type_labels']


def fmt_list(items):
    return [i.get('format') for i in (items or []) if i.get('format')]


def match(a, b):
    ca, cb = a.get('cooperation') or {}, b.get('cooperation') or {}
    complement = sorted(
        set(fmt_list(ca.get('offers'))) & set(fmt_list(cb.get('seeks'))) |
        set(fmt_list(cb.get('offers'))) & set(fmt_list(ca.get('seeks'))))
    pa = {p['topic']: p for p in a.get('positions') or [] if p.get('status') == 'asserted'}
    pb = {p['topic']: p for p in b.get('positions') or [] if p.get('status') == 'asserted'}
    both = sorted(set(pa) & set(pb))
    positions = [{
        'topic': t,
        'a': pa[t].get('stance'),
        'b': pb[t].get('stance'),
        'a_source': (pa[t].get('sources') or [{}])[0].get('url'),
        'b_source': (pb[t].get('sources') or [{}])[0].get('url'),
    } for t in both]
    acts_all_a = acts_of(a)
    acts_all_b = acts_of(b)
    common_acts = shared_acts(a, b)
    common_declared = sorted({x.get('type') for x in a.get('activities') or []}
                             & {x.get('type') for x in b.get('activities') or []})
    hyp = hypothetical_formats(a, b)
    formats = list(complement)
    for f in hyp:
        if f not in formats:
            formats.append(f)
    if not formats:
        formats = ['open_discussion']
    open_questions = []
    if not (a.get('channels') or {}).get('email') and not (a.get('channels') or {}).get('telegram'):
        open_questions.append('У %s не указан публичный контакт' % a['identity']['name'])
    if not (b.get('channels') or {}).get('email') and not (b.get('channels') or {}).get('telegram'):
        open_questions.append('У %s не указан публичный контакт' % b['identity']['name'])
    for t in sorted(set(pa) | set(pb)):
        if t not in both:
            open_questions.append('Тема «%s»: заявлена только одной стороной — уточнить у второй' % TOPIC.get(t, t))
    return {
        'pair': [a['id'], b['id']],
        'names': [a['identity']['name'], b['identity']['name']],
        'asserted': [a.get('asserted'), b.get('asserted')],
        'complementary_formats': complement,
        'hypothetical_formats': hyp,
        'shared_activities_all': [ACT.get(x, x) for x in common_acts],
        'shared_positions': positions,
        'shared_positions_count': len(both),
        'common_activities': [ACT.get(x, x) for x in common_declared],
        'recommended_formats': [FMT.get(f, f) for f in formats],
        'open_questions': open_questions,
        'draft_letter': draft_letter(a, b, formats, common_acts),
    }


def draft_letter(a, b, formats, common_acts):
    """Черновик первого обращения.

    Не приписывает сторонам того, чего нет в паспорте: если вклада или общего
    поля в данных нет — остаётся явная пометка для заполнения, а не выдумка.
    """
    offer_fmt = FMT.get(formats[0], formats[0]) if formats else None
    acts_ru = ', '.join(ACT.get(x, x) for x in common_acts[:2])
    offers = (a.get('cooperation') or {}).get('offers') or []
    our_offer = next((o.get('description') for o in offers
                      if o.get('format') == formats[0]), None) if formats else None

    L = ['Здравствуйте, %s!' % b['identity']['name'], '']
    L.append('Мы — %s (%s).' % (a['identity']['name'],
                                (a.get('channels') or {}).get('site') or 'наш сайт'))
    if acts_ru:
        L.append('В ваших открытых материалах и нашей работе есть общее поле: %s.' % acts_ru)
    if offer_fmt:
        L.append('Предлагаем начать с малого и конкретного: %s.' % offer_fmt.lower())
    if our_offer:
        L.append('Наш вклад — %s.' % our_offer.rstrip('.'))
    else:
        L.append('Наш вклад: [указать, что конкретно готовы дать — в паспорте это не зафиксировано].')
    L.append('Что было бы полезно от вас?')
    L.append('')
    L.append('Если тема интересна — ответьте, и согласуем формат и сроки.')
    return '\n'.join(L)


def render_text(r):
    a, b = r['names']
    L = []
    L.append('МАТЧ-ОТЧЁТ: %s ↔ %s' % (a, b))
    L.append('=' * 60)
    st = lambda f: 'утверждён' if f else 'черновик (не утверждён организацией)'
    L.append('Статус паспортов: %s — %s; %s — %s' % (a, st(r['asserted'][0]), b, st(r['asserted'][1])))
    L.append('')
    L.append('▌ Взаимодополняемость (offers × seeks):')
    L.append('  ' + (', '.join(FMT.get(f, f) for f in r['complementary_formats']) if r['complementary_formats'] else 'не заявлена — паспорта молчат, это не отказ'))
    L.append('')
    L.append('▌ Позиции по общим темам (обе стороны заявили): %d' % r['shared_positions_count'])
    for p in r['shared_positions']:
        L.append('  • %s' % TOPIC.get(p['topic'], p['topic']))
        L.append('    %s: %s' % (a, (p['a'] or '')[:160]))
        L.append('      %s' % (p['a_source'] or ''))
        L.append('    %s: %s' % (b, (p['b'] or '')[:160]))
        L.append('      %s' % (p['b_source'] or ''))
        L.append('    → сопоставление формулировок остаётся за читателем; расхождение — предмет разговора, не приговор')
    L.append('')
    L.append('▌ Общая деятельность (заявленная): ' + (', '.join(r['common_activities']) or 'не заявлена'))
    L.append('')
    L.append('▌ Гипотетический слой (по ролям организаций, не по заявлениям):')
    L.append('  возможные форматы: ' + (', '.join(FMT.get(f, f) for f in r['hypothetical_formats']) if r['hypothetical_formats'] else 'не найдено'))
    L.append('  общие сферы (вкл. выведенные): ' + (', '.join(r['shared_activities_all']) or 'не найдено'))
    L.append('  → это гипотеза для первого разговора, а не факт и не оценка совместимости')
    L.append('')
    L.append('▌ Рекомендованные форматы первого проекта (заявленное + возможное):')
    for f in r['recommended_formats']:
        L.append('  - %s' % f)
    L.append('')
    L.append('▌ Открытые вопросы:')
    for q in r['open_questions'] or ['нет']:
        L.append('  - %s' % q)
    L.append('')
    L.append('▌ Черновик первого обращения:')
    L.append('---')
    L.append(r['draft_letter'])
    L.append('---')
    L.append('')
    L.append('Методология: факты отделены от оценок; «не установлено» — штатное состояние.')
    L.append('Этот отчёт — сопоставление заявленного, а не приговор о совместимости.')
    return '\n'.join(L)


def main(argv):
    args = [a for a in argv[1:] if not a.startswith('--')]
    as_json = '--json' in argv
    if len(args) != 2:
        print(__doc__)
        return 2
    all_orgs = load_orgs()
    # restricted не участвует в матчинге: паспорт скрыт, в реестре только строка «существует»
    restricted = {k for k, v in all_orgs.items()
                  if (v.get('visibility') or {}).get('level') == 'restricted'}
    orgs = {k: v for k, v in all_orgs.items() if k not in restricted}
    for x in args:
        if x in restricted:
            print('%s: паспорт ограничен (visibility=restricted) — матч-отчёт не строится' % x)
            return 2
        if x not in orgs:
            print('Не найдено: %s' % x)
            return 2
    r = match(orgs[args[0]], orgs[args[1]])
    print(json.dumps(r, ensure_ascii=False, indent=1) if as_json else render_text(r))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
