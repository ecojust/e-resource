"""Record bounded model acceptance without rewriting the failed external-basemap report."""
from pathlib import Path
import datetime
import hashlib
import json
import shutil

W = Path('/workspace/shanghai-postal-qa')
S = W / 'candidate-stage'
P = Path('/workspace/e-resource/projects/shanghai')
A = P / 'data/audit/postal-office-v1'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text())
r, closure = read(S / 'candidate-stage.json'), read(S / 'candidate-process-closure.json')
assert len(r['captures']) == 5 and not r['completed'] and r['browserClosed']
assert closure['hostExitCode'] == 1 and closure['serverExited'] and closure['port8784Closed'] and closure['port9224Closed']
assert len(r['errors']) == 2
assert 'tiles.overturemaps.org/2026-10-21.0/buildings.pmtiles' in r['errors'][0] and 'CORS policy' in r['errors'][0]
assert r['errors'][1] == 'Failed to load resource: net::ERR_FAILED'
assert len(r['warnings']) == 2 and all(x.startswith('[Shanghai map] TypeError: Failed to fetch') and 'vendor/pmtiles.js' in x for x in r['warnings'])
assert not r['httpErrors'] and len(r['httpBindings']) == 5
assert r['scriptSha256'] == sha(W / 'qa-candidate-stage.cjs')
assert r['contractSha256'] == sha(W / 'candidate-stage-contract.json')
for item in r['frozen']:
    assert sha(P / item['file']) == item['sha256'], item['file']
notes = {
    'candidate-auxiliary-full.png': '实际查看完整辅助页：沿街巨柱、U形主楼、网格中庭罩、单面钟塔、绿冠、雕像与旗杆均在画布内；尺寸和隐面仍属估计。',
    'candidate-auxiliary-lod.png': '实际查看LOD，158452面与4.29MB显示正确；网格较疏，主要门窗、柱列、塔体和旗杆保留，未见明显缺面。',
    'candidate-main-default.png': '实际查看默认主图：模型位置及名称正确，西侧独立灰色建筑保留。选中灯牌遮挡部分塔体，远视角立面偏浅，不用此图单独证明完整塔或精细材质；此阶段有外部PMTiles CORS异常。',
    'candidate-main-tower-complete.png': '实际查看定向整塔：钟面、八柱上亭、两侧雕像、铜绿冠和旗杆完整，灯牌未挡塔顶；绿色窗间板、巨柱、题字和入口清楚，目标新立面实际显示。',
    'candidate-main-roof-complete.png': '实际查看宽屋顶：三翼、弧网罩和角塔整体入画，西侧独立建筑保留。位置卡遮住部分街景，不作完整街道证明；屋盖为明确年代参考的估计，不证明当前实况。',
}
visual = []
for capture in r['captures']:
    assert sha(S / capture['file']) == capture['sha256']
    visual.append({'file': capture['file'], 'sha256': capture['sha256'], 'actually_viewed': True,
                   'reviewer': 'postal_qa', 'accepted_within_recorded_scope': True,
                   'observation_zh': notes[capture['file']]})
(S / 'candidate-pixel-review.json').write_text(json.dumps(visual, ensure_ascii=False, indent=2) + '\n')
files = {name: S / name for name in ['candidate-stage.json', 'candidate-process-closure.json', 'candidate-pixel-review.json']}
files.update({name: W / name for name in ['qa-candidate-stage.cjs', 'candidate-stage-contract.json', 'qa-server.py',
    'run-browser-qa.py', 'prepare-contract.py', 'extract-geometry-highlights.py', 'geometry-highlights.json', 'visual-views.json', 'accept-candidate.py']})
files.update({capture['file']: S / capture['file'] for capture in r['captures']})
for name, source in files.items():
    shutil.copy2(source, A / name)
    assert sha(source) == sha(A / name)
old = W / 'attempt-01-wait-counter'
destination = A / 'run-history/attempt-01-wait-counter'
destination.mkdir(parents=True, exist_ok=True)
for source in old.iterdir():
    if source.is_file():
        shutil.copy2(source, destination / source.name)
evidence_names = ['candidate-stage.json', 'candidate-process-closure.json', 'candidate-pixel-review.json',
                  'qa-candidate-stage.cjs', 'candidate-stage-contract.json'] + [x['file'] for x in r['captures']]
result = {
    'schema': 'postal-candidate-acceptance-v1', 'model_id': 'hongkou-general-post-office',
    'accepted_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'passed': True, 'model_preflight_passed': True, 'final_suite_passed': False,
    'scope': 'Bounded preliminary model acceptance before queue candidate_delivered and final84-entry directory QA; not a zero-error or public-basemap acceptance.',
    'original_run_completed': r['completed'], 'original_host_exit_code': closure['hostExitCode'],
    'original_report_preserved_unchanged': True,
    'original_report': {'file': 'candidate-stage.json', 'sha256': sha(A / 'candidate-stage.json'), 'completed': False},
    'checks': {'auxiliary_full': True, 'auxiliary_lod': True, 'main_target_loaded': True,
               'main_target_clips_and_owner': True, 'actual_main_views': 3,
               'actual_images_viewed_by_postal_qa': 5, 'http_byte_bindings': 5,
               'frozen_inputs_unchanged': len(r['frozen']), 'browser_closed': True, 'server_closed': True},
    'frozen': r['frozen'], 'captures': r['captures'],
    'known_external_errors': r['errors'], 'known_external_warnings': r['warnings'],
    'external_error_scope': 'Overture remote PMTiles request failed CORS in this run. Local model/runtime requests and five explicit HTTP byte checks passed. Preserve this failure and assess final-stage external behavior separately; no empty tile or substituted input was used.',
    'qa_retry_history': {'directory': 'run-history/attempt-01-wait-counter',
        'reason': 'Original test reset stable-frame count on polls without a new frame. Preserved partial run and executed script, then corrected only the waiting counter to accumulate two stable actual new frames. Production inputs were unchanged.'},
    'evidence': [{'file': name, 'bytes': (A / name).stat().st_size, 'sha256': sha(A / name)} for name in evidence_names],
    'root_visual_review_claimed': False, 'public_http_verification_claimed': False,
}
(A / 'candidate-acceptance.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'model_preflight_passed': True, 'original_run_completed': False, 'external_errors': len(r['errors']),
                  'external_warnings': len(r['warnings']), 'captures': 5, 'frozen': len(r['frozen']),
                  'acceptance_sha256': sha(A / 'candidate-acceptance.json')}))
