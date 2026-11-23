"""Check the two true city meshes along the bank street elevation and retain its five group neighbours."""
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

IDENT = 'huangpu-chekiang-industrial-bank-beijing-front'
OWNER = 2404


def evaluate(macro, manifest, vector, output):
    review = read(PROJECT / 'source/precise' / IDENT / 'footprint-review.json')
    meta = read(manifest)
    pack = read(vector)
    own = review['owner']
    group, = review['near_tiles']
    assert own['feature_local_id'] == OWNER and set(group['feature_local_ids']) == {2404, 1700, 297, 2289, 760, 251}
    assert pack['sha256'] == 'e6a2578dd38fdc6ef28737b68ea1e59181efe7d2fbde1d812f76f0a555833495'
    fallback, = [v for v in pack['nearby_features'] if (v['id'], v['component']) == (116367960,17)]
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
        assert bounds['min'][1] >= -.015 and 16.18 < bounds['max'][1] < 16.22
        native = mesh.footprints[OWNER]
        wgs_fallback = shape(fallback['geometry'])
        fallback_local = shapely.transform(wgs_fallback, mesh.to_xy)
        assert native.intersection(fallback_local).area / native.area > .98
        # Only the contact area behind the existing upper street wall is a ground
        # obstacle. The window sills and cornice project over the existing ground floor.
        inside = box(-2.55,.36,2.55,.78)
        assert native.covers(inside) and fallback_local.covers(inside)
        points = [(x,y) for x in [-1.95,-1.15,0,1.15,1.95] for y in [.40,.50,.60]]
        assert all(inside.covers(Point(pt)) for pt in points)
        diagnostics = {}
        for name,tris,owners,ties in grouping(mesh,group):
            selected = tris[owners == OWNER]
            others = tris[owners != OWNER]
            hits = []
            for x in [-2.2,-1.5,0,1.5,2.2]:
                for z in [3.3,5.1,9.2,13.4,18.8]:
                    index,distance,point = raycast(selected,np.array([x,-4.,z]),np.array([0.,1.,0.]))
                    assert np.isfinite(distance) and -.035 <= point[1] <= .27
                    hits.append(dict(x=x,world_z=z,original_face_y=float(point[1])))
            roof = float(selected[:,:,2].max())
            assert abs(roof - 19.2) < .03
            diagnostics[name] = dict(original_owner_triangles=len(selected),retained_neighbor_triangles=len(others),
                                     original_owner_peers={int(k):int(np.count_nonzero(owners==k)) for k in np.unique(owners)},
                                     original_roof_m=roof,original_wall_intersections=hits,owner_area_m2=mesh.ground_faces(selected).area)
        # Cornice on model at 16.16 m, aligned with the top of the 19.20 m bank building.
        altitude = round(min(row['original_roof_m'] for row in diagnostics.values())-16.16,3)
        assert 3.02 < altitude < 3.06
        footprint = mapping(shapely.transform(inside,mesh.to_wgs))
        checked_geometry(footprint,IDENT+' existing bank footprint',collision=True)
        position = review['author_frame']
        collision_inside = [dict(x=x,y=y) for x,y in points]
        contract = dict(id=IDENT,lng=position['anchor']['lng'],lat=position['anchor']['lat'],
                        heading=position['runtime_heading_deg'],altitude=altitude,scale=1,
                        owner={'macro_id':own['macro_id'],'feature_local_id':OWNER},
                        source_feature_ids={'building':[],'building_part':[]},replacement_geometry=None,
                        collision_geometry=footprint,model_geometry_sha256={k:r['sha256'] for k,r in assets.items()},
                        bounds_glb=bounds,navigation={'listed':False,'status':'从北京东路南侧查看浙江兴业银行西端第一窗跨。'},
                        placement={'status':'estimated','note':'按2404号原楼北京东路临街墙装入一间完整窗跨，原有底层在人行道上方3.04米以内保持原状。西南角和其余长翼均保留。'},
                        partial_model=True,model_scope=meta['model_scope_zh'],overviewBearing=2,overviewPitch=62,
                        overviewZoom=21.15,maxDistance=620,lod_switch_in_m=330,lod_switch_out_m=460)
        result = dict(passed=True,id=IDENT,owner=own,near_group_peers=group['feature_local_ids'],
                      original_geometry_cut=False,replaced_original_triangles=0,vector_part=[116367960,17],
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
