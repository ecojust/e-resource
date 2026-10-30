"""Synchronize delivered models into both README global-scene district tables.

City landmark rows retain their names/IDs and recorded version dates. Current
view links follow master; candidate commit times are separate, frozen evidence.
No network is required. New locally available published commits may populate the
cache on write; shallow-history gaps display 未记录 until evidence is supplied.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone, timedelta
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / 'projects/shanghai/data/model-todo'
TIME_FILE = DATA / 'candidate-publication-times.json'
HEADING = '## 按区查看主要建筑\n'
CURRENT = 'https://raw.githack.com/ecojust/e-resource/master/projects/shanghai/'
# This former snapshot was used by current-view buttons and early-model tables.
# Other pinned candidate versions and historical links must retain their hashes.
LEGACY_CURRENT = 'https://rawcdn.githack.com/ecojust/e-resource/b254063f3637ad18753ab129d15ac8adac55ccf3/projects/shanghai/'
PREFIX_DISTRICT = {'chongming':'崇明区', 'hongkou':'虹口区', 'xuhui':'徐汇区', 'huangpu':'黄浦区'}
INTEGRATIONS = ROOT / 'projects/shanghai/data/candidate-city-integrations.json'
MARKER = r'\n?<!-- district-candidates:[^>]+:start -->.*?<!-- district-candidates:[^>]+:end -->\n?'


def candidates():
    queue = json.loads((DATA / 'queue.json').read_text())
    viewers = {x['id']: x for x in json.loads((ROOT / 'projects/shanghai/data/model-viewers.json').read_text())}
    result = {}
    base_ids = {item['id'] for item in json.loads((ROOT / 'projects/shanghai/data/landmarks.json').read_text())}
    for job in queue['existing_models']:
        if job['id'] in base_ids:
            continue
        viewer = viewers.get(job['id'], {})
        result[job['id']] = {
            'id': job['id'], 'name': job['name'],
            'district': viewer.get('district') or PREFIX_DISTRICT[job['id'].split('-')[0]],
            'page': viewer.get('page') or job['url'].split('/')[-1],
        }
    for job in sorted(queue['production_queue'], key=lambda x: x['order']):
        if job['status'] not in ('candidate_delivered', 'accepted'):
            continue
        viewer = viewers.get(job['id'], {})
        result[job['id']] = {
            'id': job['id'], 'name': job['name'], 'district': job['district'],
            'page': (job.get('preview_source') or viewer.get('page') or job['preview']).split('/')[-1].split('#')[0],
            'published_commit': job.get('published_commit'),
        }
    return list(result.values())


def publication_times(items, check):
    cache = json.loads(TIME_FILE.read_text()) if TIME_FILE.exists() else {'schema': 'candidate-publication-times-v1', 'records': {}}
    changed = False
    for item in items:
        commit = item.get('published_commit')
        old = cache['records'].get(item['id'], {})
        if not commit or old.get('commit') == commit:
            continue
        # Never let Git lazily fetch old commits while rendering documentation.
        env = {**os.environ, 'GIT_NO_LAZY_FETCH': '1'}
        result = subprocess.run(['git', 'show', '-s', '--format=%H%n%cI', commit], cwd=ROOT, env=env, text=True, capture_output=True)
        if result.returncode:
            continue
        sha, date = result.stdout.strip().splitlines()
        record = {'commit': sha, 'committer_date_utc': datetime.fromisoformat(date).astimezone(timezone.utc).isoformat().replace('+00:00', 'Z'), 'source': 'local Git commit object', 'meaning': 'model version commit timestamp; not a measured hosting deployment time'}
        cache['records'][item['id']] = record
        changed = True
    if changed and not check:
        TIME_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + '\n')
    return cache['records']


def integrations():
    data = json.loads(INTEGRATIONS.read_text())
    assert data['schema'] == 'candidate-city-integrations-v1'
    items = data['models']
    assert len({item['id'] for item in items}) == len(items), 'Duplicate global model ID'
    return {item['id']: item for item in items}


def render(text, items, times, project=False):
    text = text.replace(LEGACY_CURRENT, CURRENT)
    text = text.replace('以下七个建筑模型均可独立预览', '下列早期模型均可独立预览')
    text = text.replace('七个模型均已接入', '下列早期模型均已接入')
    before, rest = text.split(HEADING, 1)
    section, after = rest.split('\n## ', 1)
    section = re.sub(MARKER, '\n', section, flags=re.S)
    section = re.sub(r'^\|[^\n]*#landmark=[^&]+&mode=overview[^\n]*\n?', '', section, flags=re.M)
    section = re.sub(r'https://rawcdn\.githack\.com/ecojust/e-resource/[0-9a-f]{40}/projects/shanghai/', CURRENT, section)
    section = section.replace('模型版本上线时间（UTC+8）', '模型版本提交（UTC+8）').replace('点击时间可核对对应提交。', '已链接的时间可核对对应提交。')
    old_city_ids = re.findall(r'#landmark=([^&]+)&mode=walk', section)
    base = json.loads((ROOT / 'projects/shanghai/data/landmarks.json').read_text())
    base_ids = {item['id'] for item in base}
    assert len(old_city_ids) == len(set(old_city_ids)) == len(base_ids) == 40, 'Expected 40 existing city destinations'
    assert set(old_city_ids) == base_ids
    city = integrations()
    assert set(city) == {item['id'] for item in items}, 'Every delivered candidate must be integrated'
    assert not base_ids.intersection(city), 'Global model duplicates an existing destination'
    district_names = {str(item['id']): item['name'] for item in json.loads((ROOT / 'projects/shanghai/data/districts.json').read_text())['districts']}
    counts = Counter(district_names[str(item['districtId'])] for item in [*base, *city.values()])
    assert len(counts) == 16 and sum(counts.values()) == 70
    parts = re.split(r'(?=^### )', section, flags=re.M)
    evidence = 'data/model-todo/candidate-publication-times.json' if project else 'projects/shanghai/data/model-todo/candidate-publication-times.json'
    placement = 'data/candidate-city-integrations.json' if project else 'projects/shanghai/data/candidate-city-integrations.json'
    intro = f'<!-- district-candidates:summary:start -->\n**汇总：16区，{len(base_ids) + len(city)}处建筑与构件模型入口（{len(base_ids)}处既有＋{len(city)}处新增接入）。** 各区数量见标题；每处均有地图精灵灯牌和全局直达链接。灯牌在视野内常显，密集时显示编号，点选查看名称。原{len(base_ids)}处保留室外漫游；新增{len(city)}处按资料近似定位并提供全局查看，尺寸与细节限制保留；“全局查看”直接打开城市场景，“单体”保留独立预览。入口随master更新。[定位依据]({placement}) · [候选版本时间]({evidence})。\n<!-- district-candidates:summary:end -->\n'
    parts[0] = parts[0].rstrip() + '\n\n' + intro + '\n'
    placed, counted_districts = set(), set()
    for i in range(1, len(parts)):
        heading, body = parts[i].split('\n', 1)
        district = re.sub(r'（\d+处）$', '', heading[4:].strip())
        if district not in counts:
            continue
        counted_districts.add(district)
        parts[i] = f'### {district}（{counts[district]}处）\n' + body
        group = [item for item in items if item['district'] == district]
        if not group:
            continue
        block = parts[i].rstrip()
        for obsolete in (
            '待补充逐栋精细建筑。该区已有全市底图，不表示已完成逐栋复原。',
            '本区已有独立候选，原址配准仍待完成。全市底图不表示已完成逐栋复原。',
        ):
            block = block.replace(obsolete, '').rstrip()
        if '| 主要建筑 |' not in block:
            block += '\n\n| 主要建筑 | 模型版本提交（UTC+8） | 直接查看 |\n|---|---|---|'
        rows = []
        for item in group:
            record = times.get(item['id'], {})
            if item.get('published_commit') and record.get('commit') != item['published_commit']:
                record = {}
            date = datetime.fromisoformat(record['committer_date_utc'].replace('Z', '+00:00')).astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S') if record else '未记录'
            name = item['name'].replace('|', '／')
            links = f"[全局查看]({CURRENT}index.html#landmark={item['id']}&mode=overview) · [单体]({CURRENT}{item['page']})"
            # A global view is available for every record. Walk links require the
            # separately verified navigation contract; inclusion is not precision acceptance.
            if city[item['id']].get('navigation', {}).get('listed'):
                links += f" · [漫游]({CURRENT}index.html#landmark={item['id']}&mode=walk)"
            rows.append(f"| {name} | {date} | {links} |")
            placed.add(item['id'])
        parts[i] = block + '\n' + '\n'.join(rows) + '\n\n'
    assert counted_districts == set(counts), 'A district count heading is missing'
    assert placed == set(city), 'Candidate without matching district section'
    updated_section = ''.join(parts).rstrip()
    assert set(re.findall(r'#landmark=([^&]+)&mode=overview', updated_section)) == set(city)
    result = before + HEADING + updated_section + '\n\n## ' + after
    return result


def sync(check=False):
    items = candidates()
    times = publication_times(items, check)
    for file, project in [(ROOT / 'README.md', False), (ROOT / 'projects/shanghai/README.md', True)]:
        before = file.read_text()
        after = render(before, items, times, project)
        if not project:
            assert len(after.encode()) <= 500_000, 'Root README risks GitHub truncation'
        if check:
            assert before == after, f'{file.relative_to(ROOT)} district directory is stale'
        elif before != after:
            file.write_text(after)
    print(f'README district candidates {"verified" if check else "synchronized"}: {len(items)}; global destinations: {40 + len(items)}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    sync(parser.parse_args().check)
