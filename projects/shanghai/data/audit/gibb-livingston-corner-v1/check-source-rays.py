"""Cast the eight photographed targets through the shipping camera and signed near/far city triangles."""
from argparse import ArgumentParser
from pathlib import Path
import json
import sys
import runpy

import numpy as np
import shapely as geo
from shapely.geometry import shape

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes, read, sha, write


intersections = runpy.run_path(str(HERE.parent/'zikawei-convent-central-front-v1/check-source-rays.py'))['intersections']
decode_source = runpy.run_path(str(HERE/'verify-placement.py'))['decode_corner_group']


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('--work',type=Path,required=True)
    parser.add_argument('--out',type=Path,default=HERE/'source-ray-sightlines.json')
    args = parser.parse_args()
    c = read(HERE/'final-placement-contract.json')
    sight = read(HERE/'camera-sightlines.json')
    assert sight['contract_sha256'] == sha(HERE/'final-placement-contract.json')
    review = read(PROJECT/'source/precise'/c['id']/'footprint-review.json')
    site = PlacementMeshes(PROJECT,args.work,review)
    ground = geo.transform(shape(c['replacement_geometry']),site.to_xy)
    owner = c['owner']['feature_local_id']
    group = next(f for f in review['near_tiles'] if owner in f['feature_local_ids'])
    own_meshes = decode_source(site,group,owner)
    result = {}
    for variant,(own,others,assignment) in own_meshes.items():
        mesh = np.concatenate((own,others))
        cases = {}
        for key in ('delivered','east sidewalk','south sidewalk','high crossing','lower crossing'):
            rows = []
            for view in sight['cases'][key]:
                eye = np.array(view['camera_enu'],dtype=float)
                eye[:2] = eye[:2] @ site.axes.T
                witnesses = []
                for probe in view['probes']:
                    target = np.array(probe['target_enu'],dtype=float)
                    target[:2] = target[:2] @ site.axes.T
                    ids,hit = intersections(eye,target,mesh)
                    if len(hit):
                        cut = (ids<len(own)) & geo.intersects(geo.points(hit[:,:2]),ground)
                    else:
                        cut = np.zeros(0,dtype=bool)
                    remaining = ids[~cut]
                    witnesses.append(dict(part=probe['feature'], visible_in_viewport=probe['within_visible_map'],
                        source_intersections_before_cut=len(ids), cleared_owned_corner_intersections=int(cut.sum()),
                        retained_owner_hits=int((remaining<len(own)).sum()), other_group_hits=int((remaining>=len(own)).sum()),
                        clear=not len(remaining) and probe['within_visible_map']))
                rows.append(dict(view=view['view'],targets=witnesses,clear_count=sum(p['clear'] for p in witnesses)))
            cases[key]=rows
        result[variant] = dict(owner_triangles=len(own), other_group_triangles=len(others),assignment=assignment,cases=cases)
    write(args.out,dict(id=c['id'],contract_sha256=sha(HERE/'final-placement-contract.json'),
        camera_sightlines_sha256=sha(HERE/'camera-sightlines.json'),checker_sha256=sha(Path(__file__)),
        source_group=group['id'],source_ids=group['feature_local_ids'],variants=result))
    print({v:{k:[r['clear_count']for r in rows]for k,rows in d['cases'].items()}for v,d in result.items()})
    assert all(v['clear_count']==8 for lod in result.values()for v in lod['cases']['delivered'])


if __name__=='__main__':
    main()
