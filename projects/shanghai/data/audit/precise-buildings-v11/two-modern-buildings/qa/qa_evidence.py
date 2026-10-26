"""Actual V10 multi-target evidence gates; preparation cannot manufacture PASS."""
from collections import Counter
from pathlib import Path
from urllib.parse import urljoin, urlsplit
import json
from osm_evidence_set import meta, need, read_fixture, read_fixture_set, capture_names, near_capture_names


def verify_descriptor(descriptor):
    need(isinstance(descriptor, dict) and descriptor.get('source'), 'Missing explicit evidence descriptor')
    source = Path(descriptor['source']).resolve()
    need(meta(source) == {key: descriptor[key] for key in ('bytes', 'sha256')}, 'Evidence descriptor byte/SHA mismatch')
    return source


def bound_set(lock):
    """App composition must bind the actual set descriptor, separately from tool lock."""
    path = verify_descriptor(lock.get('osm_evidence_set'))
    document = json.loads(path.read_bytes())
    targets = list(document.get('targets', {}))
    evidence, binding = read_fixture_set(path, targets)
    return evidence, binding


def fixture(path, ident):
    return read_fixture(path, ident) if path is not None else None


def selected_binding(lock, path, ident, *, catalog=False):
    evidence, binding = bound_set(lock)
    need(ident in evidence and path is not None, 'Selected building lacks bound actual source evidence')
    expected = binding['targets'][ident] if catalog else binding['set']
    need(meta(path) == {key: expected[key] for key in ('bytes', 'sha256')},
         'Actual used evidence differs from separately bound target fixture/set')
    if catalog:
        need(read_fixture(path, ident) == evidence[ident], 'Actual catalog fixture contents differ')
    return evidence, binding


def evidence_record(lock, path, ident, *, catalog=False):
    evidence, binding = selected_binding(lock, path, ident, catalog=catalog)
    return {'qa_tools_lock': lock['qa_tools_lock'], 'osm_evidence_set': binding['set'],
            'actual_osm_fixture': binding['targets'][ident], 'building_id': ident,
            'runtime_files_unchanged': True,
            'scope': 'Frozen target-parameterized QA with separately byte-bound actual OSM fixtures. Static global return/reset images concern only the last target. No production runtime delta.'}


def ring_key(ring):
    points = [tuple(point) for point in ring]
    if len(points) > 1 and points[0] == points[-1]:
        points.pop()
    need(len(points) >= 3, 'Degenerate actual source ring')
    return min(tuple(row[i:] + row[:i]) for row in (points, list(reversed(points))) for i in range(len(row)))


def polygon_key(geometry):
    need(geometry.get('type') == 'Polygon', 'Expected complete actual source Polygon')
    rings = geometry['coordinates']
    return ring_key(rings[0]), tuple(sorted(ring_key(ring) for ring in rings[1:]))


def check_capture_evidence(lock, browser, ident, path=None, *, catalog=False):
    evidence, binding = selected_binding(lock, path, ident, catalog=catalog)
    data, tools, qa = evidence[ident], lock['tools'], browser.get('osm_qa') or {}
    tool = 'catalog_osm_probe' if catalog else 'osm_probe'
    need(qa.get('probe_sha256') == tools[tool]['sha256'], 'Actual read-only OSM probe changed')
    if catalog:
        need(qa.get('evidence_sha256') == binding['targets'][ident]['sha256'], 'Actual catalog fixture binding differs')
        targets = browser.get('targets')
        need(targets == [ident], 'V10 catalog invocation must test one complete new macro/target')
        wanted = {capture['name'] for capture in browser['captures']
                  if capture.get('image') and capture['name'].endswith(('-loaded', '-returned'))}
        need(len(wanted) == 4, 'Actual catalog near/return capture set differs')
    else:
        targets = browser.get('targets')
        need(isinstance(targets, list) and len(targets) == len(set(targets))
             and set(targets) == set(evidence), 'Static targets differ from actual evidence set')
        need(browser.get('reset_only') is False, 'Partial reset-only run cannot pass full static acceptance')
        need([capture['name'] for capture in browser['captures']] == capture_names(targets),
             'Actual static 4-per-target plus 3-global capture sequence differs')
        need(qa.get('evidence_set') == binding['set'] and qa.get('evidence_by_target') == binding['targets'],
             'Actual static per-target fixture binding differs')
        expected_names = {target: sorted(near_capture_names(targets, target)) for target in targets}
        need(qa.get('near_capture_names_by_target') == expected_names, 'Static per-target near-image scope differs')
        wanted = near_capture_names(targets, ident)
    seen, active = set(), 0
    for capture in browser['captures']:
        for key in ('osm_capture_before', 'osm_capture_after'):
            observation = capture.get(key) or {}
            need(observation.get('ready') is True and observation.get('passed') is True,
                 'Actual OSM transaction/component observation failed: ' + capture['name'])
            if capture['name'] not in wanted:
                continue
            need(observation.get('target_requested') == ident, 'Near image observed another target fixture')
            if not (observation.get('osm') or {}).get('active'):
                continue
            proof = observation.get('component_check') or {}
            need(proof.get('expected_source_id') == data['source_id'] and proof.get('source_layer') == data['source_layer'],
                 'Actual target OSM source ID/layer differs')
            need(proof.get('actual_state', {}).get('localModel') is True
                 and proof.get('residual_source_is_current') is True
                 and proof.get('residual_data_available') is True
                 and proof.get('matching_residual_components') == 0,
                 'Actual target duplicate remains or residual transaction is stale')
            need(proof.get('expected_geometry') == data['geometry'], 'Expected complete source component changed')
            extracted = proof.get('extracted_components') or []
            need(extracted and all(str(item.get('fragment_id')) == str(data['source_id'])
                                   and polygon_key(item['geometry']) == polygon_key(data['geometry']) for item in extracted),
                 'Actual queried component differs from bound full source polygon')
            seen.add(capture['name'])
            active += 1
    if catalog:
        return
    need(browser.get('network_observer_sha256') == tools['network_observer']['sha256'], 'Actual passive network observer changed')
    base = browser['url'].split('#', 1)[0].split('?', 1)[0]
    if not base.endswith('/'):
        base = base.rsplit('/', 1)[0] + '/' if base.endswith('.html') else base + '/'
    urls = {urljoin(base, row['assets'][role]['file']) for row in browser['records'].values() for role in ('web', 'lod')}
    network = browser.get('target_network', [])
    need({row['url'] for row in network} == urls and all(row.get('finished') is True
         and not row.get('error_text') and 'failed_timestamp' not in row for row in network),
         'Actual selected web/LOD requests did not all finish')
    if browser.get('force_osm'):
        need(seen == wanted and active == 2 * len(wanted),
             'Forced OSM was not checked before/after this target actual near images')
        injection = browser.get('network_fault_injection') or {}
        hosts = {'tiles.overturemaps.org', 'stac.overturemaps.org'}
        valid = lambda url: urlsplit(url).scheme == 'https' and urlsplit(url).netloc in hosts
        need(injection.get('method') == 'Chromium Network.setBlockedURLs'
             and injection.get('patterns') == ['https://tiles.overturemaps.org/*', 'https://stac.overturemaps.org/*']
             and injection.get('playwright_routes_installed') is False
             and injection.get('cache_disabled_by_qa') is False and injection.get('fetch_replaced') is False
             and injection.get('runtime_deadline_changed') is False, 'Outage injection scope differs')
        blocked, requests = browser.get('cdp_outage_failures', []), browser.get('outage_request_candidates', [])
        need(blocked and all(valid(row['url']) and row.get('kind') == 'injected-outage'
             and row.get('error_text') in ('', 'net::ERR_BLOCKED_BY_CLIENT')
             and row.get('blocked_reason') == 'inspector' for row in blocked), 'Actual configured inspector tuple missing')
        need(all(valid(row['url']) and row.get('error') in ('inspector', 'net::ERR_BLOCKED_BY_CLIENT') for row in requests)
             and Counter(row['url'] for row in blocked) == Counter(row['url'] for row in requests),
             'Playwright/CDP outage observations do not corroborate each request')
        for error in browser.get('expected_outage_console', []):
            need(error.get('type') == 'error' and 'ERR_BLOCKED_BY_CLIENT' in error.get('text', '')
                 and error.get('location', {}).get('url') in {row['url'] for row in blocked},
                 'Unexpected console error cannot be classified as injected outage')


def add_qa_files(out, lock, path, ident, public, *, catalog=False):
    evidence, binding = selected_binding(lock, path, ident, catalog=catalog)
    for key, descriptor in lock['tools'].items():
        if key in ('registrar', 'ordinary_assets'):
            continue
        source = verify_descriptor(descriptor)
        out.add(public + '/qa/' + descriptor['public_relative'], source=source)
    out.add(public + '/qa/qa-tools.lock.json', source=verify_descriptor(lock['qa_tools_lock']))
    out.add(public + '/qa/actual-osm-evidence-set.json', source=binding['set']['source'])
    for target, descriptor in binding['targets'].items():
        out.add(public + '/qa/osm-targets/' + target + '.json', source=descriptor['source'])
    for descriptor in lock.get('qa_observation_files', []):
        out.add(public + '/qa/' + descriptor['public_relative'], source=verify_descriptor(descriptor))
