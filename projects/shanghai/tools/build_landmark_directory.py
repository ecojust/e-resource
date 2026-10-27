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
    return f'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="theme-color" content="#174e50">
  <meta name="description" content="上海漫游的全部 {len(records)} 处已建模地标，一键进入建筑旁的第三人称漫游。">
  <title>地标直达 · 上海漫游</title>
  <link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="src/landmark-directory.css">
  <script src="src/landmark-directory.js" defer></script>
</head>
<body id="top">
  <a class="skip-link" href="#destinations">跳到地标目录</a>
  <header class="directory-header"><a class="wordmark" href="index.html#mode=overview">上海漫游 <small>SHANGHAI EXPLORER</small></a><a class="overview-link" href="index.html#mode=overview">打开全市地图 ↗</a></header>
  <main>
    <section class="hero"><div><span class="eyebrow">CHOOSE YOUR NEXT STOP</span><h1>想去哪里，<br>就从那里出发。</h1><p><strong>{len(records)} 处已建模地标直达。</strong>选一栋建筑，直接进入它身旁的第三人称漫游。</p><a class="latest-link" href="#building-{html.escape(latest['id'], quote=True)}">本轮新增：{html.escape(latest['name'])} ↓</a></div><div class="hero-count" aria-hidden="true">{len(records)}<span>LANDMARKS · 上海</span></div></section>
    <nav class="group-nav" aria-label="地标分组"><a href="#architecture">逐栋建筑复原</a><a href="#bund">外滩历史建筑群</a><a href="#skyline">陆家嘴天际线</a></nav>
    <div class="directory-search" hidden><label for="landmark-search">寻找目的地</label><input id="landmark-search" type="search" placeholder="输入建筑名称或行政区，如：杨浦、龙华塔" autocomplete="off"><span id="result-count" role="status" aria-live="polite">共 {len(records)} 处</span></div>
    <div id="destinations">{''.join(sections)}</div>
    <p class="no-results" hidden>没有找到匹配的建筑，试试其他名称或行政区。</p>
    <aside class="directory-note"><strong>从建筑旁开始探索</strong><p>点击卡片进入漫游；WASD / 方向键行走，拖动转向，滚轮调整镜头。手机使用摇杆。模型和地图需要联网加载。</p><p>本页列出当前已提供独立模型与漫游入口的建筑。全市 16 区地图可探索，但并非每栋建筑都已完成精细复原；部分尺寸与背面细节仍含推估。</p></aside>
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
