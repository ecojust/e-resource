#!/usr/bin/env python3
"""One real load/screenshot of Longhua in a verified extracted launcher.

This is deliberately not the application's seven-view or catalog lifecycle QA.
The unchanged read-only probes and passive network observer are reused; the
production runtime, cache policy and asset timeout are not modified.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import time
from urllib.parse import urljoin, urlsplit
import zipfile

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('longhua_static_qa', HERE / 'browser-next-v3.py')
qa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qa)
from network_observer import (install_network_observer, is_expected_outage_console,
                              is_expected_outage_request, is_confirmed_cdp_outage)
from browser_expectations import expected_neighbors, validate_owner, projected_record

ID = 'xuhui-longhua-pagoda'
SCOPE = 'one-extracted-longhua-load'
META = {'launcher': 'LAUNCHER-MANIFEST.json', 'registry': 'data/precise-buildings-v6.json',
        'landmarks': 'data/landmarks.json', 'city': 'assets/city-detail/manifest.json',
        'catalog': 'data/precise-buildings/catalog.json'}
need = qa.require


def meta(path):
    p = Path(path)
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return {'bytes': p.stat().st_size, 'sha256': h.hexdigest()}


def preflight(args):
    need(re.fullmatch('[0-9a-f]{40}', args.commit), 'An immutable application commit is required')
    root = args.project.resolve()
    archive = json.loads(args.archive_proof.read_bytes())
    need(archive.get('passed') is True and archive.get('publishable') is True
         and archive.get('candidate_only') is False, 'Actual publishable archive proof required')
    need(archive.get('expected_commit') == archive.get('manifest_commit') == args.commit,
         'Archive belongs to another application commit')
    need((archive.get('landmarks'), archive.get('ordinary_static_count'),
          archive.get('ordinary_catalog', {}).get('macro_count')) == (25, 6, 4),
         'Archive must be the actual 25-navigation/6-building/4-macro release')
    need(root == Path(archive['extraction']['path']).resolve() / 'shanghai',
         'Project must be the archive validator actual extraction/shanghai')
    archive_meta = meta(args.archive)
    need(archive_meta == {'bytes': archive['archive_bytes'], 'sha256': archive['archive_sha256']}
         and 0 < archive_meta['bytes'] < 100_000_000, 'Archive bytes/SHA/size changed')
    local = {}
    with zipfile.ZipFile(args.archive) as z:
        for name in [*META.values(), 'index.html']:
            data = (root / name).read_bytes()
            need(data == z.read('shanghai/' + name), 'Extracted input differs from archive: ' + name)
            local[name] = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    data = {key: json.loads((root / name).read_bytes()) for key, name in META.items()}
    need(data['launcher']['commit'] == args.commit, 'Extracted manifest commit differs')
    nav = data['landmarks']
    need(len(nav) == len({r['id'] for r in nav}) == 25, 'Extracted navigation count differs')
    need(sum(r.get('kind') == 'building' for r in nav) == 6, 'Extracted ordinary count differs')
    need((data['catalog']['record_count'], data['catalog']['macro_count']) == (6, 4),
         'Extracted catalog count differs')
    record = next((r for r in nav if r['id'] == ID), None)
    need(record and record.get('accepted') is True and record.get('browser_passed') is True,
         'Target must already have actual application acceptance')
    projected_record(record)
    validate_owner(record, data['registry'])
    neighbors, detail = expected_neighbors(data['registry'], [ID])
    need(len(neighbors) == 13, 'Longhua must retain its actual 13 source neighbors')
    package = json.loads(args.package_record.read_bytes())
    need(package.get('packaging_passed') is True and package.get('building_id') == ID,
         'Actual final Longhua package required')
    base = f'https://rawcdn.githack.com/ecojust/e-resource/{args.commit}/projects/shanghai/'
    for role in ('web', 'lod', 'raw', 'native'):
        source, actual = package['assets'][role], record['assets'][role]
        need(actual['file'] == base + source['file'] and
             {k: actual[k] for k in ('bytes', 'sha256')} ==
             {k: source[k] for k in ('bytes', 'sha256')},
             'Extracted asset is not pinned to this app commit/final package: ' + role)
    need(record['model'] == record['assets']['web']['file'], 'Runtime model URL differs')
    evidence = qa.read_osm_fixture(args.osm_evidence, ID)
    return {'archive': archive_meta, 'local_metadata': local, 'data': data, 'record': record,
            'neighbors': neighbors, 'near_details': detail, 'evidence': evidence,
            'public_base': base}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project', type=Path, required=True, help='Actual extracted/shanghai directory')
    p.add_argument('--url', required=True, help='HTTP URL serving the exact extracted/shanghai directory')
    p.add_argument('--archive', type=Path, required=True)
    p.add_argument('--archive-proof', type=Path, required=True)
    p.add_argument('--package-record', type=Path, required=True)
    p.add_argument('--osm-evidence', type=Path, required=True)
    p.add_argument('--commit', required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--timeout-ms', type=int, default=360000)
    p.add_argument('--chromium', default='/usr/bin/chromium')
    p.add_argument('--width', type=int, default=1040)
    p.add_argument('--height', type=int, default=760)
    p.add_argument('--dpr', type=float, default=1)
    p.add_argument('--use-env-proxy', action='store_true')
    p.add_argument('--prepare-only', action='store_true')
    args = p.parse_args()
    inputs = preflight(args)
    need(urlsplit(args.url).scheme in ('http', 'https'), 'An HTTP(S) extracted project URL is required')
    need(args.timeout_ms > 0 and args.width > 0 and args.height > 0 and args.dpr > 0,
         'Invalid timeout or viewport')
    if args.prepare_only:
        print(json.dumps({'preparation_passed': True, 'browser_run': False, 'scope': SCOPE,
                          'target': ID, 'application_commit': args.commit}))
        return
    need(not args.output.exists(), 'Use a new output directory')
    args.output.mkdir(parents=True)
    report = {'schema': 'longhua-extracted-launcher-smoke-v1', 'scope': SCOPE,
              'started_utc': qa.utc(), 'passed': False, 'technical_passed': False,
              'target_ids': [ID], 'application_commit': args.commit,
              'archive_bytes': inputs['archive']['bytes'], 'archive_sha256': inputs['archive']['sha256'],
              'archive_proof': {'file': str(args.archive_proof.resolve()), **meta(args.archive_proof)},
              'package_record': {'file': str(args.package_record.resolve()), **meta(args.package_record)},
              'project': str(args.project.resolve()), 'url': args.url,
              'navigation_count': 25, 'ordinary_records': 6, 'catalog_macros': 4,
              'captures': [], 'progress': [], 'page_errors': [], 'shader_errors': [],
              'asset_errors': [], 'request_failures': [], 'expected_aborts': [],
              'console_errors': [], 'console_warnings': [], 'external_http_errors': [],
              'outage_request_candidates': [], 'expected_outage_console': [], 'forced_outage_requests': [],
              'catalog_lifecycle_tested': False, 'all_navigation_tested': False,
              'hardware_performance_test': False, 'visual_review': 'pending',
              'script_sha256': meta(__file__)['sha256'],
              'reused_tools': {name: meta(HERE / name) for name in (
                  'browser-next-v3.py', 'browser_expectations.py', 'network_observer.py', 'osm-readiness-probe.js')},
              'limitations': ['One extracted Longhua full-model load and one screenshot only.',
                             'No ZIP catalog lifecycle, LOD cycle, all-25 navigation, all-district or FPS test.',
                             'Known Overture hosts are blocked by CDP to observe the real OSM fallback.',
                             'Production asset timeout and browser cache policy are unchanged.']}
    write = lambda: qa.write_report(args.output / 'browser.json', report)
    started = time.monotonic()
    def progress(stage, **values):
        row = {'stage': stage, 'utc': qa.utc(), 'elapsed_seconds': round(time.monotonic()-started, 3), **values}
        report['progress'].append(row)
        print('PROGRESS ' + json.dumps(row, ensure_ascii=False), flush=True)
        write()
    qa._progress_callback = progress
    record = inputs['record']
    target_url = record['model']
    base = args.url.split('#', 1)[0].split('?', 1)[0]
    if not base.endswith('/'):
        base = base.rsplit('/', 1)[0] + '/' if base.endswith('.html') else base + '/'
    def critical(url):
        path = urlsplit(url).path.lower()
        return url == target_url or path.endswith(('.glb', '.glb.gz', '/ready.json')) or url.startswith(base)
    def response_seen(response):
        if response.status >= 400:
            report['asset_errors' if critical(response.url) else 'external_http_errors'].append(
                {'url': response.url, 'status': response.status})
            write()
    def request_failed(request):
        row = {'url': request.url, 'error': request.failure}
        if is_expected_outage_request(request.url, request.failure, True):
            report['outage_request_candidates'].append(row)
        elif 'ERR_ABORTED' in str(request.failure):
            report['expected_aborts'].append(row)
        else:
            report['request_failures'].append(row)
            if critical(request.url):
                report['asset_errors'].append(row)
        write()
    def console_seen(message):
        if message.type not in ('warning', 'error'):
            return
        row = {'type': message.type, 'text': message.text, 'location': message.location}
        shader_terms = ('webglprogram', 'validate_status', 'gl_invalid', 'context lost', 'linkprogram',
                        'invalid_operation', 'invalid_value', 'invalid_enum', 'shader error', 'shader failed')
        if is_expected_outage_console(message, True):
            key = 'expected_outage_console'
        elif any(x in message.text.lower() for x in shader_terms):
            key = 'shader_errors'
        else:
            key = 'console_errors' if message.type == 'error' else 'console_warnings'
        report[key].append(row)
        write()
    browser = page = None
    write()
    with qa.sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(executable_path=args.chromium, headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage', '--enable-unsafe-swiftshader'])
            options = {'viewport': {'width': args.width, 'height': args.height}, 'device_scale_factor': args.dpr}
            if args.use_env_proxy:
                proxy, safe = qa.environment_proxy()
                options['proxy'] = proxy
                report['proxy'] = safe
            context = browser.new_context(**options)
            page = context.new_page()
            page.set_default_timeout(args.timeout_ms)
            page.on('pageerror', lambda error: report['page_errors'].append(str(error)))
            page.on('response', response_seen)
            page.on('requestfailed', request_failed)
            page.on('console', console_seen)
            page.add_init_script("window.__V6_CONTEXT_LOSSES__=0;document.addEventListener('webglcontextlost',()=>window.__V6_CONTEXT_LOSSES__++,true)")
            install_network_observer(context, page, report, write, [target_url], True)
            progress('extracted-page-navigation BEGIN')
            page.goto(urljoin(base, 'index.html') + '#landmark=' + ID + '&mode=walk',
                      wait_until='domcontentloaded', timeout=args.timeout_ms)
            page.wait_for_function('()=>Boolean(window.__SHANGHAI_APP__?.controller)',
                                   timeout=args.timeout_ms, polling=250)
            fetched = page.evaluate(qa.FETCH_JSON, META)
            for key, value in fetched.items():
                need({k: value[k] for k in ('bytes', 'sha256')} == inputs['local_metadata'][META[key]],
                     'Served extracted metadata differs from verified archive: ' + key)
            report['metadata'] = {key: {k: value[k] for k in ('url', 'bytes', 'sha256')}
                                  for key, value in fetched.items()}
            index = page.evaluate("async()=>{const r=await fetch(new URL('index.html',document.baseURI));if(!r.ok)throw Error('index HTTP '+r.status);const b=await r.arrayBuffer();return {bytes:b.byteLength,sha256:Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',b))).map(x=>x.toString(16).padStart(2,'0')).join('')}}")
            need(index == inputs['local_metadata']['index.html'], 'Served entry page differs from extracted ZIP')
            report['entry_page'] = index
            report['probe'] = page.evaluate(qa.INSTALL_PROBE, fetched['registry']['data'])
            report['osm_probe'] = page.evaluate(qa.OSM_PROBE, inputs['evidence'])
            qa.near_view(page, ID)
            qa.wait_ready(page, ID, 'full', args.timeout_ms, True)
            qa.frame(page, args.timeout_ms)
            progress('actual-model-snapshot BEGIN')
            handle = page.wait_for_function("""id=>{
              if(!__OSM_CAPTURE__.readiness().ready)return false;
              const s=__V6_CAPTURE__.snapshot(),a=s.assets[id];
              return s.audit.passed&&!s.audit.onlinePending&&!s.streaming.pendingStates&&
                !s.streaming.detail.metadataMismatches&&a?.status==='loaded'&&a.visible&&a.variant==='full'&&
                s.audit.parents.some(p=>p.near.some(n=>n.visible&&n.groups.some(g=>g.landmark===id&&!g.visible)))?s:false;
            }""", arg=ID, timeout=args.timeout_ms, polling=250)
            try:
                state = handle.json_value()
            finally:
                handle.dispose()
            asset = state['assets'][ID]
            need(asset['triangles'] == record['triangles'] and asset.get('images') == [],
                 'Actual decoded full model triangles/images differ')
            need(state['districts'] == 16, 'District navigation count changed')
            observed = set(state['audit']['visibleNeighborIDs'])
            need(inputs['neighbors'].issubset(observed), 'Actual Longhua near model lost a neighbor')
            report['neighbors'] = {'expected': sorted(inputs['neighbors']), 'observed': sorted(observed), 'passed': True}
            before = page.evaluate('v=>__OSM_CAPTURE__.inspect(v)', {'target': ID})
            need(before['passed'] and before['osm']['active'] and before.get('component_check'),
                 'Actual settled OSM target component proof missing before capture')
            image = args.output / 'longhua-extracted-smoke.png'
            progress('single-screenshot BEGIN')
            page.screenshot(path=str(image), timeout=min(args.timeout_ms, 90000))
            after = page.evaluate('v=>__OSM_CAPTURE__.inspect(v)', {'target': ID})
            need(after['passed'] and after['osm']['active'] and after.get('component_check'),
                 'Actual settled OSM target component proof changed during capture')
            report['osm'] = {'evidence_sha256': meta(args.osm_evidence)['sha256'], 'before': before, 'after': after}
            report['captures'].append({'image': image.name, **meta(image), 'state': state})
            progress('actual-public-full-model-byte-audit BEGIN')
            actual = page.evaluate(qa.AUDIT_ASSET, {'record': record, 'variant': 'full'})
            need(actual['url'] == target_url and actual['bytes'] == record['web_bytes']
                 and actual['sha256'] == record['web_sha256'] and actual['triangles'] == record['triangles']
                 and actual['images'] == [] and actual['mappedPhotoMaterials'] == []
                 and not actual['externalResources'] and actual['bytes'] < 100_000_000,
                 'Actual pinned public full GLB differs from accepted model')
            report['asset_audit'] = {'passed': True, 'variant': 'full', **actual}
            losses = page.evaluate('window.__V6_CONTEXT_LOSSES__')
            report['webgl_context_losses'] = losses
            need(not losses and not report['page_errors'] and not report['shader_errors']
                 and not report['asset_errors'], 'Page, shader or required asset error during ZIP smoke')
            blocked, candidates = report['cdp_outage_failures'], report['outage_request_candidates']
            need(blocked and all(is_confirmed_cdp_outage(x) for x in blocked)
                 and Counter(x['url'] for x in blocked) == Counter(x['url'] for x in candidates),
                 'CDP/PW actual Overture outage evidence does not corroborate')
            network = report['target_network']
            need(network and {x['url'] for x in network} == {target_url}
                 and all(x.get('finished') is True and not x.get('error_text')
                         and 'failed_timestamp' not in x for x in network),
                 'A real target full-model request failed or did not finish')
            report['technical_passed'] = report['passed'] = True
            progress('single-load-smoke PASSED')
        except Exception as error:
            report['error'] = {'type': type(error).__name__, 'message': str(error)}
            write()
            raise
        finally:
            report['finished_utc'] = qa.utc()
            write()
            if browser:
                browser.close()
    print(json.dumps({'passed': report['passed'], 'scope': SCOPE, 'captures': len(report['captures']),
                      'report': str(args.output / 'browser.json'), 'visual_review': 'pending'}))


if __name__ == '__main__':
    main()
