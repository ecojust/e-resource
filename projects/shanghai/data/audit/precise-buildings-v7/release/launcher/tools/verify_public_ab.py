#!/usr/bin/env python3
"""Bounded public byte verification for the two new precise buildings and app.

No model files are saved. --prepare-only reads local plan/main files only.
Network mode requires an explicit immutable40hex app commit and installed main
bytes equal to the supplied accepted-complete plan for every selected plan row.
This checks public accessibility/integrity, not browser or acceptance semantics.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import time
import urllib.error
import urllib.parse
import urllib.request

REPOSITORY = 'ecojust/e-resource'
REMOTE_PREFIX = 'projects/shanghai'
MAX_NETWORK_BYTES = 70_000_000
MAX_SINGLE_BYTES = 100_000_000
CHUNK_BYTES = 262_144
BUILDINGS = {'xuhui-wukang-210': '14-13718-6695',
             'qingpu-beidajie-208-212': '14-13701-6700'}
BASE_FILES = {
    'index.html', 'package.json',
    'data/landmarks.json', 'data/precise-buildings-v6.json',
    'data/precise-buildings/catalog.json',
    'assets/city/manifest.json', 'assets/city-detail/manifest.json',
    *('data/precise-candidates/'+ident+'.json' for ident in BUILDINGS),
}
CATALOG_PATH = re.compile(r'data/precise-buildings/(?:catalog\.json|by-id/[a-z0-9-]+\.json|macros/14-[0-9]+-[0-9]+/(?:index|replacement)\.json)\Z')


def fail(condition, message):
    if not condition:
        raise ValueError(message)


def safe_relative(value):
    fail(isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9_./-]+', value) is not None,
         'Unsafe project-relative path')
    p = PurePosixPath(value)
    fail(not p.is_absolute() and str(p) == value and not {'.', '..'}.intersection(p.parts),
         'Noncanonical project-relative path: '+value)
    return value


def file_digest(path):
    path = Path(path)
    with path.open('rb') as stream:
        before = os.fstat(stream.fileno())
        size = 0
        digest = hashlib.sha256()
        while block := stream.read(CHUNK_BYTES):
            size += len(block)
            digest.update(block)
        after = os.fstat(stream.fileno())
    fail((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
         (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns),
         'Local file changed while hashing: '+str(path))
    fail(size == before.st_size and 0 < size < MAX_SINGLE_BYTES,
         'Empty/oversize/changed local file: '+str(path))
    return size, digest.hexdigest()


def project_file(project, relative):
    p = project/safe_relative(relative)
    fail(p.is_file(), 'Missing installed main file: '+str(p))
    # Main legitimately exposes frozen city manifests through read-only links.
    # Hash the file behind that known main path; no writes use this function.
    return p


def read_plan(path):
    raw = path.read_bytes()
    fail(0 < len(raw) < 20_000_000, 'Unexpectedly large/empty plan')
    plan = json.loads(raw)
    fail(isinstance(plan.get('files'), list), 'Plan must contain files[]')
    rows = {}
    for row in plan['files']:
        rel = safe_relative(row['file'])
        fail(rel not in rows, 'Duplicate plan path: '+rel)
        fail(type(row['bytes']) is int and 0 < row['bytes'] < MAX_SINGLE_BYTES,
             'Invalid planned size: '+rel)
        fail(re.fullmatch('[0-9a-f]{64}', str(row['sha256'])) is not None,
             'Invalid planned SHA: '+rel)
        rows[rel] = row
    return plan, rows, hashlib.sha256(raw).hexdigest()


def selected_files(project, rows):
    selected = set(BASE_FILES)
    roles = {}
    for ident, macro in BUILDINGS.items():
        prefixes = (f'assets/models/precise/{macro}/{ident}/',
                    f'assets/native/precise/{macro}/{ident}/')
        found = {}
        for rel in rows:
            if not rel.startswith(prefixes):
                continue
            name = PurePosixPath(rel).name
            role = next((r for r in ['raw', 'web', 'lod']
                         if name in (r+'.glb', ident+'-'+r+'.glb')), None)
            if name in ('model.blend', ident+'.blend'):
                role = 'native'
            fail(role is not None, 'Unexpected asset inside selected model namespace: '+rel)
            fail(role not in found, 'Duplicate model role: '+ident+'/'+role)
            fail(rel.startswith(prefixes[1] if role == 'native' else prefixes[0]),
                 'Wrong role namespace: '+rel)
            found[role] = rel
        fail(set(found) == {'raw', 'web', 'lod', 'native'},
             'Plan must supply all four roles for '+ident)
        for role, rel in found.items():
            selected.add(rel)
            roles[rel] = {'building': ident, 'role': role}
    # All app-owned runtime JS/CSS, including unchanged files, without vendor or models.
    fail((project/'src').is_dir(), 'Missing main src directory')
    for p in (project/'src').rglob('*'):
        if p.is_file() and p.suffix in ('.js', '.css'):
            selected.add(safe_relative(p.relative_to(project).as_posix()))
    selected.update(rel for rel in rows if rel.startswith('src/') and Path(rel).suffix in ('.js', '.css'))
    selected.update(rel for rel in rows if CATALOG_PATH.fullmatch(rel))
    folder = project/'data/precise-buildings'
    if folder.exists():
        selected.update(p.relative_to(project).as_posix() for p in folder.rglob('*.json')
                        if p.is_file() and CATALOG_PATH.fullmatch(p.relative_to(project).as_posix()))
    for macro in BUILDINGS.values():
        fail(f'data/precise-buildings/macros/{macro}/index.json' in selected,
             'Missing selected macro index: '+macro)
        fail(f'data/precise-buildings/macros/{macro}/replacement.json' in selected,
             'Missing selected macro replacement manifest: '+macro)
    for ident in BUILDINGS:
        fail('data/precise-buildings/by-id/'+ident+'.json' in selected,
             'Missing by-id locator for '+ident)
    return sorted(selected), roles


def prepare_expected(project, plan_rows, paths, roles, prepare_only):
    entries = []
    for rel in paths:
        row = plan_rows.get(rel)
        if prepare_only and row is not None:
            local = Path(row['source'])
            fail(local.is_file(), 'Missing planned source: '+str(local))
            basis = 'accepted_plan_source_preview_only'
        else:
            local = project_file(project, rel)
            basis = 'installed_main'
        size, digest = file_digest(local)
        if row is not None:
            fail((size, digest) == (row['bytes'], row['sha256']),
                 'Selected installed/source bytes differ from accepted plan: '+rel)
        entry = {'path': rel, 'expected_bytes': size, 'expected_sha256': digest,
                 'expected_from': basis, 'matched_accepted_plan': row is not None,
                 'endpoint': 'raw_github'}
        entry.update(roles.get(rel, {'role': 'app_or_index'}))
        entries.append(entry)
    html = dict(next(r for r in entries if r['path'] == 'index.html'))
    html.update(endpoint='rawcdn_githack_html', role='public_app_html')
    entries.append(html)
    total = sum(r['expected_bytes'] for r in entries)
    # Reserve one extra byte/file to detect overlong unframed responses within cap.
    fail(total+len(entries) <= MAX_NETWORK_BYTES,
         f'Selection exceeds70MB network bound: {total} bytes/{len(entries)} files')
    return entries, total


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, target):
        raise urllib.error.HTTPError(request.full_url, code,
                                     'Redirect rejected for immutable public URL', headers, response)


def stream_one(opener, entry, commit, accounting):
    remote = REMOTE_PREFIX+'/'+entry['path']
    host = 'rawcdn.githack.com' if entry['endpoint'] == 'rawcdn_githack_html' else 'raw.githubusercontent.com'
    url = f'https://{host}/{REPOSITORY}/{commit}/'+urllib.parse.quote(remote, safe='/-._')
    result = dict(entry, url=url, passed=False, bytes=0)
    started = time.monotonic()
    digest = hashlib.sha256()
    try:
        request = urllib.request.Request(url, headers={
            'User-Agent': 'ShanghaiPublicByteVerification/1.0', 'Accept-Encoding': 'identity'})
        with opener.open(request, timeout=35) as response:
            result['http_status'] = response.status
            result['final_url'] = response.geturl()
            fail(response.status == 200 and response.geturl() == url, 'Non200 or changed URL')
            result['content_type'] = response.headers.get('Content-Type', '')
            if entry['endpoint'] == 'rawcdn_githack_html':
                fail(result['content_type'].split(';', 1)[0].strip().lower() == 'text/html',
                     'Fixed rawcdn app entry must return Content-Type text/html')
            encoding = response.headers.get('Content-Encoding', 'identity').lower()
            fail(encoding in ('', 'identity'), 'Unexpected content encoding: '+encoding)
            declared = response.headers.get('Content-Length')
            if declared is not None:
                fail(declared.isdecimal() and int(declared) == entry['expected_bytes'],
                     'Content-Length differs from expected bytes')
            while True:
                fail(time.monotonic()-started < 120, 'Per-file120s stream deadline exceeded')
                fail(time.monotonic()-accounting['start'] < 600, 'Whole-run600s deadline exceeded')
                remaining = MAX_NETWORK_BYTES-accounting['bytes']
                fail(remaining > 0, '70MB network read bound reached')
                take = min(CHUNK_BYTES, entry['expected_bytes']-result['bytes']+1, remaining)
                block = response.read(take)
                if not block:
                    break
                accounting['bytes'] += len(block)
                result['bytes'] += len(block)
                digest.update(block)
                fail(result['bytes'] <= entry['expected_bytes'], 'Remote body exceeds expected size')
        result['sha256'] = digest.hexdigest()
        fail(result['bytes'] == entry['expected_bytes'], 'Truncated public response')
        fail(result['sha256'] == entry['expected_sha256'], 'Public SHA mismatch')
        result['passed'] = True
    except Exception as error:
        result['sha256'] = digest.hexdigest()
        result['error'] = {'type': type(error).__name__, 'message': str(error)}
        if isinstance(error, urllib.error.HTTPError):
            result['http_status'] = error.code
            error.close()  # Do not fetch/save the error body.
    result['seconds'] = round(time.monotonic()-started, 3)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare-only', action='store_true', help='Offline selection; no network')
    mode.add_argument('--commit', help='Actual published app commit, full40lowercasehex')
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.commit and re.fullmatch('[0-9a-f]{40}', args.commit) is None:
        parser.error('--commit must be the actual immutable40hex app commit')
    project = args.project.absolute()
    fail(project.is_dir() and not any(q.is_symlink() for q in [project, *project.parents]),
         'Main root must be a real directory without symlink parents')
    report_path = args.report.absolute()
    fail(not report_path.exists() and not report_path.is_symlink(), 'Refuse to overwrite a report')
    fail(not report_path.is_relative_to(project), 'Report must remain outside main')
    fail(not any(q.is_symlink() for q in report_path.parents), 'Report parent symlink rejected')
    plan, rows, plan_sha = read_plan(args.plan)
    paths, roles = selected_files(project, rows)
    entries, total = prepare_expected(project, rows, paths, roles, args.prepare_only)
    report = {'schema': 'bounded-public-ab-byte-verification-v1', 'passed': False,
              'mode': 'offline_preparation' if args.prepare_only else 'public_commit_stream',
              'repository': REPOSITORY, 'commit': args.commit,
              'project': str(project), 'accepted_complete_plan': str(args.plan.absolute()),
              'plan_sha256': plan_sha, 'selected_file_count': len(paths),
              'request_count': len(entries), 'fixed_rawcdn_html_requests': 1,
              'selected_asset_count': len(roles), 'expected_response_bytes': total,
              'network_byte_limit': MAX_NETWORK_BYTES, 'network_bytes_read': 0,
              'network_not_run': args.prepare_only, 'replica_files_written': False,
              'allcity_model_downloaded': False, 'retry_count': 0,
              'scope': 'Both new raw/web/LOD/native assets; app src JS/CSS and entry; navigation, precise registry, ordinary catalog/macro indexes/locators, two existing city manifest JSONs. Also exact fixed-commit rawcdn.githack.com index HTML with required text/html. No city tile/model traversal, browser or new geometry review.',
              'plan_status_as_supplied': {k: plan.get(k) for k in
                 ['status','static_browser_passed','catalog_lifecycle_browser_passed','production_install_supported']},
              'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'files': []}
    report_path.parent.mkdir(parents=True, exist_ok=True)
    # Reserve just a report, never asset data. Exclusive creation prevents clobber.
    with report_path.open('x', encoding='utf-8') as output:
        try:
            if args.prepare_only:
                report['files'] = entries
                report['passed'] = True
                report['public_accessibility_verified'] = False
            else:
                opener = urllib.request.build_opener(NoRedirect())
                accounting = {'bytes': 0, 'start': time.monotonic()}
                for entry in entries:
                    result = stream_one(opener, entry, args.commit, accounting)
                    report['files'].append(result)
                    report['network_bytes_read'] = accounting['bytes']
                    print(json.dumps({k: result.get(k) for k in
                          ['path','endpoint','passed','http_status','content_type','bytes','sha256','error']}), flush=True)
                    fail(result['passed'], 'Public verification failed: '+entry['path'])
                # Bind the result to the same known main and plan at completion.
                fail(hashlib.sha256(args.plan.read_bytes()).hexdigest() == plan_sha,
                     'Accepted plan changed during public verification')
                for entry in entries:
                    fail(file_digest(project_file(project, entry['path'])) ==
                         (entry['expected_bytes'], entry['expected_sha256']),
                         'Main changed during verification: '+entry['path'])
                report['passed'] = True
                report['public_accessibility_verified'] = True
                report['main_and_plan_stable_after_stream'] = True
        except Exception as error:
            report['error'] = {'type': type(error).__name__, 'message': str(error)}
        finally:
            report['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            json.dump(report, output, ensure_ascii=False, indent=2)
            output.write('\n')
    print(json.dumps({k: report.get(k) for k in ['passed','mode','selected_file_count','request_count',
          'expected_response_bytes','network_bytes_read','public_accessibility_verified']}), flush=True)
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
