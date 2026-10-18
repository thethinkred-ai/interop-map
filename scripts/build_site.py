# -*- coding: utf-8 -*-
"""Генератор статической витрины → docs/index.html (для GitHub Pages).

Витрина самодостаточна: все данные вшиты одним JSON-блобом, матч-отчёт
считается в браузере (логика mirror scripts/match.py, упрощённая).
Запуск:  python scripts/build_site.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate import load_orgs, ROOT  # noqa: E402

TAX = json.load(open(os.path.join(ROOT, 'taxonomy.json'), encoding='utf-8'))

CAT_COLORS = {'A': '#16a34a', 'B': '#eab308', 'C': '#f97316', 'D': '#3b82f6', 'E': '#dc2626'}
CAT_LABELS = {'A': 'первоочередной контакт', 'B': 'перспективный', 'C': 'точечные кампании',
              'D': 'наблюдение', 'E': 'не взаимодействуем'}


def bundle():
    orgs = []
    for oid, rec in sorted(load_orgs().items()):
        if (rec.get('visibility') or {}).get('level') == 'restricted':
            orgs.append({'id': oid, 'name': rec['identity'].get('name', oid),
                         'restricted': True, 'asserted': rec.get('asserted')})
            continue
        orgs.append({
            'id': oid,
            'name': rec['identity'].get('name', oid),
            'asserted': rec.get('asserted'),
            'section': (rec.get('meta') or {}).get('list_section') or '',
            'form': rec['identity'].get('legal_form') or '',
            'status': rec['identity'].get('status') or '',
            'site': (rec.get('channels') or {}).get('site') or '',
            'category': (rec.get('meta') or {}).get('page_category'),
            'page_status': (rec.get('meta') or {}).get('page_status') or '',
            'notes': (rec.get('meta') or {}).get('notes') or '',
            'acts': [a.get('type') for a in rec.get('activities') or []],
            'offers': [(o.get('format'), o.get('description')) for o in (rec.get('cooperation') or {}).get('offers') or []],
            'seeks': [(o.get('format'), o.get('description')) for o in (rec.get('cooperation') or {}).get('seeks') or []],
            'positions': [(p.get('topic'), p.get('status')) for p in rec.get('positions') or []],
        })
    conns = json.load(open(os.path.join(ROOT, 'data', 'connections.json'), encoding='utf-8'))
    return {'orgs': orgs, 'connections': len(conns), 'tax': TAX,
            'updated': '2026-10-18'}


HTML = '''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Карта взаимодействия — открытый сервис для организаций движения</title>
<meta name="description" content="Открытая карта: кто есть кто, кто что предлагает и ищет, с кем по каким темам возможно взаимодействие. Факты отделены от оценок, глобальных рейтингов нет.">
<style>
:root{--red:#c8102e;--ink:#1a1a2e;--text:#374151;--muted:#6b7280;--bg:#f8f9fa;--card:#fff;--border:#e5e7eb}
*{box-sizing:border-box}
body{margin:0;font:16px/1.6 -apple-system,'Segoe UI',Roboto,Arial,sans-serif;color:var(--text);background:var(--bg)}
a{color:var(--red)}
.wrap{max-width:1080px;margin:0 auto;padding:0 20px}
header{background:var(--ink);color:#fff;padding:26px 0 30px}
header h1{margin:0 0 6px;font-size:30px}
header h1 span{color:#ff6b81}
header p{margin:0;color:#d1d5db;max-width:820px}
.badge{display:inline-block;background:rgba(255,255,255,.12);border-radius:999px;padding:2px 12px;font-size:13px;margin-bottom:10px}
.principles{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;margin:18px 0 6px}
.principle{background:rgba(255,255,255,.07);border-radius:10px;padding:12px 16px;font-size:14px;color:#e5e7eb}
.principle b{display:block;color:#fff;margin-bottom:4px}
.toolbar{display:flex;flex-wrap:wrap;gap:10px;margin:18px 0}
.toolbar input,.toolbar select{padding:9px 12px;border:1px solid var(--border);border-radius:8px;font-size:14px;background:var(--card)}
#q{flex:1;min-width:220px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:14px}
.card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:16px;display:flex;flex-direction:column}
.card h3{margin:0 0 4px;font-size:16px;color:var(--ink)}
.cat{display:inline-block;font-size:11px;font-weight:700;border-radius:999px;padding:2px 9px;margin-bottom:6px;color:#fff}
.meta{font-size:12px;color:var(--muted);margin-bottom:8px}
.stat{font-size:13px;margin:0 0 6px}
.stat b{font-weight:600}
.draft{font-size:12px;color:#92400e;background:#fef3c7;border-radius:6px;padding:2px 8px;display:inline-block;margin-bottom:6px}
.ok{font-size:12px;color:#166534;background:#dcfce7;border-radius:6px;padding:2px 8px;display:inline-block;margin-bottom:6px}
.link{margin-top:auto;font-size:13px;font-weight:600}
section.match{background:#fff;border:1px solid var(--border);border-radius:14px;padding:20px;margin:26px 0}
section.match h2{margin:0 0 4px;font-size:20px;color:var(--ink)}
.matchrow{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-top:12px}
.matchrow select{flex:1;min-width:200px;padding:9px 12px;border:1px solid var(--border);border-radius:8px;font-size:14px}
#report{margin-top:14px;font-size:14px;white-space:pre-wrap;background:var(--bg);border-radius:10px;padding:14px;display:none}
footer{margin:40px 0 30px;color:var(--muted);font-size:13px;border-top:1px solid var(--border);padding-top:16px}
.count{color:var(--muted);font-size:13px;margin:0 0 12px}
</style>
</head>
<body>
<header>
  <div class="wrap">
    <span class="badge">Открытый сервис · методология ThinkRed · данные под MIT</span>
    <h1>Карта <span>взаимодействия</span></h1>
    <p>Кто есть кто в движении, кто что предлагает и ищет, с кем по каким темам возможно взаимодействие — по заявлениям самих организаций, с источниками.</p>
    <div class="principles">
      <div class="principle"><b>Без рейтингов и ярлыков</b>Система не вычисляет «ортодоксальность» и не ранжирует организации. Только попарные отчёты.</div>
      <div class="principle"><b>Голос организации</b>Паспорт утверждает сама организация. Черновики по открытым данным помечены явно.</div>
      <div class="principle"><b>«Не установлено» — норма</b>Молчание паспорта — не отказ и не согласие. Факты отделены от оценок.</div>
    </div>
  </div>
</header>
<main class="wrap">
  <section class="match">
    <h2>Матч-отчёт двух организаций</h2>
    <p style="margin:0;color:var(--muted);font-size:14px">Выберите две организации — отчёт покажет взаимодополняемость, общие темы, рекомендованные форматы и черновик первого письма.</p>
    <div class="matchrow">
      <select id="mA"></select>
      <span>↔</span>
      <select id="mB"></select>
      <button onclick="doMatch()" style="padding:9px 18px;background:var(--red);color:#fff;border:0;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer">Сопоставить</button>
    </div>
    <div id="report"></div>
  </section>

  <div class="toolbar">
    <input id="q" type="search" placeholder="Поиск по названию…">
    <select id="fCat"><option value="">Все категории</option></select>
    <select id="fSec"><option value="">Все разделы</option></select>
    <select id="fOnly"><option value="">Все паспорта</option><option value="asserted">Только утверждённые</option></select>
  </div>
  <p class="count" id="count"></p>
  <div class="grid" id="grid"></div>

  <footer>
    <p><b>Как участвовать:</b> проверьте карточку своей организации и утвердите паспорт — 30 минут по инструкции в репозитории.
    Формат данных и код — свободные (MIT): <a href="https://github.com/thethinkred-ai/interop-map" target="_blank" rel="noopener">github.com/thethinkred-ai/interop-map</a>.
    Методология: <a href="https://github.com/thethinkred-ai/interop-map/blob/main/handbook/METHODOLOGY.md" target="_blank" rel="noopener">как устроены карточки и оценки</a>.</p>
    <p>Данные-посев: публичная карта взаимодействия ThinkRed (снимок 17.10.2026, 209 организаций) + паспорт ThinkRed. Обновлено: <span id="upd"></span>. Удаление своей организации из реестра — по первому запросу.</p>
  </footer>
</main>
<script>
var DATA = __BUNDLE__;
var CATC = __CATC__, CATL = __CATL__, FMT = DATA.tax.interaction_format_labels, ACT = DATA.tax.activity_type_labels, TOPIC = DATA.tax.position_topic_labels;
document.getElementById('upd').textContent = DATA.updated;

function fill(sel, filterSel){ var s=document.getElementById(sel); DATA.orgs.forEach(function(o){ if(o.restricted) return; var op=document.createElement('option'); op.value=o.id; op.textContent=o.name+' ('+o.id+')'; s.appendChild(op); }); }
fill('mA'); fill('mB');
document.getElementById('mA').value='ORG-000';
document.getElementById('mB').value='ORG-029';

function doMatch(){
  var byId={}; DATA.orgs.forEach(function(o){byId[o.id]=o;});
  var a=byId[document.getElementById('mA').value], b=byId[document.getElementById('mB').value];
  var comp = (a.offers||[]).map(function(x){return x[0];}).filter(function(f){return (b.seeks||[]).some(function(x){return x[0]===f;});})
    .concat((b.offers||[]).map(function(x){return x[0];}).filter(function(f){return (a.seeks||[]).some(function(x){return x[0]===f;});}));
  var pa={}, pb={}; (a.positions||[]).forEach(function(p){if(p[1]==='asserted')pa[p[0]]=1;}); (b.positions||[]).forEach(function(p){if(p[1]==='asserted')pb[p[0]]=1;});
  var both=Object.keys(pa).filter(function(t){return pb[t];});
  var actsA={}, actsB={}; (a.acts||[]).forEach(function(x){actsA[x]=1;}); (b.acts||[]).forEach(function(x){actsB[x]=1;});
  var common=(a.acts||[]).filter(function(x){return actsB[x];});
  var formats=comp.slice();
  [[['labour_conflicts','trade_unions'],'labour_monitoring_exchange'],[['publishing','media'],'exchange_publications'],[['research'],'joint_analytics'],[['education'],'joint_seminar'],[['translation'],'translation_project'],[['events'],'open_discussion'],[['software'],'caos_shared_goal']].forEach(function(rule){
    if((rule[0].some(function(x){return actsA[x];})) && (rule[0].some(function(x){return actsB[x];})) && formats.indexOf(rule[1])<0) formats.push(rule[1]);
  });
  if(!formats.length) formats=['open_discussion'];
  var L=[];
  L.push('МАТЧ-ОТЧЁТ: '+a.name+' ('+a.id+') ↔ '+b.name+' ('+b.id+')');
  L.push('Статус паспортов: '+a.name+' — '+(a.asserted?'утверждён':'черновик')+'; '+b.name+' — '+(b.asserted?'утверждён':'черновик'));
  L.push('');
  L.push('▌ Взаимодополняемость (предложения × запросы):');
  L.push('  '+(comp.length?comp.map(function(f){return FMT[f]||f;}).join(', '):'не заявлена — это не отказ'));
  L.push('');
  L.push('▌ Общие темы с утверждёнными позициями обеих сторон: '+both.length);
  both.forEach(function(t){L.push('  • '+(TOPIC[t]||t)+' → сопоставьте формулировки в паспортах; расхождение — предмет разговора');});
  L.push('');
  L.push('▌ Общая деятельность: '+(common.length?common.map(function(x){return ACT[x]||x;}).join(', '):'не заявлена'));
  L.push('');
  L.push('▌ Рекомендованные форматы первого проекта:');
  formats.forEach(function(f){L.push('  – '+(FMT[f]||f));});
  L.push('');
  L.push('▌ Черновик первого обращения:');
  L.push('«Здравствуйте, '+b.name+'! Мы — '+a.name+'. Изучили ваши открытые материалы и видим общее поле: '+(common.length?common.map(function(x){return ACT[x]||x;}).slice(0,2).join(', '):'смежная деятельность')+'. Предлагаем начать с малого: '+((FMT[formats[0]]||formats[0]).toLowerCase())+'. Наш вклад — '+((a.offers||[])[0]?a.offers[0][1]:'материалы и площадка')+'. Что было бы полезно от вас?»');
  L.push('');
  L.push('Отчёт — сопоставление заявленного, а не приговор о совместимости. Паспорта-черновики молчат: заполните их.');
  var r=document.getElementById('report'); r.textContent=L.join('\\n'); r.style.display='block';
}

var fCat=document.getElementById('fCat'), fSec=document.getElementById('fSec'), fOnly=document.getElementById('fOnly');
Object.keys(CATL).forEach(function(k){var o=document.createElement('option');o.value=k;o.textContent=k+' — '+CATL[k];fCat.appendChild(o);});
var secs={}; DATA.orgs.forEach(function(o){if(o.section)secs[o.section]=1;});
Object.keys(secs).sort().forEach(function(s){var o=document.createElement('option');o.value=s;o.textContent=s;fSec.appendChild(o);});
[fCat,fSec,fOnly,document.getElementById('q')].forEach(function(el){el.addEventListener('input',render);});

function esc(s){return (s||'').replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
function render(){
  var q=document.getElementById('q').value.trim().toLowerCase();
  var cat=fCat.value, sec=fSec.value, only=fOnly.value;
  var g=document.getElementById('grid'); g.innerHTML=''; var n=0;
  DATA.orgs.forEach(function(o){
    if(o.restricted){return;}
    if(q && o.name.toLowerCase().indexOf(q)<0 && o.id.toLowerCase().indexOf(q)<0) return;
    if(cat && o.category!==cat) return;
    if(sec && o.section!==sec) return;
    if(only==='asserted' && !o.asserted) return;
    n++;
    var d=document.createElement('div'); d.className='card';
    var badge=o.asserted?'<span class="ok">паспорт утверждён</span>':'<span class="draft">черновик — не утверждён организацией</span>';
    var c=o.category?'<span class="cat" style="background:'+(CATC[o.category]||'#9ca3af')+'">Кат. '+o.category+' · '+CATL[o.category]+'</span>':'';
    d.innerHTML=badge+c+'<h3>'+esc(o.name)+'</h3><div class="meta">'+esc(o.id)+' · '+esc(o.section||'—')+(o.form?' · '+esc(o.form):'')+'</div>'
      +(o.acts.length?'<p class="stat"><b>Деятельность:</b> '+o.acts.map(function(x){return ACT[x]||x;}).join(', ')+'</p>':'')
      +(o.offers.length?'<p class="stat"><b>Предлагает:</b> '+o.offers.map(function(x){return FMT[x[0]]||x[0];}).join(', ')+'</p>':'')
      +(o.seeks.length?'<p class="stat"><b>Ищет:</b> '+o.seeks.map(function(x){return FMT[x[0]]||x[0];}).join(', ')+'</p>':'')
      +(o.site?'<a class="link" href="'+esc(o.site)+'" target="_blank" rel="noopener">Источник →</a>':'');
    g.appendChild(d);
  });
  document.getElementById('count').textContent='Показано '+n+' из '+DATA.orgs.length+' · подтверждённых связей в базе: '+DATA.connections;
}
render();
</script>
</body>
</html>
'''


def main():
    b = bundle()
    html = (HTML
            .replace('__BUNDLE__', json.dumps(b, ensure_ascii=False))
            .replace('__CATC__', json.dumps(CAT_COLORS, ensure_ascii=False))
            .replace('__CATL__', json.dumps(CAT_LABELS, ensure_ascii=False)))
    out = os.path.join(ROOT, 'docs', 'index.html')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'w', encoding='utf-8').write(html)
    print('site →', out, '(%.1f KB)' % (len(html.encode('utf-8')) / 1024))


if __name__ == '__main__':
    sys.exit(main())
