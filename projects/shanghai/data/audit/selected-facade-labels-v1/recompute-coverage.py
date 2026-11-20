"""Recompute real foreground/label coverage from the signed browser projections."""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

import numpy as np
from PIL import Image, ImageDraw

bundle = Path(__file__).resolve().parent
cli = argparse.ArgumentParser(description=__doc__)
cli.add_argument('--project', type=Path, default=bundle.parents[2],
                 help='Shanghai project containing the original Hamilton report and model')
cli.add_argument('--verify-mesh', action='store_true',
                 help='Also decode the published meshopt GLB with Node and verify every triangle index')
args = cli.parse_args()
project = args.project.resolve()
old = project / 'data/audit/hamilton-house-v1'
model = project / 'assets/models/candidates/huangpu-hamilton-house'
def sha(data):
    return hashlib.sha256(data).hexdigest()
def read(path):
    return json.loads(path.read_bytes())
def check(value, message):
    if not value:
        raise ValueError(message)

run = read(bundle / 'result.json')
binding = read(bundle / 'source-bindings.json')
reference = read(bundle / 'mesh-and-labels.json')
archive = read(bundle / 'evidence-manifest.json')
check(run['completed'] and run['closed'] and not run['errors'], 'Browser session incomplete')
for rel, digest in archive['sha256'].items():
    check(sha((bundle / rel).read_bytes()) == digest, 'Evidence signature mismatch: ' + rel)
model_info = read(model / 'manifest.json')['assets']['full']
check(sha((model / model_info['file']).read_bytes()) == binding['mesh']['input_sha256'] == reference['web_sha256'],
      'Displayed source mesh differs')
check(sha((bundle / 'original/check.cjs').read_bytes()) == run['script'], 'Browser checker differs')
def unpack(filename, digest):
    data = gzip.decompress((bundle / filename).read_bytes())
    check(sha(data) == digest, 'Uncompressed input differs: ' + filename)
    return data

indices = np.load(io.BytesIO(unpack('projection/indices.npy.gz', binding['mesh']['indices_sha256'])), allow_pickle=False)
check(indices.shape == (model_info['triangles'], 3) == (39472, 3), 'Unexpected face count')
check(indices.dtype == np.dtype('<i4') and indices.min() == 0 and indices.max() == 19983, 'Unexpected vertex indices')
if args.verify_mesh:
    with tempfile.TemporaryDirectory(prefix='verify-selected-facade-') as temp:
        decoded = Path(temp) / 'decoded.glb'
        subprocess.run(['node', project / 'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs',
                        model / model_info['file'], decoded, project / 'vendor/meshopt_decoder.module.js'], check=True, stdout=subprocess.PIPE)
        helpers = runpy.run_path(str(project / 'data/audit/postal-office-v1/independent-glb-review-helpers.py'))
        triangles, *_ = helpers['load_triangles'](decoded)
        vertices, order = np.unique(triangles.reshape(-1, 3), axis=0, return_inverse=True)
        check(np.array_equal(order.reshape(-1, 3), indices), 'Face index order differs from delivered GLB')
        authored = json.dumps(vertices.round(6).tolist(), separators=(',', ':')).encode()
        check(sha(authored) == binding['mesh']['points_sha256'], 'Mesh coordinate order differs')

previous_run = read(old / 'main-map-browser.json')
previous_labels = read(old / 'public-zoom-steps.json')['views'][0]['labels']
rows = {}
later = json.loads(gzip.decompress((bundle / 'projection/later-layouts.json.gz').read_bytes()))
later_expected = {s['stage']: s for s in read(bundle / 'catalog-density-replay.json')}
later_results = {}
for device, view in run['views'].items():
    width, height = view['viewport']
    screenshot = bundle / view['file']
    original = old / ('main-' + device + '.png')
    check(sha(screenshot.read_bytes()) == view['sha256'], device + ' screenshot differs')
    check(sha(original.read_bytes()) == reference['checks'][device]['old_file_sha256'], device + ' original differs')
    with Image.open(screenshot) as img:
        img.load()
        check(img.size == (width, height), device + ' viewport differs')
    before = next(v for v in previous_run['views'] if v['view'] == 'main-' + device)
    cam, prev = view['camera'], before['camera']
    for k in ['zoom', 'bearing', 'pitch']:
        check(abs(cam[k] - prev[k]) < .0001, device + ' camera differs: ' + k)
    for k in ['lng', 'lat']:
        check(abs(cam['center'][k] - prev['center'][k]) < 1e-7, device + ' center differs: ' + k)
    xy = json.loads(unpack('projection/' + device + '.json.gz', view['projectionSha256']))
    check(len(xy) == binding['mesh']['vertices'] == 19984, device + ' projected vertex count differs')
    image = Image.new('1', (width, height))
    draw = ImageDraw.Draw(image)
    for tri in indices:
        draw.polygon([tuple(xy[i]) for i in tri], fill=1)
    mask = np.asarray(image, dtype=bool)
    def cover(labels):
        rect = np.zeros((height, width), dtype=bool)
        for label in labels:
            x, y, w, h = (label[k] for k in ['x', 'y', 'width', 'height'])
            l, r = max(0, round(x-w/2)), min(width, round(x+w/2))
            t, b = max(0, round(y-h/2)), min(height, round(y+h/2))
            if l < r and t < b:
                rect[t:b, l:r] = True
        return int((mask & rect).sum())
    labels = view['labels']
    for point in labels:
        check(len(point['hits']) == 9 and all(h['picked'] == point['id'] for h in point['hits']),
              device + ' hit area differs: ' + point['id'])
    result = dict(total_mesh_pixels=int(mask.sum()), overlapping_pixels=cover(labels),
                  visible_labels=len(labels), hit_tests=sum(len(v['hits']) for v in labels))
    expected = reference['checks'][device]
    check(result['total_mesh_pixels'] == expected['projected_mesh_pixels'] and
          result['overlapping_pixels'] == expected['mesh_pixels_beneath_actual_label_rectangles'] and
          result['hit_tests'] == expected['nine_point_app_hits'], device + ' raster or hit result differs')
    if device == 'desktop':
        check({r['id'] for r in previous_labels} == {r['id'] for r in labels}, 'Desktop ID set differs')
        result['original_overlapping_pixels'] = cover(previous_labels)
        check(result['original_overlapping_pixels'] == expected['old_mesh_pixels_beneath_actual_label_rectangles'],
              'Desktop historical comparison differs')
    else:
        selected = next(r for r in labels if r['id'] == run['id'])
        prior = before['selected_label']
        check(all(abs(selected[k] - prior[k]) < .5 for k in ('x', 'y', 'width', 'height')), 'Mobile hit area moved')
    for stage in later['stages']:
        seq = stage['order']
        stage_result = later_results.setdefault(seq, {})
        expected_stage = later_expected[seq]
        check(stage['receipt'] == expected_stage['receipts'], 'Later catalog receipts differ')
        if device == 'desktop' and seq == 93:
            for old_label in previous_labels:
                reproduced = next(l for l in stage['views'][device]['before']['labels'] if l['id'] == old_label['id'])
                check(all(abs(reproduced[k] - old_label[k]) < .01 for k in ('x','y','width','height')), 'Baseline replay does not match original browser')
        if seq == 93:
            for new_label in labels:
                reproduced = next(l for l in stage['views'][device]['after']['labels'] if l['id'] == new_label['id'])
                check(all(abs(reproduced[k] - new_label[k]) < .01 for k in ('x','y','width','height')), 'Selection replay differs from measured browser')
        values = {k: cover(group['labels']) for k, group in stage['views'][device].items()}
        check(all(values[k] == expected_stage['views'][device][k]['covered_mesh_pixels'] for k in values), 'Later catalog mask differs')
        stage_result[device] = values
    rows[device] = result
check(set(rows) == {'desktop', 'mobile'}, 'Missing viewport')
print(json.dumps({'mesh_triangles':len(indices), 'mesh_vertices':binding['mesh']['vertices'],
                  'mesh_decode_repeated':args.verify_mesh, 'measurements':rows, 'later_catalog_replays':later_results}, indent=2))
