"""Prepare an image-by-image evidence sheet. Sign only the human observations supplied after the city sessions."""
from pathlib import Path
from hashlib import sha256
from PIL import Image, ImageDraw, ImageChops
from datetime import datetime, timezone
import argparse, shutil, json, os, sys, math
from sequence import w, e, phases, r, h, verify_closed, write
q = argparse.ArgumentParser(description=__doc__)
q.add_argument('--notes', type=Path)
args = q.parse_args()
case = r(w / 'bound.json')
ready = r(w / 'all-sessions-closed.json')
assert ready['phases'] == list(phases)
images = {}
reports = {}
closings = {}
diffs = {}
review_dir = w / 'review'
review_dir.mkdir(exist_ok=True)
for phase in phases:
    d = e / phase
    close = verify_closed(phase)
    rep = r(d / 'browser.json')
    closings[phase] = close
    reports[phase] = dict(report=str(d / 'browser.json'), report_sha256=h(d / 'browser.json'), exit=str(d / 'closed.json'), exit_sha256=h(d / 'closed.json'))
    for photo in rep['screenshots']:
        name = phase + '/' + photo['file']
        images[name] = dict(sha256=photo['sha256'], observation='')
for kind in ('west-stair','roof','main-door','corner'):
    old = e / ('old-' + kind)
    new = e / kind
    a = r(old / 'browser.json')
    b = r(new / 'browser.json')
    assert a['cameraUsed'] == b['cameraUsed']
    assert a['states'][0]['camera']['padding'] == b['states'][0]['camera']['padding']
    for x, y in zip(a['points'], b['points']):
        assert x['name'] == y['name'] and x['clear'] and y['clear'] and (abs(x['x'] - y['x']) < 0.3) and (abs(x['y'] - y['y']) < 0.3)
    xs = [p['x'] for p in b['points']]
    ys = [p['y'] for p in b['points']]
    width, height = Image.open(new / b['screenshots'][0]['file']).size
    rect = (max(0, int(min(xs)) - 9), max(0, int(min(ys)) - 10), min(width, math.ceil(max(xs)) + 12), min(height, math.ceil(max(ys)) + 16))
    assert rect[0] < rect[2] and rect[1] < rect[3]
    before = Image.open(old / a['screenshots'][0]['file']).convert('RGB').crop(rect)
    after = Image.open(new / b['screenshots'][0]['file']).convert('RGB').crop(rect)
    D = ImageChops.difference(before, after)
    pairs = list(zip(before.getdata(), after.getdata()))
    changed = sum((max((abs(c - d) for c, d in zip(x, y))) >= 18 for x, y in pairs))
    dest = review_dir / (kind + '-aligned-crops.png')
    zoom = 3
    sheet = Image.new('RGB', (before.width * 3 * zoom, before.height * zoom + 28), 'white')
    draw = ImageDraw.Draw(sheet)
    for i, (v, t) in enumerate([(before, '240 prior'), (after, '241 revised'), (D, 'absolute pixel difference')]):
        sheet.paste(v.resize((before.width * zoom, before.height * zoom), Image.Resampling.NEAREST), (i * before.width * zoom, 28))
        draw.text((i * before.width * zoom + 2, 4), t, fill='black')
    sheet.save(dest)
    diffs[kind] = dict(rect=rect, changed_pixels=changed, crop_sha256=h(dest), same_camera=a['cameraUsed'], notes='These counts describe this crop, including any unrelated render variation. Review the stair treads, handrail and high arched west windows in the west comparison. The main-door, street-corner and roof crops document the rest of the building.')
for part in ('before', 'phone', 'desktop'):
    rr = r(e / part / 'browser.json')
    assert rr['ground'] == r(e / 'before/browser.json')['ground']
    assert rr['states'][0]['mode'] == 'walk'
for part in ('mouse', 'touch'):
    assert r(e / part / 'browser.json')['physical']['device'] == part
assert r(e / 'distant/browser.json')['states'][0]['asset']['variant'] == 'distant'
assert r(e / 'distant/browser.json')['states'][-1]['asset']['variant'] == 'full'
assert [s['id'] for s in r(e/'neighbors/browser.json')['states']]==['bund03','bund06','bund05']
assert r(w / 'actual-saved-downloads.json')['passed'] and len(r(w / 'actual-saved-downloads.json')['items']) == 8
for phase in ('standalone-desktop','standalone-phone'):
    isolated=r(e/phase/'browser.json')['isolatedPage']
    assert isolated['public_route'] is False and isolated['source_site']==case['stages']['241']['origin']
    if phase=='standalone-desktop':
        assert set(isolated['downloads'])=={'raw','full','lod','native'}
        for role,entry in isolated['downloads'].items():
            assert entry['saved_and_reread'] and entry['sha256']==case['stages']['241']['assets'][role]['sha256']
write(review_dir/'paired-pixels.json', diffs)
for i in range(0, len(images), 6):
    chunk = list(images)[i:i + 6]
    sheet = Image.new('RGB', (960, math.ceil(len(chunk) / 3) * 282), 'white')
    draw = ImageDraw.Draw(sheet)
    for j, name in enumerate(chunk):
        image = Image.open(e / name).convert('RGB')
        image.thumbnail((312, 246))
        x = j % 3 * 320
        y = j // 3 * 282
        sheet.paste(image, (x + (320 - image.width) // 2, y))
        draw.text((x + 4, y + 247), name, fill='black')
    sheet.save(review_dir / f'contact-{i // 6 + 1}.jpg', quality=88)
if not args.notes:
    write(review_dir / 'notes-template.json', dict(order=241,images=images,west_stair_comparison='',roof_comparison='',main_door_comparison='',corner_comparison='',standalone_summary=''))
    print('Review originals and both aligned crops in', review_dir)
    sys.exit()
notes = r(args.notes)
assert notes['order']==241 and set(notes['images']) == set(images) and all((notes[k].strip() for k in ('west_stair_comparison','roof_comparison','main_door_comparison','corner_comparison','standalone_summary')))
for name, rec in images.items():
    assert notes['images'][name]['sha256'] == rec['sha256'] and notes['images'][name]['observation'].strip(), name
assert diffs['west-stair']['changed_pixels'] > 0, 'Inspect the revised west-wall stair directly in the aligned pair.'
dst = Path('/workspace/e-resource/projects/shanghai/data/audit/nissin-west-stair-v1/final-map-31241')
dst.mkdir(exist_ok=True)

def keep(p, name):
    end = dst / name
    end.parent.mkdir(parents=True, exist_ok=True)
    if not end.exists():
        try:
            os.link(p, end)
        except OSError:
            shutil.copy2(p, end)
    assert h(end) == h(p)
for name in ('bind.py', 'bound.json', 'map.cjs', 'sequence.py', 'review.py', 'downloads.py', 'actual-saved-downloads.json', 'verify-neighbors.py', 'neighbor-files.json', 'prior-release.json', '306-native-gate.json', '306-viewer-gate.json', 'single.cjs', 'complete-inputs.py', 'model-ranges.py', 'actual-glb-documents.json', 'official-inputs-verified.json', 'module-prewarm.json','guest-and-next.json', 'all-sessions-closed.json'):
    keep(w / name, name)
for action in ('native','viewer'):
    ticket=r(w/f'306-{action}-gate.json'); receipt=Path(ticket['guest_receipt']); assert h(receipt)==ticket['guest_sha256']; keep(receipt,'306-'+action+'-guest-receipt.json')
native530 = Path('/tmp/overseas-chinese530/241-native-returned.json')
native_gate = r(native530)
assert native_gate['all_children_exited'] and native_gate['remaining_children']==[] and native_gate['reverified_early']
assert native_gate['host_sha256'] == h(e/'mouse/closed.json') and native_gate['host_report_sha256'] == h(e/'mouse/browser.json')
assert native_gate['early_sha256'] == h(native530.parent/'early-236-native-returned.json') and len(native_gate['four_assets'])==4
keep(native530,'530-native-returned.json')
for phase in phases:
    for name in ('browser.json', 'closed.json'):
        keep(e / phase / name, phase + '/' + name)
for name in images:
    keep(e / name, name)
for name in ('paired-pixels.json', 'west-stair-aligned-crops.png','roof-aligned-crops.png','main-door-aligned-crops.png','corner-aligned-crops.png'):
    keep(review_dir / name, name)
keep(args.notes, 'manual-review.json')
allhttp = Path('/tmp/shanghai-yongjia-porch/scenes/241-all-http.json')
assert r(allhttp)['passed'] and h(allhttp) == case['stages']['241']['all_http_sha256']
keep(allhttp, '241-all-http.json')
development=Path('/tmp/hongkou-420-study/development-native/241-development-returned.json')
provided=r(development)
assert provided['host']==241 and provided['order']==420 and provided['all_children_exited'] and provided['remaining_children']==[]
assert provided['physical_sha256']==h(Path(provided['physical'])) and provided['host_sha256']==h(e/'standalone-phone/closed.json')
assert provided['previous_sha256']==h(w/'all-sessions-closed.json')
keep(development,'420-development-returned.json')
receipt = dict(development_420_return_sha256=h(development),order=241, passed=True, exit_code=0, remaining_chromium=[], all_captures_visually_reviewed=True, real_browser_process_exits=closings, reports=reports, finished=ready['closed_at'], manual_sha256=h(args.notes), ports=[31240,31241], screenshots={name: v['sha256'] for name, v in images.items()}, actual_saved_downloads=r(e/'standalone-desktop/browser.json')['isolatedPage']['downloads'],saved_downloads=r(w / 'actual-saved-downloads.json')['items'], unchanged_city_count=276, west_stair_triangle_delta=[8916,3054], review_sha256=h(args.notes))
write(dst / 'slot-released.json', receipt)
write(w / '241-map-slot-released.json', receipt)
print(dst)
