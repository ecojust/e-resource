"""Synchronize delivered independent candidates into both README district tables.

City landmark rows retain their names/IDs and recorded version dates. Current
view links follow master; candidate commit times are separate, frozen evidence.
No network is required. New locally available published commits may populate the
cache on write; shallow-history gaps display 未记录 until evidence is supplied.
"""
import argparse
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
PREFIX_DISTRICT = {'chongming':'崇明区', 'hongkou':'虹口区', 'xuhui':'徐汇区'}
MARKER = r'\n?<!-- district-candidates:[^>]+:start -->.*?<!-- district-candidates:[^>]+:end -->\n?'


def candidates():
    queue = json.loads((DATA / 'queue.json').read_text())
    viewers = {x['id']: x for x in json.loads((ROOT / 'projects/shanghai/data/model-viewers.json').read_text())}
    result = {}
    for job in queue['existing_models']:
        if '独立候选已交付' not in job['status']:
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
        if viewer.get('walk_landmark_id'):
            continue
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


def render(text, items, times, project=False):
    before, rest = text.split(HEADING, 1)
    section, after = rest.split('\n## ', 1)
    old_city_ids = re.findall(r'#landmark=([^&]+)&mode=walk', section)
    assert len(old_city_ids) == len(set(old_city_ids)) == 40, 'Expected 40 existing city destinations'
    section = re.sub(MARKER, '\n', section, flags=re.S)
    section = re.sub(r'https://rawcdn\.githack\.com/ecojust/e-resource/[0-9a-f]{40}/projects/shanghai/', CURRENT, section)
    section = section.replace('待补充逐栋精细建筑。该区已有全市底图，不表示已完成逐栋复原。', '本区已有独立候选，原址配准仍待完成。全市底图不表示已完成逐栋复原。')
    # Preserve city table version-date explanations and append explicit current/candidate scope.
    parts = re.split(r'(?=^### )', section, flags=re.M)
    evidence = 'data/model-todo/candidate-publication-times.json' if project else 'projects/shanghai/data/model-todo/candidate-publication-times.json'
    intro = f'<!-- district-candidates:summary:start -->\n当前入口随master更新。以下另收录{len(items)}件独立候选，均未原址配准，不计入40处城市入口；尺寸与未见细节含估计。候选日期为资产版本提交时间，逐件提交与来源见[时间依据]({evidence})，不是实际托管上线时间。\n<!-- district-candidates:summary:end -->\n'
    parts[0] = parts[0].rstrip() + '\n\n' + intro + '\n'
    placed = set()
    for i in range(1, len(parts)):
        district = parts[i].splitlines()[0][4:].strip()
        group = [x for x in items if x['district'] == district]
        if not group:
            continue
        rows = [f'<!-- district-candidates:{district}:start -->', '', '| 独立候选（未配准） | 版本提交（UTC+8） |', '|---|---|']
        for item in group:
            record = times.get(item['id'], {})
            if item.get('published_commit') and record.get('commit') != item['published_commit']:
                record = {}
            date = datetime.fromisoformat(record['committer_date_utc'].replace('Z', '+00:00')).astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S') if record else '未记录'
            name = item['name'].replace('|', '／')
            rows.append(f"| [{name}]({CURRENT}{item['page']}) | {date} |")
            placed.add(item['id'])
        rows += ['', f'<!-- district-candidates:{district}:end -->']
        parts[i] = parts[i].rstrip() + '\n\n' + '\n'.join(rows) + '\n\n'
    assert placed == {x['id'] for x in items}, 'Candidate without matching district section'
    updated_section = ''.join(parts).rstrip()
    assert re.findall(r'#landmark=([^&]+)&mode=walk', updated_section) == old_city_ids, 'City destinations changed'
    result = before + HEADING + updated_section + '\n\n## ' + after
    result = result.replace('崇明区的逐栋精模待补充。', '崇明区已有独立候选，原址精模接入仍待完成。')
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
    print(f'README district candidates {"verified" if check else "synchronized"}: {len(items)}; city destinations preserved: 40')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    sync(parser.parse_args().check)
