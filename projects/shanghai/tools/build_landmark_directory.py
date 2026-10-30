#!/usr/bin/env python3
"""Generate the no-WebGL landmark directory from the scene's navigation data."""
from __future__ import annotations
import argparse
import html
import json
import os
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]


def render(root: Path = ROOT) -> str:
    from sync_readme_districts import candidates

    base = json.loads((root / 'data/landmarks.json').read_text())
    integration = json.loads((root / 'data/candidate-city-integrations.json').read_text())
    assert integration['schema'] == 'candidate-city-integrations-v1'
    additions = integration['models']
    records = base + additions
    integrated_ids = {item['id'] for item in additions}
    assert len({p['id'] for p in records}) == len(records), 'Duplicate global destination IDs'
    assert len(base) == 40
    viewers = {p['id']: p for p in json.loads((root / 'data/model-viewers.json').read_text())}
    candidates_by_id = {p['id']: p for p in candidates()}
    assert integrated_ids == set(candidates_by_id), 'Every delivered candidate must appear in the global directory'
    districts = json.loads((root / 'data/districts.json').read_text())['districts']
    district_names = {str(p['id']): p['name'] for p in districts}
    latest = additions[-1] if additions else base[-1]
    esc = html.escape
    sections = []
    navigation = []
    for district in districts:
        district_id = str(district['id'])
        items = [p for p in records if str(p['districtId']) == district_id]
        if not items:
            continue
        key = 'district-' + district_id
        navigation.append(f'<a href="#{key}">{esc(district["name"])}</a>')
        cards = []
        for item in items:
            ident = item['id']
            integrated = ident in integrated_ids
            viewer = viewers.get(ident, candidates_by_id.get(ident, {}))
            href = 'index.html#landmark=' + quote(ident, safe='') + ('&mode=overview' if integrated else '&mode=walk')
            description = (viewer.get('description') or item.get('architecture_style') or ('近似定位的建筑外观模型；尺寸与未见细节含估计。' if integrated else '逐栋建筑外观模型。'))
            location_note = '近似定位' if integrated else '城市地标'
            actions = [f'<a href="{esc(href, quote=True)}">{"全局查看" if integrated else "进入漫游"} ↗</a>']
            if integrated and item.get('navigation', {}).get('listed'):
                walk = 'index.html#landmark=' + quote(ident, safe='') + '&mode=walk'
                actions.append(f'<a href="{esc(walk, quote=True)}">室外漫游 ↗</a>')
            if viewer.get('page'):
                assert viewer['page'].endswith('.html') and '/' not in viewer['page'], 'Viewer must be a project page'
                actions.append(f'<a href="{esc(viewer["page"], quote=True)}">单体预览 ↗</a>')
            tag = '<span class="new-tag">最近接入</span>' if ident == latest['id'] else ''
            cards.append(f'''<article class="landmark-card{' featured' if tag else ''}" id="building-{esc(ident, quote=True)}" data-landmark="{esc(ident, quote=True)}" data-search="{esc(item['name'] + ' ' + district['name'] + ' ' + description, quote=True)}">
  <div class="card-meta"><span>{esc(district['name'])} · {location_note}</span>{tag}</div><h3><a href="{esc(href, quote=True)}">{esc(item['name'])}</a></h3><p>{esc(description)}</p>
  <div class="card-foot">{' · '.join(actions)}</div>
</article>''')
        aliases = '<span id="bund"></span>' if district_id == '310101' else '<span id="skyline"></span>' if district_id == '310115' else ''
        sections.append(f'''{aliases}<section class="landmark-group" id="{key}" aria-labelledby="heading-{key}">
<div class="group-heading"><div><h2 id="heading-{key}">{esc(district['name'])} <span>{len(items)}</span></h2><p>按建筑名称选择，直接打开全局场景。</p></div><a href="#top">回到顶部 ↑</a></div>
<div class="landmark-grid">{''.join(cards)}</div></section>''')
    assert sum(1 for record in records if str(record['districtId']) in district_names) == len(records)
    surfaces = [viewer for viewer in viewers.values() if viewer['kind'] == 'surface']
    surface_cards = []
    for item in surfaces:
        surface_cards.append(f'''<a class="landmark-card" id="viewer-{esc(item['id'], quote=True)}" data-viewer="{esc(item['id'], quote=True)}" href="{esc(item['page'], quote=True)}" data-search="{esc(item['name'] + ' ' + item['district'], quote=True)}"><div class="card-meta">全市16区 · 平面模型</div><h3>{esc(item['name'])}</h3><p>{esc(item['description'])}</p><div class="card-foot"><strong>分区查看与下载 ↗</strong></div></a>''')
    surface_section = f'''<section class="landmark-group" id="surfaces" aria-labelledby="heading-surfaces"><div class="group-heading"><div><h2 id="heading-surfaces">地面与水系</h2><p>地图水面与非水域底面的零高程平面；尚无实测地形。</p></div><a href="#top">回到顶部 ↑</a></div><div class="landmark-grid">{''.join(surface_cards)}</div></section>'''
    count = len(records) + len(surfaces)
    return f'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="theme-color" content="#174e50">
  <meta name="description" content="按上海16区查看{len(records)}处建筑与构件模型，直接进入全局场景，并保留单体预览与下载。">
  <title>按区查看主要建筑 · 上海漫游</title>
  <link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="src/landmark-directory.css">
  <script src="src/landmark-directory.js" defer></script>
</head>
<body id="top">
  <a class="skip-link" href="#destinations">跳到建筑目录</a>
  <header class="directory-header"><a class="wordmark" href="index.html#mode=overview">上海漫游 <small>SHANGHAI EXPLORER</small></a><a class="overview-link" href="index.html#mode=overview">打开全市地图 ↗</a></header>
  <main>
    <section class="hero"><div><span class="eyebrow">SHANGHAI MODEL COLLECTION</span><h1>按区找建筑，<br>在城市中查看。</h1><p><strong>{len(records)} 处建筑与构件 · {len(sections)} 个行政区。</strong>已完成模型统一接入全局场景；选择建筑可直接定位，单体预览保留旋转查看和下载。</p><a class="latest-link" href="#building-{esc(latest['id'], quote=True)}">最近接入：{esc(latest['name'])} ↓</a></div><div class="hero-count" aria-hidden="true">{len(records)}<span>全局建筑入口 · 上海</span></div></section>
    <nav class="group-nav" aria-label="按行政区查看">{''.join(navigation)}<a href="#surfaces">地面与水系</a></nav>
    <div class="directory-search" hidden><label for="landmark-search">寻找建筑</label><input id="landmark-search" type="search" placeholder="输入建筑名称或行政区，如：永安、崇明" autocomplete="off"><span id="result-count" role="status" aria-live="polite">共 {count} 个入口</span></div>
    <div id="destinations"><span id="models"></span><span id="architecture"></span>{''.join(sections)}{surface_section}</div>
    <p class="no-results" hidden>没有找到匹配的建筑，试试其他名称或行政区。</p>
    <aside class="directory-note"><strong>全局查看与单体预览</strong><p>“全局查看”在城市地图中定位模型；“单体预览”提供独立旋转、缩放和下载。“进入漫游”从已有室外起点开始，WASD / 方向键行走，手机使用摇杆。模型和地图需要联网加载。</p><p>本次接入{len(additions)}件模型按资料近似定位；尺寸、未见细节和部分院落布局仍含估计。局部构件不代表整栋复原，地图接入也不表示测绘精度验收。<a href="data/candidate-city-integrations.json">查看定位记录</a>。</p></aside>
  </main>
  <footer><span>上海漫游 · 按区直达</span><a href="https://github.com/ecojust/e-resource/tree/master/projects/shanghai">模型、来源与项目说明 ↗</a></footer>
</body>
</html>
'''


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Fail if the published directory is stale')
    args = parser.parse_args()
    target = ROOT / 'landmarks.html'
    content = render()
    if args.check:
        assert target.read_text() == content, 'landmarks.html is stale; run tools/build_landmark_directory.py'
        print('Landmark directory matches navigation data')
    else:
        temporary = target.with_name(target.name + '.new')
        temporary.write_text(content)
        os.replace(temporary, target)
        print(f'Generated {target}')


if __name__ == '__main__':
    main()
