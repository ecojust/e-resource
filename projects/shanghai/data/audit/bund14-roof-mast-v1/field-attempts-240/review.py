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
for kind in ('roof', 'river'):
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
    red = lambda px: px[0] > 1.34 * px[1] + 7 and px[0] > 1.16 * px[2] + 8
    pairs = list(zip(before.getdata(), after.getdata()))
    changed = sum((max((abs(c - d) for c, d in zip(x, y))) >= 18 for x, y in pairs))
    added = sum((red(y) and (not red(x)) for x, y in pairs))
    dest = review_dir / (kind + '-aligned-crops.png')
    zoom = 3
    sheet = Image.new('RGB', (before.width * 3 * zoom, before.height * zoom + 28), 'white')
    draw = ImageDraw.Draw(sheet)
    for i, (v, t) in enumerate([(before, '239 prior'), (after, '240 revised'), (D, 'absolute pixel difference')]):
        sheet.paste(v.resize((before.width * zoom, before.height * zoom), Image.Resampling.NEAREST), (i * before.width * zoom, 28))
        draw.text((i * before.width * zoom + 2, 4), t, fill='black')
    sheet.save(dest)
    diffs[kind] = dict(rect=rect, changed_pixels=changed, newly_red_pixels=added, prior_red=sum((red(x) for x, y in pairs)), new_red=sum((red(y) for x, y in pairs)), crop_sha256=h(dest), same_camera=a['cameraUsed'], notes='These counts describe this crop, including any unrelated render variation. Review the pole, finial, gathered cloth and retained stone crest against the source photographs.')
for part in ('before', 'phone', 'desktop'):
    rr = r(e / part / 'browser.json')
    assert rr['ground'] == r(e / 'before/browser.json')['ground']
    assert rr['states'][0]['mode'] == 'walk'
for part in ('mouse', 'touch'):
    assert r(e / part / 'browser.json')['physical']['device'] == part
assert r(e / 'distant/browser.json')['states'][0]['asset']['variant'] == 'distant'
assert r(e / 'distant/browser.json')['states'][-1]['asset']['variant'] == 'full'
assert [s['id'] for s in r(e / 'neighbors/browser.json')['states']] == ['customs-house', 'bund15', 'bund14']
assert r(w / 'actual-saved-downloads.json')['passed'] and len(r(w / 'actual-saved-downloads.json')['items']) == 8
write(review_dir / 'paired-pixels.json', diffs)
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
    write(review_dir / 'notes-template.json', dict(order=240, images=images, roof_comparison='', river_comparison=''))
    print('Review originals and both aligned crops in', review_dir)
    sys.exit()
notes = r(args.notes)
assert notes['order'] == 240 and set(notes['images']) == set(images) and all((notes[k].strip() for k in ('roof_comparison', 'river_comparison')))
for name, rec in images.items():
    assert notes['images'][name]['sha256'] == rec['sha256'] and notes['images'][name]['observation'].strip(), name
assert diffs['roof']['changed_pixels'] > 0 and diffs['roof']['newly_red_pixels'] > 0, 'The matched roof crop supplies no pixel evidence for the red cloth. Inspect and retake if necessary.'
dst = Path('/workspace/e-resource/projects/shanghai/data/audit/bund14-roof-mast-v1/final-map-31240')
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
for name in ('bind.py', 'bound.json', 'map.cjs', 'sequence.py', 'review.py', 'downloads.py', 'actual-saved-downloads.json', 'verify-neighbors.py', 'neighbor-files.json', 'prior-release.json', '305-native-gate.json', '305-viewer-gate.json', 'all-sessions-closed.json'):
    keep(w / name, name)
for phase in phases:
    for name in ('browser.json', 'closed.json'):
        keep(e / phase / name, phase + '/' + name)
for name in images:
    keep(e / name, name)
for name in ('paired-pixels.json', 'roof-aligned-crops.png', 'river-aligned-crops.png'):
    keep(review_dir / name, name)
keep(args.notes, 'manual-review.json')
allhttp = Path('/tmp/shanghai-yongjia-porch/scenes/240-all-http.json')
assert r(allhttp)['passed'] and h(allhttp) == case['stages']['240']['all_http_sha256']
keep(allhttp, '240-all-http.json')
receipt = dict(order=240, passed=True, exit_code=0, remaining_chromium=[], all_captures_visually_reviewed=True, real_browser_process_exits=closings, reports=reports, finished=ready['closed_at'], manual_sha256=h(args.notes), ports=[31239, 31240], screenshots={name: v['sha256'] for name, v in images.items()}, saved_downloads=r(w / 'actual-saved-downloads.json')['items'], unchanged_city_count=276, roof_geometry_delta=[880, 308])
write(dst / 'slot-released.json', receipt)
write(w / '240-map-slot-released.json', receipt)
print(dst)
