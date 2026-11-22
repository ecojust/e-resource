"""Intersect the actual accepted model rays with both original city groups after the local cut."""
from contextlib import ExitStack
from pathlib import Path
import argparse
import os
import subprocess
import sys

import numpy as np
import shapely as geo
from shapely.geometry import shape

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT / 'tools'))
from candidate_placement_meshes import PlacementMeshes, read, write, sha

MODEL = 'jingan-eye-hospital-building-three-front'


def crossings(eye, target, triangles):
    direction = target - eye
    length = np.linalg.norm(direction)
    direction /= length
    low = np.minimum(eye, target) - 1.e-5
    high = np.maximum(eye, target) + 1.e-5
    possible = np.all((triangles.max(1) >= low) & (triangles.min(1) <= high), axis=1)
    ids = np.flatnonzero(possible)
    triangles = triangles[ids]
    a, b, c = np.moveaxis(triangles, 1, 0)
    e1, e2 = b - a, c - a
    cross = np.cross(direction, e2)
    det = (e1 * cross).sum(1)
    ok = np.abs(det) > 1.e-9
    inv = np.divide(1., det, out=np.zeros_like(det), where=ok)
    delta = eye - a
    u = inv * (cross * delta).sum(1)
    q = np.cross(delta, e1)
    v = inv * (q @ direction)
    distance = inv * (e2 * q).sum(1)
    ok &= (u >= -1.e-8) & (v >= -1.e-8) & (u+v <= 1+1.e-8) & (distance > .005) & (distance < length-.015)
    return ids[ok], eye + distance[ok, None] * direction


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('contract', 'rays', 'work', 'out'):
        parser.add_argument('--' + key, required=True, type=Path)
    args = parser.parse_args()
    placement, rays = read(args.contract), read(args.rays)
    assert placement['id'] == MODEL and rays['contract_sha256'] == sha(args.contract)
    owner = placement['owner']['feature_local_id']
    review = read(PROJECT / 'source/precise' / MODEL / 'footprint-review.json')
    site = PlacementMeshes(PROJECT, args.work, review)
    cut = geo.transform(shape(placement['replacement_geometry']), site.to_xy)
    groups = review['near_tiles'] + review.get('preserved_near_tiles',[])
    results = []
    for group in groups:
        local_ids = group['feature_local_ids']
        site.link('baseline-near.glb.gz', site.files[Path(group['file']).name])
        site.link('baseline-far.glb', site.files['far.glb'])
        site.link('macro-READY.json', site.files['READY.json'])
        write(site.work/'context-features.json', [{'localId': n} for n in local_ids])
        with ExitStack() as release:
            for lod in ('near', 'far'):
                for suffix in ('owners.u32', 'triangles.f64'):
                    name = site.work/f'baseline-{lod}-{suffix}'
                    assert not name.exists() and not name.is_symlink()
                    fd = os.memfd_create('eye-court-physical-rays')
                    release.callback(os.close, fd)
                    name.symlink_to(f'/proc/{os.getpid()}/fd/{fd}')
                    release.callback(name.unlink)
            subprocess.run(['node', site.decoders/'map-decode-source.mjs'], env=site.env, check=True,
                           stdout=subprocess.DEVNULL)
            for lod in ('near', 'far'):
                triangles = np.fromfile(site.work/f'baseline-{lod}-triangles.f64', np.float64).reshape(-1, 3, 3)
                triangles[:, :, :2] = triangles[:, :, :2] @ site.axes.T
                owners = np.fromfile(site.work/'baseline-far-owners.u32', np.uint32) if lod == 'far' else None
                if lod == 'near' and owner in local_ids:
                    centers = geo.points(triangles[:, :, :2].mean(1))
                    distances = np.stack([geo.distance(centers, site.footprints[n]) for n in local_ids], axis=1)
                    owners = np.asarray(local_ids)[distances.argmin(1)]
                rows = []
                for model in rays['geometry']:
                    for view in model['views']:
                        eye = np.array(view['local_camera_eye'])
                        for mark in view['targets']:
                            assert mark['visible'], (view['view'], mark['feature'])
                            target = np.asarray(mark['hit']['physical_endpoint_m'])
                            ids, hits = crossings(eye, target, triangles)
                            removed = np.zeros(len(ids), bool)
                            if owner in local_ids:
                                removed = (owners[ids] == owner) & geo.covers(cut, geo.points(hits[:, :2]))
                            assert removed.all(), (lod, group['file'], view['view'], mark['feature'], hits[~removed])
                            rows.append(dict(model=model['role'], view=view['view'], feature=mark['feature'],
                                             original_crossings=len(ids), removed_owner_crossings=int(removed.sum()),
                                             retained_blockers=0))
                results.append(dict(group=group['file'], source_lod=lod, triangles=len(triangles), checks=rows))
    write(args.out, dict(id=MODEL, passed=True, contract_sha256=sha(args.contract), model_rays_sha256=sha(args.rays),
                         method='Intersect both sides of each original triangle before the accepted model hit. Discard only original owner 712 hits inside the signed replacement mask.',
                         original_groups=results))


if __name__ == '__main__':
    main()
