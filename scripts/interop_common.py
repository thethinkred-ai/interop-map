# -*- coding: utf-8 -*-
"""Общий модуль гипотетического слоя: единственный источник матрицы
«роль × роль → формат» и вывода сфер деятельности из раздела списка.

Используется и сайтом (build_site.py инжектит матрицу в JS),
и CLI (match.py печатает гипотетические форматы) — чтобы оценки нигде
не расходились между витриной и отчётом.
"""

# Сферы деятельности черновиков выводятся из раздела списка-посева.
# Это оценка «кто они есть» по открытым данным, а не заявление организации —
# на витрине такие сферы помечаются «по разделу списка».
SECTION_ACTS = {
    'Системные структуры': ['party_politics'],
    'Несистемные коммунистические партии и движения': ['party_politics', 'grassroots_politics'],
    'Несистемные левые и социалистические': ['grassroots_politics', 'party_politics'],
    'Молодёжные организации': ['grassroots_politics', 'education'],
    'Профсоюзы и рабочие объединения': ['trade_unions', 'labour_conflicts'],
    'Международные партии и форматы': ['party_politics', 'events'],
    'Медиа-проекты и площадки': ['media', 'publishing'],
    'Русскоязычные YouTube-каналы': ['media', 'publishing'],
    'Зарубежные каналы и медиапроекты': ['media', 'translation'],
    'Telegram-каналы и блоги': ['media'],
    'Библиотеки и архивы первоисточников': ['library_archive', 'publishing'],
    'Образовательные проекты и школы': ['education', 'research'],
    'ВКонтакте: сообщества': ['media', 'grassroots_politics'],
    'Страны СНГ: организации и проекты': ['grassroots_politics', 'party_politics'],
}

# Матрица «роль × роль → возможный формат». Пары направлений [A, B]:
# у одной организации есть роль A, у другой B — значит, возможен формат.
FMT_MATRIX = [
    [['education', 'media'],            'joint_seminar'],
    [['education', 'publishing'],       'joint_collection'],
    [['education', 'library_archive'],  'joint_collection'],
    [['education', 'education'],        'joint_seminar'],
    [['education', 'trade_unions'],     'joint_seminar'],
    [['education', 'labour_conflicts'], 'joint_seminar'],
    [['education', 'research'],         'joint_analytics'],
    [['media', 'media'],                'exchange_publications'],
    [['media', 'publishing'],           'exchange_publications'],
    [['media', 'labour_conflicts'],     'labour_monitoring_exchange'],
    [['media', 'trade_unions'],         'labour_monitoring_exchange'],
    [['media', 'translation'],          'translation_project'],
    [['publishing', 'library_archive'], 'joint_collection'],
    [['publishing', 'translation'],     'translation_project'],
    [['research', 'party_politics'],    'joint_analytics'],
    [['research', 'research'],          'comparative_research'],
    [['trade_unions', 'party_politics'], 'joint_campaign'],
    [['trade_unions', 'labour_conflicts'], 'labour_monitoring_exchange'],
    [['events', 'media'],               'joint_seminar'],
    [['events', 'events'],              'conference'],
    [['software', 'education'],         'caos_shared_goal'],
    [['software', 'grassroots_politics'], 'caos_shared_goal'],
    [['software', 'party_politics'],    'caos_shared_goal'],
    [['translation', 'library_archive'], 'translation_project'],
]


def acts_of(org):
    """Все сферы организации: заявленные в паспорте + выведенные из раздела.

    Понимает оба формата: бандл витрины (acts / acts_inferred) и сырой
    паспорт (activities[].type + meta.list_section).
    """
    s = {}
    if 'acts' in org:
        for x in org.get('acts') or []:
            s[x] = 1
    else:
        for x in org.get('activities') or []:
            if x.get('type'):
                s[x['type']] = 1
    if 'acts_inferred' in org:
        for x in org.get('acts_inferred') or []:
            s[x] = 1
    else:
        sec = (org.get('meta') or {}).get('list_section') or ''
        for x in SECTION_ACTS.get(sec, []):
            s[x] = 1
    return s


def shared_acts(a, b):
    A, B = acts_of(a), acts_of(b)
    return sorted(A.keys() & B.keys())


def hypothetical_formats(a, b):
    """Форматы, возможные для пары по матрице ролей (без заявленного)."""
    A, B = acts_of(a), acts_of(b)
    out = []
    for pair, fmt in FMT_MATRIX:
        x, y = pair
        if ((A.get(x) and B.get(y)) or (B.get(x) and A.get(y))) and fmt not in out:
            out.append(fmt)
    return out
