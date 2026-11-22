"""Determine ownership where the garden facade meets the actual near and far meshes."""
from pathlib import Path
import sys
import subprocess
import json

import numpy as np
import shapely as geo
from shapely.geometry import Polygon

PROJECT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT / 'tools'))
from candidate_placement_meshes import PlacementMeshes, read, sha, write

ID = 'jingan-pan-garden-south-portico'
OWNER = 2572


def load_values(file, dtype):
    if file.is_file():
        return np.fromfile(file, dtype)
    import gzip, hashlib
    values = gzip.decompress(file.with_name(file.name + '.gz').read_bytes())
    expected = file.with_name(file.name + '.sha256').read_text().strip()
    assert hashlib.sha256(values).hexdigest() == expected
    return np.frombuffer(values, dtype).copy()


def local_mask(registration):
    return Polygon(registration['preliminary_mask_xy'])



def check(work, decoded=False):
    root = Path(__import__('os').environ.get('PAN_SOURCE_ROOT', PROJECT)) / 'source/precise' / ID
    footprint = root / 'footprint-review.json'
    site = PlacementMeshes(PROJECT, work, read(footprint))
    cut = local_mask(read(root / 'source/frontage-registration.json'))
    group, = site.review['near_tiles']
    ids = np.array(group['feature_local_ids'])
    assert set(ids) == {2572,1450,1086,1895}
    site.link('baseline-far.glb', site.files['far.glb'])
    site.link('baseline-near.glb.gz', site.files[Path(group['file']).name])
    site.link('macro-READY.json', site.files['READY.json'])
    write(work / 'context-features.json', [{'localId': int(k)}for k in ids])
    if not decoded:
        subprocess.run(['node', site.decoders / 'map-decode-source.mjs'],env=site.env, check=True, stdout=subprocess.DEVNULL)
    # Frozen baseline arrays have individual digests and were decoded from the signed GLBs.
    # Decompression is checked by load_values in either mode.
    results = {}
    for level in ('far', 'near'):
        triangles = load_values(work / f'baseline-{level}-triangles.f64', np.float64).reshape(-1, 3, 3)
        triangles[:, :, :2] = triangles[:, :, :2] @ site.axes.T
        explicit = load_values(work/'baseline-far-owners.u32',np.uint32) if level == 'far' else None
        hit_count=0;near_halo=0;foreign_hits=0;peer_distance=float('inf');minimum_gap=float('inf');maximum_offset=0.;closest_neighbor=float('inf')
        observed=set();owned=[];heights=[]
        for offset in range(0,len(triangles),3072):
            block=triangles[offset:offset+3072]
            faces=geo.polygons(block[:,:,:2]);hits=geo.intersects(faces,cut)
            distances=geo.distance(faces,cut);halo=distances<.5
            if explicit is None:
                centroids=geo.points(block[:,:,:2].mean(1))
                scores=np.column_stack([geo.distance(centroids,site.footprints[int(owner)]) for owner in ids])
                nearest=np.argmin(scores,axis=1);labels=ids[nearest];wanted=int(np.flatnonzero(ids==OWNER)[0]);own=scores[:,wanted];other=np.delete(scores,wanted,axis=1).min(1)
                if np.any(halo):
                    minimum_gap=min(minimum_gap,float((other-own)[halo].min()))
                    maximum_offset=max(maximum_offset,float(own[halo].max()))
                    closest_neighbor=min(closest_neighbor,float(other[halo].min()))
                    near_halo+=int(halo.sum())
            else:
                labels=explicit[offset:offset+len(block)]
            observed.update(int(v)for v in np.unique(labels))
            if np.any(labels==OWNER): owned.append(block[labels==OWNER])
            if np.any(labels!=OWNER):peer_distance=min(peer_distance,float(distances[labels!=OWNER].min()))
            foreign_hits+=int(np.sum(hits&(labels!=OWNER)));hit_count+=int(hits.sum())
            if hits.any():heights.append(block[hits,:,2].ravel())
        assert observed==set(ids) and hit_count and foreign_hits==0
        source=site.project_faces(np.concatenate(owned))
        assert peer_distance>.40 and source.difference(cut).area/source.area>.81
        if explicit is None:
            # The upper facade protrudes beyond the older polygon by a few centimetres.
            # Require every centroid within 0.50m of the entire mask to be at least
            # one metre closer to 2572 than the nearest other source in the group.
            assert near_halo>=hit_count and minimum_gap>1.0 and closest_neighbor>maximum_offset+1.0
            attribution={'method':'Nearest original footprint at every triangle in the 0.50m halo; independently checked with typed far feature IDs.','validation_halo_m':.5,'halo_faces':near_halo,'halo_minimum_margin_m':minimum_gap,'max_hit_centroid_distance_to_owner_m':maximum_offset,'closest_nonowner_to_halo_centroid_m':closest_neighbor}
        else:
            attribution={'method':'Per-vertex feature IDs in the archived far mesh'}
        heights = np.concatenate(heights)
        results[level] = {'group_triangles': len(triangles), 'triangles_intersecting_cut': hit_count,
                          'foreign_intersections': 0, 'other_face_distance_m': peer_distance,
                          'source_projected_m2': source.area, 'retained_m2': source.difference(cut).area,
                          'projected_area_basis': 'typed far' if level == 'far' else 'nearest-ring estimate outside cut',
                          'roof_m': float(heights.max()), 'attribution': attribution}
    assert abs(results['far']['roof_m'] - results['near']['roof_m']) < .10
    neighbors = {str(r['local_id']): site.footprints[r['local_id']].distance(cut)
                 for r in site.review['owners']if r['local_id'] != OWNER}
    assert min(neighbors.values()) > .40
    return {'id': ID, 'passed': True, 'source_review_sha256': sha(footprint),
            'mask_local_m': list(cut.exterior.coords), 'mask_area_m2': cut.area,
            'source_levels': results, 'neighbor_distance_m': neighbors}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--reuse-decoded',action='store_true')
    args = parser.parse_args()
    write(args.out, check(args.work,args.reuse_decoded))
