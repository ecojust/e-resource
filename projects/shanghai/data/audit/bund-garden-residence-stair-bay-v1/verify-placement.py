"""Check the two true city meshes at the residence staircase and retain four grouped neighbours."""
from argparse import ArgumentParser
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import runpy
import sys

import numpy as np
import shapely
from shapely.geometry import Point, Polygon, box, mapping, shape

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT / 'tools'))
from candidate_placement_meshes import PlacementMeshes, read, sha, write
from build_candidate_city_integrations import checked_geometry

IDENT = 'huangpu-bund-garden-residence-stair-bay'
OWNER = 1555


def evaluate(macro, manifest, vector, output):
    review = read(PROJECT / 'source/precise' / IDENT / 'footprint-review.json')
    meta = read(manifest)
    pack = read(vector)
    own = review['owner']
    group, = review['near_tiles']
    assert own['feature_local_id'] == OWNER and set(group['feature_local_ids']) == {1555, 2884, 2747, 2383, 1754}
    assert pack['sha256'] == '2cc557168a2d1e041735028eab34d233a0ed2c3bf04497e91cfa92dbf27cb48c'
    fallback, = [v for v in pack['nearby_features'] if (v['id'], v['component']) == (3000545220,23)]
    grouping = runpy.run_path(str(HERE.parent / 'metropole-hotel-v1/verify-placement.py'))['grouped_sources']
    raycast = runpy.run_path(str(HERE.parent / 'postal-office-v1/independent-glb-review-helpers.py'))['first_hit']
    with TemporaryDirectory() as private:
        temp = Path(private)
        for source in review['frozen_bindings']:
            filename = Path(source['repository_path']).name
            original = macro / filename
            assert original.stat().st_size == source['bytes'] and sha(original) == source['sha256']
            (temp / filename).symlink_to(original.resolve())
        mesh = PlacementMeshes(PROJECT,temp,review)
        assets,bounds,profile,whole = mesh.decode_model(manifest)
        assert bounds['min'][1] >= -.015 and 6.77 < bounds['max'][1] < 6.82
        native = mesh.footprints[OWNER]
        wgs_fallback = shape(fallback['geometry'])
        fallback_local = shapely.transform(wgs_fallback, mesh.to_xy)
        assert native.intersection(fallback_local).area / native.area > .98
        # Only the contact area behind the existing upper street wall is a ground
        # obstacle. The window sills and cornice project over the existing ground floor.
        inside = box(-1.49,.36,1.49,.78)
        assert native.covers(inside) and fallback_local.covers(inside)
        points = [(x,y) for x in [-1.32,-.75,0,.75,1.32] for y in [.40,.50,.60]]
        assert all(inside.covers(Point(pt)) for pt in points)
        diagnostics = {}
        for name,tris,owners,ties in grouping(mesh,group):
            selected = tris[owners == OWNER]
            others = tris[owners != OWNER]
            hits = []
            for x in [-1.67,-.82,0,.82,1.67]:
                for z in [1.0,3.1,5.1,7.2,9.2]:
                    index,distance,point = raycast(selected,np.array([x,-4.,z]),np.array([0.,1.,0.]))
                    assert np.isfinite(distance) and -.085 <= point[1] <= .24
                    hits.append(dict(x=x,world_z=z,original_face_y=float(point[1])))
            roof = float(selected[:,:,2].max())
            assert abs(roof - 9.60) < .03
            diagnostics[name] = dict(original_owner_triangles=len(selected),retained_neighbor_triangles=len(others),
                                     original_owner_peers={int(k):int(np.count_nonzero(owners==k)) for k in np.unique(owners)},
                                     original_roof_m=roof,original_wall_intersections=hits,owner_area_m2=mesh.ground_faces(selected).area)
        # The stone cap stays 0.06 m below the retained 9.60 m city roof.
        altitude = round(min(row['original_roof_m'] for row in diagnostics.values())-6.85,3)
        assert 2.745 < altitude < 2.755
        footprint = mapping(shapely.transform(inside,mesh.to_wgs))
        checked_geometry(footprint,IDENT+' retained garden house footprint',collision=True)
        position = review['author_frame']
        collision_inside = [dict(x=x,y=y) for x,y in points]
        contract = dict(id=IDENT,lng=position['anchor']['lng'],lat=position['anchor']['lat'],
                        heading=position['runtime_heading_deg'],altitude=altitude,scale=1,
                        owner={'macro_id':own['macro_id'],'feature_local_id':OWNER},
                        source_feature_ids={'building':[],'building_part':[]},replacement_geometry=None,
                        collision_geometry=footprint,model_geometry_sha256={k:r['sha256'] for k,r in assets.items()},
                        bounds_glb=bounds,navigation={'listed':False,'status':'从汉口路南侧看花园住宅的错层钢窗。'},
                        placement={'status':'estimated','note':'1555号原楼南墙仅添加两排外窗和砖石窄带，原底层与同组邻栋和园门前的步行地面保留。'},
                        partial_model=True,model_scope=meta['model_scope_zh'],overviewBearing=346,overviewPitch=64,
                        overviewZoom=21.15,maxDistance=620,lod_switch_in_m=330,lod_switch_out_m=460)
        result = dict(passed=True,id=IDENT,owner=own,near_group_peers=group['feature_local_ids'],
                      original_geometry_cut=False,replaced_original_triangles=0,vector_part=[3000545220,23],
                      checked_model_files=assets,frozen_inputs={s['repository_path']:s['sha256'] for s in review['frozen_bindings']},
                      source_variants=diagnostics,ground_witnesses_inside_original=collision_inside,
                      collision_retained_area_m2=inside.area,source_facade_length_m=review['bay_width_m'],
                      public_street_clear_height_m=altitude)
        output.mkdir(exist_ok=True,parents=True)
        write(output/'final-placement-contract.json',contract)
        write(output/'placement-geometry.json',result)
        return result


if __name__ == '__main__':
    parser=ArgumentParser(description=__doc__)
    parser.add_argument('--macro',required=True,type=Path)
    parser.add_argument('--manifest',required=True,type=Path)
    parser.add_argument('--vector',required=True,type=Path)
    parser.add_argument('--out',type=Path,default=HERE)
    args=parser.parse_args()
    report=evaluate(args.macro,args.manifest,args.vector,args.out)
    print(report['source_facade_length_m'],report['public_street_clear_height_m'])
