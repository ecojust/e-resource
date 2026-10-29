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
    records = json.loads((root / 'data/landmarks.json').read_text())
    viewers = json.loads((root / 'data/model-viewers.json').read_text())
    assert len({p['id'] for p in viewers}) == len(viewers), 'Duplicate viewer IDs'
    assert all(p['page'].endswith('.html') and '/' not in p['page'] for p in viewers), 'Viewer must be a project page'
    for viewer in viewers:
        if viewer.get('walk_landmark_id'):
            assert any(r['id']==viewer['walk_landmark_id'] and r.get('accepted') and r.get('navigation',{}).get('listed') for r in records), 'Viewer walking link lacks accepted navigation'
    districts = {str(p['id']): p['name'] for p in json.loads((root / 'data/districts.json').read_text())['districts']}
    assert records, 'Navigation directory must not be empty'
    assert len({p['id'] for p in records}) == len(records), 'Duplicate navigation IDs'
    # Precise models are appended after acceptance; feature the latest published record.
    latest = next((p for p in reversed(records) if p.get('kind') == 'building'), records[-1])
    groups = [
        ('architecture', '逐栋建筑复原', '从屋顶与门窗，到扩建翼部与庭院。', list(reversed([p for p in records if p.get('kind') == 'building']))),
        ('bund', '外滩历史建筑群', '沿江展开的柱廊、钟塔、石砌立面与铜屋顶。', [p for p in records if p.get('bund_number')]),
        ('skyline', '陆家嘴天际线', '走到上海的高层地标脚下，仰望城市轮廓。', [p for p in records if p.get('kind') != 'building' and not p.get('bund_number')]),
    ]
    assert sum(len(group[3]) for group in groups) == len(records)
    sections = []
    for key, title, subtitle, items in groups:
        cards = []
        for item in items:
            name = html.escape(item['name'])
            district = html.escape(item.get('district', {}).get('name') or districts[str(item['districtId'])])
            ident = html.escape(item['id'], quote=True)
            href = html.escape('index.html#landmark=' + quote(item['id'], safe='') + '&mode=walk', quote=True)
            description = html.escape(item.get('architecture_style') or ('逐栋建筑复原' if item.get('kind') == 'building' else f"建筑高度 {item['height_m']:g} 米"))
            tag = '<span class="new-tag">本轮新增</span>' if item['id'] == latest['id'] else ''
            number = f"外滩 {item['bund_number']} 号" if item.get('bund_number') else district
            cards.append(f'''<a class="landmark-card{' featured' if tag else ''}" id="building-{ident}" data-landmark="{ident}" href="{href}" data-search="{html.escape(item['name'] + ' ' + district + ' ' + number, quote=True)}">
  <div class="card-meta"><span>{number}</span>{tag}</div><h3>{name}</h3><p>{description}</p>
  <div class="card-foot"><span>{district}</span><strong>进入漫游 <span aria-hidden="true">↗</span></strong></div>
</a>''')
        sections.append(f'''<section class="landmark-group" id="{key}" aria-labelledby="heading-{key}">
<div class="group-heading"><div><h2 id="heading-{key}">{title} <span>{len(items)}</span></h2><p>{subtitle}</p></div><a href="#top">回到顶部 ↑</a></div>
<div class="landmark-grid">{''.join(cards)}</div></section>''')
    viewer_sections = []
    for key, kind, title, note in [
        ('models', 'candidate', '独立建筑模型', '旋转、缩放并查看细节。标注已接入的模型也可从下方漫游列表进入；尺寸及隐蔽部分含估计。'),
        ('surfaces', 'surface', '地面与水系', '按行政区查看和下载；当前为地图平面，尚无实测地形与河床。'),
    ]:
        items = [p for p in viewers if p['kind'] == kind]
        cards = []
        for item in items:
            esc = html.escape
            cards.append(f'''<a class="landmark-card" id="viewer-{esc(item['id'], quote=True)}" data-viewer="{esc(item['id'], quote=True)}" href="{esc(item['page'], quote=True)}" data-search="{esc(item['name'] + ' ' + item['district'] + ' ' + item['description'], quote=True)}">
  <div class="card-meta"><span>{esc(item['district'])}</span><span>{'已接入漫游' if item.get('walk_landmark_id') else '独立候选' if kind == 'candidate' else '平面模型'}</span></div><h3>{esc(item['name'])}</h3><p>{esc(item['description'])}</p>
  <div class="card-foot"><span>{'室外地面漫游已开放' if item.get('walk_landmark_id') else '待城市定位与接入' if kind == 'candidate' else '16区分区查看'}</span><strong>打开模型 <span aria-hidden="true">↗</span></strong></div>
</a>''')
        viewer_sections.append(f'''<section class="landmark-group" id="{key}" aria-labelledby="heading-{key}">
<div class="group-heading"><div><h2 id="heading-{key}">{title} <span>{len(items)}</span></h2><p>{note}</p></div><a href="#top">回到顶部 ↑</a></div>
<div class="landmark-grid">{''.join(cards)}</div></section>''')
    return f'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="theme-color" content="#174e50">
  <meta name="description" content="上海模型统一入口：{len(records)}处地标漫游、独立建筑候选及16区地面水系模型。">
  <title>全部模型与地标 · 上海漫游</title>
  <link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="src/landmark-directory.css">
  <script src="src/landmark-directory.js" defer></script>
</head>
<body id="top">
  <a class="skip-link" href="#destinations">跳到地标目录</a>
  <header class="directory-header"><a class="wordmark" href="index.html#mode=overview">上海漫游 <small>SHANGHAI EXPLORER</small></a><a class="overview-link" href="index.html#mode=overview">打开全市地图 ↗</a></header>
  <main>
    <section class="hero"><div><span class="eyebrow">SHANGHAI MODEL COLLECTION</span><h1>看建筑，<br>也走进城市。</h1><p><strong>{len(records)} 处地标漫游 · {len(viewers)} 个独立模型入口。</strong>查看新交付的建筑候选与地面水系，或选择已接入的地标进入第三人称漫游。</p><a class="latest-link" href="#models">查看{html.escape(viewers[0]['name'])}等新模型 ↓</a><br><a class="latest-link" href="#building-{html.escape(latest['id'], quote=True)}">本轮新增：{html.escape(latest['name'])} ↓</a></div><div class="hero-count" aria-hidden="true">{len(records) + len(viewers)}<span>模型与漫游入口 · 上海</span></div></section>
    <nav class="group-nav" aria-label="模型分组"><a href="#models">独立建筑模型</a><a href="#surfaces">地面与水系</a><a href="#architecture">逐栋建筑漫游</a><a href="#bund">外滩历史建筑群</a><a href="#skyline">陆家嘴天际线</a></nav>
    <div class="directory-search" hidden><label for="landmark-search">寻找模型与目的地</label><input id="landmark-search" type="search" placeholder="输入建筑名称或行政区，如：宋庆龄、崇明" autocomplete="off"><span id="result-count" role="status" aria-live="polite">共 {len(records) + len(viewers)} 个入口</span></div>
    <div id="destinations">{''.join(viewer_sections)}{''.join(sections)}</div>
    <p class="no-results" hidden>没有找到匹配的建筑，试试其他名称或行政区。</p>
    <aside class="directory-note"><strong>查看模型，或从建筑旁开始探索</strong><p>“打开模型”进入可旋转、缩放的独立展示；“进入漫游”前往城市原址，WASD / 方向键行走，手机使用摇杆。模型和地图需要联网加载。</p><p>全市 16 区地图可探索，但并非每栋建筑都已完成精细复原；部分尺寸与背面细节仍含推估。独立候选尚未接入城市漫游。</p></aside>
  </main>
  <footer><span>上海漫游 · 地标直达</span><a href="https://github.com/ecojust/e-resource/tree/master/projects/shanghai">模型、来源与项目说明 ↗</a></footer>
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
