"""Measure both original-city LODs of the adjacent tile against the registered tower."""
from contextlib import ExitStack
from pathlib import Path
import argparse
import os
import subprocess
import sys

import numpy as np
import shapely as geo
from shapely.geometry import Point, shape

AUDIT = Path(__file__).resolve().parent
PROJECT = AUDIT.parents[2]
sys.path.insert(0, str(PROJECT / 'tools'))
from candidate_placement_meshes import PlacementMeshes, read, write, sha

MODEL = 'jingan-daxin-tobacco-northeast-tower'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', required=True, type=Path)
    parser.add_argument('--contract', type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    review_file = PROJECT / 'source/precise' / MODEL / 'footprint-review.json'
    review = read(review_file)
    site = PlacementMeshes(PROJECT, args.work, review)
    group, = review['preserved_near_tiles']
    owners = group['feature_local_ids']
    assert 1989 not in owners and set(group['closely_checked']) == {346, 353}
    site.link('baseline-far.glb', site.files['far.glb'])
    site.link('baseline-near.glb.gz', site.files[Path(group['file']).name])
    site.link('macro-READY.json', site.files['READY.json'])
    write(site.work / 'context-features.json', [{'localId': n} for n in owners])
    cut = None
    if args.contract:
        contract = read(args.contract)
        assert contract['id'] == MODEL and contract['owner']['feature_local_id'] == 1989
        cut = geo.transform(shape(contract['replacement_geometry']), site.to_xy)
    variants = {}
    with ExitStack() as temporary:
        for lod in ('near', 'far'):
            for type_name in ('owners.u32', 'triangles.f64'):
                link = site.work / f'baseline-{lod}-{type_name}'
                if link.exists() or link.is_symlink():
                    raise RuntimeError(f'Use a separate empty output directory for {link}')
                fd = os.memfd_create('daxin-neighbor-decode')
                temporary.callback(os.close, fd)
                link.symlink_to(f'/proc/{os.getpid()}/fd/{fd}')
                temporary.callback(link.unlink)
        subprocess.run(['node', site.decoders / 'map-decode-source.mjs'], env=site.env, check=True,
                       stdout=subprocess.DEVNULL)
        for lod in ('near', 'far'):
            triangles = np.fromfile(site.work / f'baseline-{lod}-triangles.f64', np.float64).reshape(-1, 3, 3)
            triangles[:, :, :2] = triangles[:, :, :2] @ site.axes.T
            if lod == 'far':
                membership = np.fromfile(site.work / 'baseline-far-owners.u32', np.uint32)
            else:
                centers = geo.points(triangles[:, :, :2].mean(1))
                distances = np.stack([geo.distance(centers, site.footprints[i]) for i in owners], axis=1)
                membership = np.asarray(owners)[distances.argmin(1)]
            assert set(membership) == set(owners)
            # Test the entire decoded group so the near assignment cannot hide an intersecting triangle.
            def measure(selection):
                projected = site.project_faces(triangles[selection])
                out = {'triangles': int(selection.sum()), 'axis_distance_m': projected.distance(Point(0, 0)),
                       'projected_area_m2': projected.area,
                       'roof_m': float(triangles[selection, :, 2].max())}
                if cut is not None:
                    out['mask_clearance_m'] = projected.distance(cut)
                    out['intersecting_triangles'] = int(np.count_nonzero(geo.intersects(cut, geo.polygons(triangles[selection, :, :2]))))
                    assert out['mask_clearance_m'] > 0 and out['intersecting_triangles'] == 0, (lod, out)
                return out
            variants[lod] = {'whole_tile': measure(np.ones(len(triangles), dtype=bool)),
                             'source_owners': {str(n): measure(membership == n) for n in group['closely_checked']}}
    write(args.out, {'id': MODEL, 'passed': True, 'source_review_sha256': sha(review_file),
                     'placement_sha256': sha(args.contract) if args.contract else None,
                     'source_tile': group, 'far_sha256': sha(site.files['far.glb']),
                     'near_assignment': 'Closest original polygon to each decoded triangle centroid',
                     'far_assignment': 'Original _FEATURE_ID_0 attribute', 'variants': variants})


if __name__ == '__main__':
    main()
