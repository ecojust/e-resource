"""Trace the photographed cloth and four stone mouldings with glTF face culling."""

import argparse
import itertools
import json
import os
from pathlib import Path
import runpy
import sys

import numpy as np
import zstandard


def checked_triangles(path, helpers):
    if path.suffix == '.zst':
        with path.open('rb') as src, os.fdopen(os.memfd_create('facade'), 'w+b') as dest:
            zstandard.ZstdDecompressor().copy_stream(src, dest)
            dest.flush()
            return checked_triangles(Path(f'/proc/self/fd/{dest.fileno()}'), helpers)
    triangles, material_ids, names, identity = helpers['load_triangles'](path)
    appearance = helpers['material_appearance'](path)['materials']
    two_sided = np.array([appearance[name]['doubleSided'] for name in names])[material_ids]
    normals = np.cross(triangles[:,1] - triangles[:,0], triangles[:,2] - triangles[:,0])
    return triangles, material_ids, names, identity['sha256'], two_sided, normals


def run(project, mesh):
    study = project / 'source/precise/huangpu-jiangxi-320-paired-pediment-windows'
    sys.path.insert(0, str(study / 'source'))
    from photo_plane import position
    from window_details import BAYS
    helpers = runpy.run_path(project / 'data/audit/postal-office-v1/independent-glb-review-helpers.py')
    triangles, ids, names, sha, two_sided, normals = checked_triangles(mesh, helpers)

    def cast(x, y):
        origin = position(x,y,-1.35)
        direction = position(x,y,.65) - origin
        direction /= np.linalg.norm(direction)
        face_visible = (normals @ direction < -1.e-12) | two_sided
        kept = np.flatnonzero(face_visible)
        hit, distance, point = helpers['first_hit'](triangles[kept], origin, direction)
        if not np.isfinite(distance):
            return None, None
        return names[ids[kept[hit]]], float(-point[1])

    profiles = json.loads((study / 'measurements/heldout-curtain-colours.json').read_bytes())
    cloth = []
    for p in profiles['profiles']:
        for sample in p['extrema']:
            mat, depth = cast(*sample['xy'])
            expected = dict(blue='Dusty blue awning stripe',ochre='Warm flax awning stripe')[sample['kind']]
            cloth.append(dict(name=p['curtain'],xy=sample['xy'],wanted=expected,observed=mat,passed=mat==expected))
    rakes = []
    for bay, side, along, across in itertools.product(BAYS,range(2),(.26,.51,.74),(.07,.44,.85)):
        outline = np.array(bay['hood'],dtype=float)
        opening = np.array(bay['hood_in'],dtype=float)
        line = outline * (1-across) + opening * across
        xy = (1-along)*line[side] + along*line[side+1]
        mat, depth = cast(*xy)
        passed = mat in {'Pale carved limestone','Cream arris','Weathered moulding return'} and depth is not None and depth > .14
        rakes.append(dict(bay=bay['name'],side=side,xy=xy.tolist(),observed=mat,projection_metres=depth,passed=passed))
    return dict(role=mesh.name,decoded_sha256=sha,curtain_matches=sum(r['passed'] for r in cloth),
                rake_matches=sum(r['passed'] for r in rakes),curtains=cloth,rakes=rakes)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('meshes',nargs='+',type=Path)
    args=parser.parse_args()
    results=[run(args.project,mesh) for mesh in args.meshes]
    args.output.write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    print([(r['role'],r['curtain_matches'],r['rake_matches']) for r in results])
