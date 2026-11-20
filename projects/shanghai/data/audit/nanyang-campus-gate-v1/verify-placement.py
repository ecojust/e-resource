"""Verify both gate meshes, the open street-to-campus route and the close southern neighbor."""
from argparse import ArgumentParser
from pathlib import Path
import subprocess
import sys

import numpy as np
import shapely as geo

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry

ID='xuhui-nanyang-campus-gate'
OWNER=1575
NEIGHBORS=[797,1393,885,1657]


def main():
    parser=ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--work',type=Path,required=True)
    parser.add_argument('--out',type=Path,default=HERE)
    options=parser.parse_args()
    ref=read(PROJECT/'source/precise'/ID/'footprint-review.json')
    site=PlacementMeshes(PROJECT,options.work,ref)
    assets,bounds,model,collision=site.decode_model(options.manifest)
    source=site.footprints[OWNER]
    group=next(t for t in ref['near_tiles'] if OWNER in t['feature_local_ids'])
    ids=group['feature_local_ids']
    site.link('baseline-near.glb.gz',site.files[Path(group['file']).name])
    site.link('baseline-far.glb',site.files['far.glb'])
    site.link('macro-READY.json',site.files['READY.json'])
    write(site.work/'context-features.json',[{'localId':i}for i in ids])
    subprocess.run(['node',site.decoders/'map-decode-source.mjs'],env=site.env,check=True,stdout=subprocess.DEVNULL)
    variants={}
    for kind in ['near','far']:
        tr=np.fromfile(site.work/f'baseline-{kind}-triangles.f64',np.float64).reshape(-1,3,3)
        tr[:,:,:2]=tr[:,:,:2]@site.axes.T
        if kind=='near':
            dist=np.stack([geo.distance(geo.points(tr[:,:,:2].mean(1)),site.footprints[i])for i in ids],axis=1)
            owners=np.array(ids)[dist.argmin(1)]
            ordered=np.sort(dist[owners==OWNER],axis=1)
            margin=float((ordered[:,1]-ordered[:,0]).min())
            error=float(ordered[:,0].max())
            assert margin>.020 and error<.080
            assignment=dict(method='nearest original building polygon within the bound streamed group',minimum_next_owner_margin_m=margin,maximum_own_distance_m=error)
            # The original 20.9 m gate and 22.6 m neighboring building have thin facade ornaments
            # that physically overlap in projection. Protect the entire neighbor's actual surface.
            protected=site.project_faces(tr[owners==797]).convex_hull.buffer(.015,join_style='mitre')
            cut=source.buffer(.10,join_style='mitre').difference(protected)
            assert cut.covers(source) and cut.geom_type=='Polygon' and len(cut.exterior.coords)<=12
        else:
            owners=np.fromfile(site.work/'baseline-far-owners.u32',np.uint32)
            assignment=dict(method='per-vertex _FEATURE_ID_0')
        building=tr[owners==OWNER];context=tr[owners!=OWNER]
        target=site.project_faces(building);others=site.project_faces(context)
        remaining=target.difference(cut)
        assert remaining.area < (.061 if kind=='near' else 1e-7)
        assert cut.distance(others)>.014 and model.distance(others)>.25
        variants[kind]=dict(group=group['id'],source_faces=len(building),context_faces=len(context),source_area_m2=target.area,
            original_outside_cut_m2=remaining.area,original_retained_percent=100*remaining.area/target.area,
            retained_local_bounds=None if remaining.is_empty else list(remaining.bounds),cut_to_neighbor_mesh_m=cut.distance(others),
            authored_model_to_other_mesh_m=model.distance(others),assignment=assignment)
    neighbors=[dict(local_id=i,source_height_m=next(r['height']for r in ref['owners']if r['local_id']==i),
        distance_to_model_m=model.distance(site.footprints[i]),distance_to_cut_m=cut.distance(site.footprints[i]))for i in NEIGHBORS]
    assert all(row['distance_to_model_m']>.25 and row['distance_to_cut_m']>.03 for row in neighbors)
    checks=[]
    cases=[(f'central route at {y:.1f} m',[x,y],False)for y in [-2.6,.2,2.8,4.80,5.9,8.4,10.0,12.7]for x in [-.92,.92]]
    cases.extend([('southern wing base',[-4.30,5.48],True),('northern wing base',[5.90,5.48],True),
                  ('fixed southern side door',[-2.0,4.79],True),('fixed northern side door',[2.0,4.79],True),
                  ('opened southern leaf',[-1.24,5.52],True),('opened northern leaf',[1.24,5.52],True),
                  ('left guardian plinth',[-4.97,-1.15],True),('right guardian plinth',[4.97,-1.15],True),
                  ('pavement beside southern lion',[-4.0,-1.16],False),('pavement beside northern lion',[4.0,-1.16],False),
                  ('north exterior walkway',[7.74,6.2],False)])
    for desc,xy,expected in cases:
        point=geo.Point(xy);observed=collision.covers(point);assert observed==expected,(desc,xy)
        checks.append(dict(name=desc,xy=xy,model_obstacle=observed,source_cut=cut.covers(point)))
    r=next(k for k in ref['owners']if k['local_id']==OWNER)
    contract=dict(id=ID,owner=dict(macro_id=ref['frozen_macro'],feature_local_id=OWNER),source_feature_ids=dict(building=[r['key'][9:]],building_part=[]),
        replacement_geometry=site.wgs(cut),collision_geometry=site.wgs(collision),lng=site.lon,lat=site.lat,heading=ref['author_frame']['runtime_heading_deg'],
        scale=1,altitude=0,bounds_glb=bounds,model_geometry_sha256={k:v['sha256']for k,v in assets.items()},
        overviewBearing=255,overviewPitch=54,overviewZoom=19.42,maxDistance=630,lod_switch_in_m=550,lod_switch_out_m=680,
        navigation=dict(listed=False,status='从华山路正面可见双狮和校名竖牌，中央门道贯通校园。'),
        placement=dict(status='map-aligned',note='华山路1954号现存1935年正门对应实名地块1575，南邻797、外围校墙、桥灯和其他教学楼独立。'),
        partial_model=True,model_scope=read(options.manifest)['scope'])
    checked_geometry(contract['replacement_geometry'],'replacement');checked_geometry(contract['collision_geometry'],'collision',collision=True)
    write(options.out/'final-placement-contract.json',contract)
    write(options.out/'placement-geometry.json',dict(id=ID,assets=assets,manifest_sha256=sha(options.manifest),source_area_m2=source.area,
        model_m2=model.area,collision_m2=collision.area,mask_m2=cut.area,variants=variants,neighbors=neighbors,ground_probes=checks,
        checker_sha256=sha(Path(__file__)),decoder_sha256=sha(PROJECT/'tools/candidate_placement_meshes.py')))


if __name__=='__main__':
    main()
