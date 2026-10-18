# -*- coding: utf-8 -*-
"""Генератор статической витрины → docs/index.html (для GitHub Pages и thinkred.ru/interop/).

Два вида: список организаций и организациоцентричная карта
(выбранная организация в центре, остальные — по радиусу согласно
заявленному результату взаимодействия). Матч-отчёты считаются в браузере.
Запуск:  python scripts/build_site.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate import load_orgs, ROOT  # noqa: E402
from interop_common import SECTION_ACTS, FMT_MATRIX  # noqa: E402

TAX = json.load(open(os.path.join(ROOT, 'taxonomy.json'), encoding='utf-8'))

CAT_COLORS = {'A': '#16a34a', 'B': '#eab308', 'C': '#f97316', 'D': '#3b82f6', 'E': '#dc2626'}
CAT_LABELS = {'A': 'первоочередной контакт', 'B': 'перспективный', 'C': 'точечные кампании',
              'D': 'наблюдение', 'E': 'не взаимодействуем'}

COOPERATIVE_LINKS = {'joint_project', 'coalition', 'publication_exchange', 'joint_event',
                     'international_network'}


def load_cards():
    """Карточки исследований по организациям: {org_id: [карточки]}."""
    cards_dir = os.path.join(ROOT, 'data', 'cards')
    out = {}
    if not os.path.isdir(cards_dir):
        return out
    for fn in sorted(os.listdir(cards_dir)):
        if not fn.endswith('.jsonl'):
            continue
        for line in open(os.path.join(cards_dir, fn), encoding='utf-8'):
            if not line.strip():
                continue
            try:
                c = json.loads(line)
            except json.JSONDecodeError:
                continue
            out.setdefault(c.get('org_id'), []).append({
                'researcher': (c.get('researcher') or {}).get('name') or '—',
                'date': c.get('date') or '',
                'confidence': c.get('confidence') or '',
                'completeness': c.get('completeness') or '',
                'summary': (c.get('summary') or '')[:400],
                'priority': (c.get('priority') or {}).get('category') or '',
                'priority_reason': (c.get('priority') or {}).get('reason') or '',
                'assessments': c.get('assessments') or {},
            })
    return out


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
            'acts_inferred': [a for a in SECTION_ACTS.get((rec.get('meta') or {}).get('list_section') or '', [])],
            'offers': [(o.get('format'), o.get('description')) for o in (rec.get('cooperation') or {}).get('offers') or []],
            'seeks': [(o.get('format'), o.get('description')) for o in (rec.get('cooperation') or {}).get('seeks') or []],
            'positions': [(p.get('topic'), p.get('status')) for p in rec.get('positions') or []],
        })
    conns = json.load(open(os.path.join(ROOT, 'data', 'connections.json'), encoding='utf-8'))
    links = [{'p': c.get('participants'), 't': c.get('type'),
              'coop': c.get('type') in COOPERATIVE_LINKS} for c in conns]
    return {'orgs': orgs, 'connections': links, 'tax': TAX, 'cards': load_cards(),
            'fmtMatrix': FMT_MATRIX,
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
.tabs{display:flex;gap:8px;margin:22px 0 0}
.tab{padding:10px 20px;border:1px solid var(--border);background:var(--card);border-radius:10px 10px 0 0;font-size:15px;font-weight:600;color:var(--muted);cursor:pointer}
.tab.active{color:#fff;background:var(--red);border-color:var(--red)}
.toolbar{display:flex;flex-wrap:wrap;gap:10px;margin:18px 0}
.toolbar input,.toolbar select{padding:9px 12px;border:1px solid var(--border);border-radius:8px;font-size:14px;background:var(--card)}
#q{flex:1;min-width:220px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:14px}
.card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:16px;display:flex;flex-direction:column}
.card h3{margin:0 0 4px;font-size:16px;color:var(--ink)}
.cat{display:inline-block;font-size:11px;font-weight:700;border-radius:999px;padding:2px 9px;margin-bottom:6px;color:#fff}
.meta{font-size:12px;color:var(--muted);margin-bottom:8px}
.stat{font-size:13px;margin:0 0 6px}
.draft{font-size:12px;color:#92400e;background:#fef3c7;border-radius:6px;padding:2px 8px;display:inline-block;margin-bottom:6px}
.ok{font-size:12px;color:#166534;background:#dcfce7;border-radius:6px;padding:2px 8px;display:inline-block;margin-bottom:6px}
.link{margin-top:auto;font-size:13px;font-weight:600}
section.match{background:#fff;border:1px solid var(--border);border-radius:14px;padding:20px;margin:26px 0}
section.match h2{margin:0 0 4px;font-size:20px;color:var(--ink)}
.matchrow{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-top:12px}
.matchrow select{flex:1;min-width:200px;padding:9px 12px;border:1px solid var(--border);border-radius:8px;font-size:14px}
#report{margin-top:14px;font-size:14px;white-space:pre-wrap;background:var(--bg);border-radius:10px;padding:14px;display:none}
.mapbox{background:#fff;border:1px solid var(--border);border-radius:14px;padding:20px;margin:20px 0}
.mapbox h2{margin:0 0 4px;font-size:20px;color:var(--ink)}
.catchk{display:inline-flex;align-items:center;gap:5px;font-size:13px;color:var(--text);cursor:pointer;background:#f3f4f6;border-radius:8px;padding:4px 10px}
.catchk input{accent-color:var(--red);margin:0}
.mapctl{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:12px 0}
.mapctl select{flex:1;min-width:240px;padding:9px 12px;border:1px solid var(--border);border-radius:8px;font-size:14px}
#layout{width:100%;height:auto;display:block;background:linear-gradient(#fff, #fbfbfd);border:1px solid var(--border);border-radius:10px}
.legend{display:flex;flex-wrap:wrap;gap:14px;font-size:13px;color:var(--muted);margin-top:10px}
.legend i{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:5px;vertical-align:-1px}
#panel{display:none;margin-top:14px;border-top:1px solid var(--border);padding-top:12px;font-size:14px}
#panel .brk{display:flex;justify-content:space-between;max-width:520px;padding:3px 0;color:var(--text)}
#panel .brk b{font-weight:600}
.mapnote{font-size:13px;color:var(--muted);margin-top:10px}
footer{margin:40px 0 30px;color:var(--muted);font-size:13px;border-top:1px solid var(--border);padding-top:16px}
.count{color:var(--muted);font-size:13px;margin:0 0 12px}
.node{cursor:pointer}
.node text{font-size:11px;fill:#374151;paint-order:stroke;stroke:#fff;stroke-width:3px;stroke-linejoin:round}
.ringlbl{font-size:11px;fill:#9ca3af}
@media (max-width:720px){#layout{min-height:520px}}
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
  <div class="tabs">
    <button class="tab active" id="tabList" onclick="showView('list')">Список организаций</button>
    <button class="tab" id="tabMap" onclick="showView('map')">Карта вокруг организации</button>
  </div>

  <section class="match">
    <h2>Матч-отчёт двух организаций</h2>
    <p style="margin:0;color:var(--muted);font-size:14px">Сопоставляет два паспорта: взаимодополняемость, общие темы, рекомендованные форматы, черновик первого письма.</p>
    <div class="matchrow">
      <select id="mA"></select>
      <span>↔</span>
      <select id="mB"></select>
      <button onclick="doMatch()" style="padding:9px 18px;background:var(--red);color:#fff;border:0;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer">Сопоставить</button>
    </div>
    <div id="report"></div>
  </section>

  <div id="viewList">
    <div class="toolbar">
      <input id="q" type="search" placeholder="Поиск по названию…">
      <select id="fCat"><option value="">Все категории</option></select>
      <select id="fSec"><option value="">Все разделы</option></select>
      <select id="fOnly"><option value="">Все паспорта</option><option value="asserted">Только утверждённые</option><option value="cards">Только с карточкой исследования</option></select>
    </div>
    <p class="count" id="count"></p>
    <div class="grid" id="grid"></div>
  </div>

  <div id="viewMap" style="display:none">
    <div class="mapbox">
      <h2>Карта вокруг организации</h2>
      <p style="margin:0;color:var(--muted);font-size:14px">Выберите организацию — она окажется в центре. Остальные расположены по радиусу: <b>ближе — выше гипотетический потенциал взаимодействия</b>, дальше — ниже. Клик по точке — из чего складывается потенциал; у организаций с красным пунктиром (есть карточка исследования) в панели появится блок «Что установили наши исследователи».</p>
      <div class="mapctl">
        <select id="centerSel"></select>
        <span style="font-size:13px;color:var(--muted)">в центре</span>
      </div>
      <div class="mapctl">
        <input id="limitN" type="range" min="10" max="__MAXN__" step="1" value="60" style="flex:1;min-width:240px;accent-color:var(--red)">
        <span style="font-size:13px;color:var(--muted);min-width:170px">показывать: <b id="limitVal">60</b> из <span id="limitMax"></span> ближайших</span>
      </div>
      <div class="mapctl">
        <select id="fSecMap" style="flex:1;min-width:240px"><option value="">Все разделы</option></select>
        <span style="font-size:13px;color:var(--muted)">раздел</span>
      </div>
      <div class="mapctl" id="catChks">
        <span style="font-size:13px;color:var(--muted)">категории:</span>
        <label class="catchk"><input type="checkbox" class="catChk" value="A" checked> <b style="color:#16a34a">А</b> первоочередной</label>
        <label class="catchk"><input type="checkbox" class="catChk" value="B" checked> <b style="color:#ca8a04">Б</b> перспективный</label>
        <label class="catchk"><input type="checkbox" class="catChk" value="C" checked> <b style="color:#f97316">В</b> точечные кампании</label>
        <label class="catchk"><input type="checkbox" class="catChk" value="D" checked> <b style="color:#3b82f6">Г</b> наблюдение</label>
        <label class="catchk"><input type="checkbox" class="catChk" value="E" checked> <b style="color:#dc2626">Д</b> не взаимодействуем</label>
        <label class="catchk"><input type="checkbox" class="catChk" value="?" checked> без категории</label>
        <button id="catAll" type="button" style="border:0;background:none;color:var(--red);font-size:13px;cursor:pointer;text-decoration:underline">выбрать все</button>
      </div>
      <svg id="layout" viewBox="0 0 1000 700" role="img" aria-label="Организациоцентричная карта взаимодействия"></svg>
      <div class="legend">
        <span><i style="background:#c8102e"></i>организация в центре</span>
        <span><i style="background:#16a34a"></i>паспорт утверждён</span>
        <span><i style="background:#9ca3af"></i>черновик (не утверждён)</span>
        <span><i style="background:#f59e0b"></i>есть подтверждённая связь</span>
        <span><i style="background:#dc2626"></i>публичный конфликт</span>
        <span><i style="background:none;border:1.6px dashed #c8102e;border-radius:50%"></i>есть карточка исследования</span>
      </div>
      <div id="panel"></div>
      <p class="mapnote">Карта строится по <b>гипотетическому потенциалу</b> — какие форматы взаимодействия возможны для пары, судя по их ролям (образование, медиа, профсоюзы, библиотека…; для черновиков сферы выведены из раздела списка), усиленному заявленным в паспортах: возможные форматы по ролям (+2 за формат, до 6), общие сферы (+1, до 4), заявленная взаимодополняемость «предлагаю × ищу» (+2, до 6), общие темы с утверждёнными обеими сторонами позициями (+1, до 3), подтверждённая связь (+2), оба паспорта утверждены (+1); нормировка к 10. Заявленные политические ограничения учитываются как потолок (статусы карты ThinkRed: «расхождения по методу» ограничивают потенциал точечными кампаниями, «не взаимодействуем» — почти обнуляют).
      Радиус нормируется к самой близкой организации текущего выбора — кольца подписаны фактическими значениями потенциала. Это гипотеза для первого разговора, а не факт сотрудничества и не оценка политической совместимости: реальную совместимость устанавливают только сами организации.</p>
    </div>
  </div>

  <footer>
    <p><b>Как участвовать:</b> проверьте карточку своей организации и утвердите паспорт — 30 минут по инструкции в репозитории.
    Формат данных и код — свободные (MIT): <a href="https://github.com/thethinkred-ai/interop-map" target="_blank" rel="noopener">github.com/thethinkred-ai/interop-map</a> · зеркало на <a href="https://thinkred.ru/interop/" target="_blank" rel="noopener">thinkred.ru/interop</a>.
    Методология: <a href="https://github.com/thethinkred-ai/interop-map/blob/main/handbook/METHODOLOGY.md" target="_blank" rel="noopener">как устроены карточки и оценки</a>.</p>
    <p>Данные-посев: публичная карта взаимодействия ThinkRed (снимок 17.10.2026, 209 организаций) + паспорт ThinkRed. Обновлено: <span id="upd"></span>. Удаление своей организации из реестра — по первому запросу.</p>
  </footer>
</main>
<script>
var DATA = __BUNDLE__;
var CATC = __CATC__, CATL = __CATL__, FMT = DATA.tax.interaction_format_labels, ACT = DATA.tax.activity_type_labels, TOPIC = DATA.tax.position_topic_labels;
var byId = {}; DATA.orgs.forEach(function(o){byId[o.id]=o;});
document.getElementById('upd').textContent = DATA.updated;

function fill(sel){ var s=document.getElementById(sel); DATA.orgs.forEach(function(o){ if(o.restricted) return; var op=document.createElement('option'); op.value=o.id; op.textContent=o.name+' ('+o.id+')'; s.appendChild(op); }); }
fill('mA'); fill('mB'); fill('centerSel');
document.getElementById('mA').value='ORG-000';
document.getElementById('mB').value='ORG-029';
document.getElementById('centerSel').value='ORG-000';

/* ---------- сфер деятельности: заявленные + выведенные из раздела списка ---------- */
function linkBetween(a, b){
  var r = null;
  DATA.connections.forEach(function(c){
    if(c.p && c.p.indexOf(a)!==-1 && c.p.indexOf(b)!==-1 && a!==b){ if(!r || c.coop) r = c; }
  });
  return r;
}
function actsOf(o){
  var s = {}; (o.acts||[]).forEach(function(x){s[x]=1;}); (o.acts_inferred||[]).forEach(function(x){s[x]=1;});
  return s;
}

/* ---------- матрица «роль × роль → возможный формат» (гипотетический слой) ---------- */
var FMT_MATRIX = DATA.fmtMatrix;

/* ---------- гипотетический потенциал пары (не вердикт, а оценка «что возможно») ---------- */
function scorePair(a, b){
  var brk = [];
  var A = actsOf(a), B = actsOf(b);
  // 1) гипотетические форматы по ролям
  var hypFormats = [];
  FMT_MATRIX.forEach(function(rule){
    var p = rule[0];
    if((A[p[0]] && B[p[1]]) || (B[p[0]] && A[p[1]])){
      if(hypFormats.indexOf(rule[1])<0) hypFormats.push(rule[1]);
    }
  });
  if(hypFormats.length) brk.push({label:'Возможные форматы по ролям (гипотеза): '+hypFormats.map(function(f){return FMT[f]||f;}).join(', '), pts:Math.min(6, 2*hypFormats.length)});
  // 2) общие сферы — потенциал «ровесного» сотрудничества
  var sharedActs = Object.keys(A).filter(function(x){return B[x];});
  if(sharedActs.length) brk.push({label:'Общие сферы деятельности: '+sharedActs.map(function(x){return ACT[x]||x;}).join(', '), pts:Math.min(4, sharedActs.length)});
  // 3) заявленная взаимодополняемость (факт, усиливает гипотезу)
  var nA={}, nB={};
  (a.offers||[]).forEach(function(x){nA[x[0]]=1;}); (b.seeks||[]).forEach(function(x){nB[x[0]]=1;});
  var comp = Object.keys(nA).filter(function(f){return nB[f];}).length;
  nA={}; nB={};
  (b.offers||[]).forEach(function(x){nA[x[0]]=1;}); (a.seeks||[]).forEach(function(x){nB[x[0]]=1;});
  comp += Object.keys(nA).filter(function(f){return nB[f];}).length;
  if(comp) brk.push({label:'Заявленная взаимодополняемость («предлагаю × ищу»): совпадений '+comp, pts:Math.min(6, 2*comp)});
  // 4) общие темы с утверждёнными позициями
  var pa={}, pb={};
  (a.positions||[]).forEach(function(p){if(p[1]==='asserted')pa[p[0]]=1;});
  (b.positions||[]).forEach(function(p){if(p[1]==='asserted')pb[p[0]]=1;});
  var shared = Object.keys(pa).filter(function(t){return pb[t];});
  if(shared.length) brk.push({label:'Общие темы с утверждёнными обеими сторонами позициями: '+shared.length, pts:Math.min(3, shared.length)});
  // 5) связь
  var link = linkBetween(a.id, b.id);
  if(link && link.coop) brk.push({label:'Подтверждённая кооперативная связь', pts:2});
  // 6) утверждённость паспортов
  if(a.asserted && b.asserted) brk.push({label:'Оба паспорта утверждены организациями', pts:1});
  var raw = brk.reduce(function(s,x){return s+x.pts;},0);
  // 7) заявленные политические ограничения (только политики ThinkRed, где применимы)
  var cap = 10, capNote = null;
  function other(o){return o.id==='ORG-000';}
  if(other(a)||other(b)){
    var x = other(a)? b : a;
    if(/Не взаимодействуем/i.test(x.page_status||'')){ cap=1.5; capNote='Политика ThinkRed: «не взаимодействуем» — потенциал ограничен'; }
    else if(/Расхождения по методу/i.test(x.page_status||'')){ cap=4; capNote='Политика ThinkRed: «расхождения по методу» — только точечные кампании'; }
  }
  var score = Math.round(Math.min(cap, raw/22*10)*10)/10;
  return {score:score, brk:brk, link:link, conflict:link&&!link.coop,
          hypFormats:hypFormats, capNote:capNote, capped:score>=cap&&raw/22*10>cap};
}

/* ---------- матч-отчёт ---------- */
function doMatch(){
  var a=byId[document.getElementById('mA').value], b=byId[document.getElementById('mB').value];
  var sc = scorePair(a,b);
  var pa={}, pb={}; (a.positions||[]).forEach(function(p){if(p[1]==='asserted')pa[p[0]]=1;}); (b.positions||[]).forEach(function(p){if(p[1]==='asserted')pb[p[0]]=1;});
  var both=Object.keys(pa).filter(function(t){return pb[t];});
  var A=actsOf(a), B=actsOf(b);
  var common=Object.keys(A).filter(function(x){return B[x];});
  var oA={}, oB={};
  (a.offers||[]).forEach(function(x){oA[x[0]]=1;}); (b.seeks||[]).forEach(function(x){oB[x[0]]=1;});
  var compFormats = Object.keys(oA).filter(function(f){return oB[f];});
  oA={};oB={};
  (b.offers||[]).forEach(function(x){oA[x[0]]=1;}); (a.seeks||[]).forEach(function(x){oB[x[0]]=1;});
  compFormats = compFormats.concat(Object.keys(oA).filter(function(f){return oB[f];}));
  var formats = compFormats.concat(sc.hypFormats.filter(function(f){return compFormats.indexOf(f)<0;}));
  if(!formats.length) formats=['open_discussion'];
  var L=[];
  L.push('МАТЧ-ОТЧЁТ: '+a.name+' ('+a.id+') ↔ '+b.name+' ('+b.id+')   ·   потенциал взаимодействия: '+sc.score+'/10');
  L.push('Статус паспортов: '+a.name+' — '+(a.asserted?'утверждён':'черновик')+'; '+b.name+' — '+(b.asserted?'утверждён':'черновик'));
  if(sc.brk.length){L.push('Из чего складывается потенциал:'); sc.brk.forEach(function(x){L.push('  +'+x.pts+' — '+x.label);});}
  else L.push('Потенциал 0: не находится ни одного возможного формата по ролям и заявленным данным.');
  if(sc.capNote) L.push('ОГРАНИЧЕНИЕ: '+sc.capNote+'.');
  if(sc.conflict) L.push('ВНИМАНИЕ: между организациями зафиксирован публичный конфликт — он показан, но потенциал не описывает.');
  L.push('');
  L.push('▌ Заявленная взаимодополняемость (предложения × запросы):');
  L.push('  '+(compFormats.length?compFormats.map(function(f){return FMT[f]||f;}).join(', '):'не заявлена'));
  L.push('');
  L.push('▌ Возможные форматы по ролям (гипотеза): '+(sc.hypFormats.length?sc.hypFormats.map(function(f){return FMT[f]||f;}).join(', '):'не найдено'));
  L.push('');
  L.push('▌ Общие темы с утверждёнными позициями обеих сторон: '+both.length);
  both.forEach(function(t){L.push('  • '+(TOPIC[t]||t)+' → сопоставьте формулировки в паспортах; расхождение — предмет разговора');});
  L.push('');
  L.push('▌ Общие сферы деятельности: '+(common.length?common.map(function(x){return ACT[x]||x;}).join(', '):'не найдено'));
  L.push('');
  L.push('▌ Рекомендованные форматы первого проекта (заявленное + возможное):');
  formats.forEach(function(f){L.push('  – '+(FMT[f]||f));});
  L.push('');
  L.push('▌ Черновик первого обращения:');
  L.push('«Здравствуйте, '+b.name+'! Мы — '+a.name+'. Судя по вашим открытым материалам, у нас общее поле: '+(common.length?common.map(function(x){return ACT[x]||x;}).slice(0,2).join(', '):'смежная деятельность')+'. Предлагаем начать с малого: '+((FMT[formats[0]]||formats[0]).toLowerCase())+'. Наш вклад — '+((a.offers||[])[0]?a.offers[0][1]:'материалы и площадка')+'. Что было бы полезно от вас?»');
  L.push('');
  L.push('Потенциал — гипотеза по ролям и заявленным данным, а не приговор о совместимости.');
  var r=document.getElementById('report'); r.textContent=L.join('\\n'); r.style.display='block';
}

/* ---------- организациоцентричная карта ---------- */
var GOLD = 2.399963;
function drawMap(){
  var svg = document.getElementById('layout');
  var cx=500, cy=390, Rmin=95, Rmax=345;
  var center = byId[document.getElementById('centerSel').value];
  var N = parseInt(document.getElementById('limitN').value, 10) || 60;
  var catOn = {};
  document.querySelectorAll('.catChk').forEach(function(c){ if(c.checked) catOn[c.value]=1; });
  var secFilter = document.getElementById('fSecMap').value;
  var others = DATA.orgs.filter(function(o){
    return o.id!==center.id && !o.restricted && catOn[o.category||'?']
      && (!secFilter || o.section===secFilter);
  });
  document.getElementById('limitVal').textContent = N;
  document.getElementById('limitMax').textContent = others.length;
  var scoredAll = others.map(function(o){return {o:o, sc:scorePair(center, o)};});
  scoredAll.sort(function(x,y){return y.sc.score-x.sc.score || (x.o.name<y.o.name?-1:1);});
  var scored = scoredAll.slice(0, N);
  // радиус нормируется к максимальному потенциалу текущего выбора — точки расходятся по всей площади
  var smax = 0;
  scored.forEach(function(it){ if(it.sc.score>smax) smax=it.sc.score; });
  smax = Math.max(smax, 2);
  var pos = function(s){ return Rmin + (1 - Math.min(1, s/smax))*(Rmax-Rmin); };
  var parts = [];
  // кольца с фактическими значениями (по нормированной шкале)
  [1, 0.75, 0.5, 0.25].forEach(function(fr, idx){
    var val = Math.round(smax*fr*10)/10;
    var r = pos(smax*fr);
    parts.push('<circle cx="'+cx+'" cy="'+cy+'" r="'+r.toFixed(1)+'" fill="none" stroke="#e5e7eb" stroke-dasharray="3 5"/>');
    var lx = cx + r*0.7071 + 6, ly = cy - r*0.7071 - 6;
    parts.push('<text class="ringlbl" x="'+lx.toFixed(1)+'" y="'+ly.toFixed(1)+'">'+val+'</text>');
  });
  parts.push('<line x1="'+(cx-Rmax-12)+'" y1="'+cy+'" x2="'+(cx+Rmax+12)+'" y2="'+cy+'" stroke="#eef0f3"/>');
  parts.push('<line x1="'+cx+'" y1="'+(cy-Rmax-12)+'" x2="'+cx+'" y2="'+(cy+Rmax+12)+'" stroke="#eef0f3"/>');
  var labeled = 0;
  scored.forEach(function(it, i){
    var s = it.sc.score;
    var r = pos(s);
    var jr = r + ((i%7)-3)*5;                       // разброс по радиусу против слипания
    var ang = i * GOLD;
    var x = cx + jr*Math.cos(ang), y = cy + jr*Math.sin(ang)*0.94;
    var fill = it.o.asserted ? '#16a34a' : '#9ca3af';
    if(it.sc.link) fill = it.sc.link.coop ? '#f59e0b' : '#dc2626';
    var rad = it.o.asserted ? 8 : 6;
    var hasCard = !!DATA.cards[it.o.id];
    var showLbl = (s>0 || hasCard) && labeled<22;
    if(showLbl) labeled++;
    var right = x >= cx;
    parts.push('<g class="node" data-id="'+it.o.id+'">'
      + '<circle cx="'+x.toFixed(1)+'" cy="'+y.toFixed(1)+'" r="'+rad+'" fill="'+fill+'" stroke="#fff" stroke-width="1.5" opacity="0.92"><title>'+it.o.name+' — потенциал '+s+'/10'+(hasCard?' · есть карточка исследования':'')+'</title></circle>'
      + (hasCard ? '<circle cx="'+x.toFixed(1)+'" cy="'+y.toFixed(1)+'" r="'+(rad+3.5)+'" fill="none" stroke="#c8102e" stroke-width="1.6" stroke-dasharray="2.5 2.5"/>' : '')
      + (showLbl ? '<text x="'+((right? x+11 : x-11)).toFixed(1)+'" y="'+(y+4).toFixed(1)+'" text-anchor="'+(right?'start':'end')+'" style="font-weight:'+(it.o.asserted?'700':'400')+'">'+it.o.name.slice(0,30)+'</text>' : '')
      + '</g>');
  });
  parts.push('<g><circle cx="'+cx+'" cy="'+cy+'" r="17" fill="#c8102e"/><circle cx="'+cx+'" cy="'+cy+'" r="17" fill="none" stroke="#fff" stroke-width="2.5"/><text x="'+cx+'" y="'+(cy+38)+'" text-anchor="middle" style="font-size:14px;font-weight:700;fill:#1a1a2e;paint-order:stroke;stroke:#fff;stroke-width:3px">'+center.name.slice(0,40)+'</text></g>');
  svg.setAttribute('viewBox', '0 0 1000 780');
  svg.innerHTML = parts.join('');
  Array.prototype.forEach.call(svg.querySelectorAll('.node'), function(g){
    g.addEventListener('click', function(){
      var o = byId[g.getAttribute('data-id')];
      var sc = scorePair(center, o);
      var p = document.getElementById('panel');
      var h = '<b>'+o.name+'</b> <span style="color:var(--muted)">('+o.id+')</span> — потенциал взаимодействия с <b>'+center.name+'</b>: <b style="color:var(--red)">'+sc.score+'/10</b>';
      if(sc.brk.length){ h += '<div style="margin-top:6px">'; sc.brk.forEach(function(x){h+='<div class="brk"><span>'+x.label+'</span><b>+'+x.pts+'</b></div>';}); h+='</div>'; }
      else h += '<div style="margin-top:6px;color:var(--muted)">Не находится возможных форматов — данных о ролях слишком мало.</div>';
      if(sc.capNote) h += '<div style="margin-top:6px;color:#b45309">'+sc.capNote+'.</div>';
      if(sc.conflict) h += '<div style="margin-top:6px;color:#b91c1c">Зафиксирован публичный конфликт (в потенциал не входит, показан для полноты).</div>';
      h += '<div style="margin-top:10px"><button onclick="toMatch(\\''+center.id+'\\', \\''+o.id+'\\')" style="padding:7px 14px;background:var(--red);color:#fff;border:0;border-radius:8px;font-size:13px;font-weight:600;cursor:pointer">Матч-отчёт '+center.name.slice(0,14)+' ↔ '+o.name.slice(0,14)+'</button></div>';
      h += cardsBlock(o.id);
      p.innerHTML = h; p.style.display='block';
    });
  });
}
function cardsBlock(orgId){
  var cards = DATA.cards[orgId] || [];
  if(!cards.length) return '';
  var h = '<div style="margin-top:14px;border-top:1px dashed var(--border);padding-top:10px"><b>Что установили наши исследователи</b> <span style="color:var(--muted);font-size:12px">('+cards.length+')</span></div>';
  cards.forEach(function(c){
    var AX=[['ideological_compatibility','Идейная'],['practical_compatibility','Практическая'],['mutual_benefit','Полезность'],['confirmed_activity','Активность'],['contact_accessibility','Доступность']];
    var ax = AX.map(function(x){var v=(c.assessments||{})[x[0]];return x[1]+': '+(v===null||v===undefined?'Н/Д':v+'/4');}).join(' · ');
    var cl={high:'высокая',medium:'средняя',low:'низкая'}[c.confidence]||c.confidence;
    var pl={high:'высокая',medium:'средняя',low:'низкая'}[c.completeness]||c.completeness;
    h += '<details style="margin-top:8px"><summary style="cursor:pointer;font-size:13px;color:var(--red)">Карточка · '+esc(c.researcher)+' · '+esc(c.date)+'</summary>'
      + '<div style="margin-top:6px;font-size:13px;line-height:1.55">'
      + '<div><b>Оценки исследователя:</b> '+ax+'</div>'
      + '<div><b>Приоритет:</b> '+(c.priority?('Кат. '+c.priority):'—')+(c.priority_reason?' — '+esc(c.priority_reason):'')+'</div>'
      + '<div><b>Достоверность:</b> '+cl+' · <b>полнота:</b> '+pl+'</div>'
      + '<div style="margin-top:4px">'+esc(c.summary)+'</div>'
      + '</div></details>';
  });
  return h;
}
function toMatch(aid, bid){
  document.getElementById('mA').value=aid;
  document.getElementById('mB').value=bid;
  doMatch();
  document.querySelector('.match').scrollIntoView({behavior:'smooth'});
}
document.getElementById('centerSel').addEventListener('change', drawMap);
document.getElementById('limitN').addEventListener('input', drawMap);
document.getElementById('fSecMap').addEventListener('change', drawMap);
(function(){
  var s = document.getElementById('fSecMap'), seen = {};
  DATA.orgs.forEach(function(o){ if(o.section && !seen[o.section]){ seen[o.section]=1; var op=document.createElement('option'); op.value=o.section; op.textContent=o.section; s.appendChild(op); } });
})();
document.querySelectorAll('.catChk').forEach(function(c){ c.addEventListener('change', drawMap); });
document.getElementById('catAll').addEventListener('click', function(){
  document.querySelectorAll('.catChk').forEach(function(c){ c.checked = true; });
  drawMap();
});
document.getElementById('limitMax').textContent = DATA.orgs.filter(function(o){return !o.restricted;}).length - 1;

/* ---------- виды и список ---------- */
function showView(v){
  document.getElementById('viewList').style.display = v==='list' ? '' : 'none';
  document.getElementById('viewMap').style.display = v==='map' ? '' : 'none';
  document.getElementById('tabList').classList.toggle('active', v==='list');
  document.getElementById('tabMap').classList.toggle('active', v==='map');
  if(v==='map') drawMap();
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
    if(only==='cards' && !DATA.cards[o.id]) return;
    n++;
    var d=document.createElement('div'); d.className='card';
    var badge=o.asserted?'<span class="ok">паспорт утверждён</span>':'<span class="draft">черновик — не утверждён организацией</span>';
    var c=o.category?'<span class="cat" style="background:'+(CATC[o.category]||'#9ca3af')+'">Кат. '+o.category+' · '+CATL[o.category]+'</span>':'';
    d.innerHTML=badge+c+'<h3>'+esc(o.name)+'</h3><div class="meta">'+esc(o.id)+' · '+esc(o.section||'—')+(o.form?' · '+esc(o.form):'')+'</div>'
      +(((o.acts||[]).concat(o.acts_inferred||[]).length)?'<p class="stat"><b>Сферы:</b> '+Object.keys((function(){var m={};(o.acts||[]).concat(o.acts_inferred||[]).forEach(function(x){m[x]=1;});return m;})()).map(function(x){return ACT[x]||x;}).join(', ')+((o.acts_inferred||[]).length && !(o.acts||[]).length?' <span style="color:var(--muted)">(по разделу списка)</span>':'')+'</p>':'')
      +(o.offers.length?'<p class="stat"><b>Предлагает:</b> '+o.offers.map(function(x){return FMT[x[0]]||x[0];}).join(', ')+'</p>':'')
      +(o.seeks.length?'<p class="stat"><b>Ищет:</b> '+o.seeks.map(function(x){return FMT[x[0]]||x[0];}).join(', ')+'</p>':'')
      + cardsBlock(o.id)
      +(o.site?'<a class="link" href="'+esc(o.site)+'" target="_blank" rel="noopener">Источник →</a>':'');
    g.appendChild(d);
  });
  var nCards = 0; DATA.orgs.forEach(function(o){ if(DATA.cards[o.id]) nCards += DATA.cards[o.id].length; });
  document.getElementById('count').textContent='Показано '+n+' из '+DATA.orgs.length+' · подтверждённых связей в базе: '+DATA.connections.length+' · карточек исследований: '+nCards;
}
render();
</script>
</body>
</html>
'''


def js_json(obj):
    """JSON для вставки внутрь <script>: экранирует всё, чем можно вырваться."""
    return (json.dumps(obj, ensure_ascii=False)
            .replace('<', '\\u003c')
            .replace('>', '\\u003e')
            .replace('&', '\\u0026')
            .replace('\u2028', '\\u2028')
            .replace('\u2029', '\\u2029'))


def main():
    b = bundle()
    html = (HTML
            .replace('__BUNDLE__', js_json(b))
            .replace('__CATC__', js_json(CAT_COLORS))
            .replace('__CATL__', js_json(CAT_LABELS))
            .replace('__MAXN__', str(sum(1 for o in b['orgs'] if not o.get('restricted')) - 1)))
    out = os.path.join(ROOT, 'docs', 'index.html')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'w', encoding='utf-8').write(html)
    print('site →', out, '(%.1f KB)' % (len(html.encode('utf-8')) / 1024))


if __name__ == '__main__':
    sys.exit(main())
