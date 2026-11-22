"""Compare reference colour peaks against the actual pixels of the Three.js viewer."""

import argparse
import hashlib
import itertools
import json
from pathlib import Path
import runpy
import sys

import numpy as np
from PIL import Image


def unit(vector):
    return vector / np.linalg.norm(vector)


def project(points, view, viewport, screenshot_size):
    width, height = viewport
    if width <= 650:
        top, right, bottom = 110, 0, height * .43 + 62
    else:
        top, right, bottom = 90, 350, 45
    canvas_width, canvas_height = width - right, height - top - bottom
    aspect = canvas_width / canvas_height
    tangent = np.tan(np.deg2rad(19))
    back = unit(np.array(view['direction']))
    side = unit(np.cross([0, 1, 0], back))
    up = np.cross(back, side)
    corners = np.array(list(itertools.product([-.5, .5], repeat=3))) * view['size']
    extent = np.maximum(abs(corners @ up), abs(corners @ side) / aspect)
    distance = np.max(corners @ back + 1.14 * extent / tangent)
    relative = points - (np.array(view['center']) + distance * back)
    depth = -(relative @ back)
    x = canvas_width * (.5 + relative @ side / (2 * depth * tangent * aspect))
    y = top + canvas_height * (.5 - relative @ up / (2 * depth * tangent))
    return np.column_stack([x, y]) * (np.array(screenshot_size) / viewport)


def shade(rgb):
    red, green, blue = [int(part) for part in rgb]
    if blue - red >= 14 and green > red + 8:
        return 'blue'
    if red - blue >= 20 and green - blue >= 12:
        return 'ochre'
    return 'other'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['project','mesh','screens','output']:
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--role', choices=['full', 'lod'], required=True)
    args = parser.parse_args()
    slug = 'jiangxi-320-paired-pediment-windows'
    study = args.project / 'source/precise' / ('huangpu-' + slug)
    sys.path.insert(0, str(study / 'source'))
    from photo_plane import position
    checks = runpy.run_path(args.project / 'data/audit/postal-office-v1/independent-glb-review-helpers.py')
    triangles, materials, names, model = checks['load_triangles'](args.mesh)
    profiles = json.loads((study / 'measurements/heldout-curtain-colours.json').read_bytes())
    reg = json.loads((study / 'measurements/viewer-camera-registration.json').read_bytes())['views']
    points, reference = [], []
    for profile in profiles['profiles']:
        for obs in profile['extrema']:
            x, y = obs['xy']
            origin = position(x, y, -1.35)
            ray = unit(position(x, y, .65) - origin)
            index, distance, point = checks['first_hit'](triangles, origin, ray)
            if not np.isfinite(distance):
                raise ValueError(f"No geometry at {x}, {y}")
            points.append([point[0], point[2], -point[1]])
            reference.append(dict(curtain=profile['curtain'], source_pixel=obs['xy'],
                                  expected=obs['kind'], material=names[materials[index]]))
    records = []
    for entry in json.loads((args.screens / 'viewer.json').read_bytes())['views']:
        if entry['mode'] not in ('front','oblique') or entry['role'] != args.role:
            continue
        path = args.screens / entry['filename']
        picture = Image.open(path).convert('RGB')
        width, height = entry['viewport']['width'], entry['viewport']['height']
        pixels = project(np.array(points), reg[entry['mode']]['web'], (width,height), picture.size)
        samples = []
        for ref, pixel in zip(reference, pixels):
            # Pillow samples pixel centres at (x + .5, y + .5).
            probe = tuple(int(np.floor(v)) for v in pixel)
            rgb = picture.getpixel(probe)
            seen = shade(rgb)
            samples.append(dict(**ref, at=probe,rgb=rgb,observed=seen,matched=seen==ref['expected']))
        score = sum(s['matched'] for s in samples)
        blues = [s for s in samples if s['expected'] == 'blue']
        print(entry['filename'], score, '/', len(samples), 'blue',sum(s['matched'] for s in blues),'/',len(blues))
        records.append(dict(frame=entry['filename'],frame_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),matched=score,samples=samples))
    args.output.write_text(json.dumps(dict(model=model['sha256'],role=args.role,frames=records),indent=2)+'\n')


if __name__ == '__main__':
    main()
