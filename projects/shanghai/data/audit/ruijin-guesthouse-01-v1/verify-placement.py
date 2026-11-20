"""Replace the two segmentation fragments of the labelled Morris house and its portico."""
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

ID='huangpu-ruijin-guesthouse-01'
HOUSE=1250
PORCH=2335
RETAINED=[799,3003,2513,4074]


def accepted_owners(site,group):
    ids=group['feature_local_ids']
    site.link('baseline-far.glb',site.files['far.glb'])
    site.link('baseline-near.glb.gz',site.files[Path(group['file']).name])
    site.link('macro-READY.json',site.files['READY.json'])
    write(site.work/'context-features.json',[dict(localId=i)for i in ids])
    subprocess.run(['node',site.decoders/'map-decode-source.mjs'],env=site.env,check=True,stdout=subprocess.DEVNULL)
    for variant in ['near','far']:
        tris=np.fromfile(site.work/('baseline-'+variant+'-triangles.f64'),np.float64).reshape(-1,3,3)
        tris[:,:,:2]=tris[:,:,:2]@site.axes.T
        if variant=='far':
            owner=np.fromfile(site.work/'baseline-far-owners.u32',np.uint32)
            assignment={'method':'per-vertex _FEATURE_ID_0'}
        else:
            points=geo.points(tris[:,:,:2].mean(1))
            distances=np.stack([geo.distance(points,site.footprints[i])for i in ids],axis=1)
            owner=np.asarray(ids)[distances.argmin(1)]
            selected=np.sort(distances[np.isin(owner,[HOUSE,PORCH])],axis=1)
            maximum_own=float(selected[:,0].max());min_gap=float((selected[:,1]-selected[:,0]).min())
            assert maximum_own<.30 and min_gap>2,(maximum_own,min_gap)
            assignment=dict(method='triangles to verified frozen group footprints',largest_own_distance_m=maximum_own,next_owner_margin_m=min_gap)
        assert set(owner)==set(ids)
        yield variant,tris,owner,assignment


def main():
    cli=ArgumentParser(description=__doc__)
    cli.add_argument('--manifest',required=True,type=Path)
    cli.add_argument('--work',required=True,type=Path)
    cli.add_argument('--out',type=Path,default=HERE)
    args=cli.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    src=read(PROJECT/'source/precise'/ID/'footprint-review.json')
    site=PlacementMeshes(PROJECT,args.work,src);assets,bounds,model,_=site.decode_model(args.manifest)
    ground=[]
    for rec in read(site.work/'delivered-decode.json'):
        pos=np.fromfile(rec['triangle_file'],np.float64).reshape(-1,3,3)[:,:,[0,2,1]]*[1,-1,1]
        materials=np.fromfile(rec['triangle_material_ids_file'],np.uint16)
        paving=rec['material_names'].index('garden threshold')
        ground.append(site.ground_faces(pos[materials!=paving]))
    # The closed-room floor reaches the building's alignment. Only the doorway
    # niche above its low sill remains walkable up to the actual inset oak doors.
    clear_door=geo.box(-1.23,-5.08,1.23,1.245)
    collision=geo.union_all(ground,grid_size=.001).difference(clear_door).simplify(.024)
    owner_ids=[HOUSE,PORCH];source_rows={r['local_id']:r for r in src['owners']}
    group=next(g for g in src['near_tiles']if HOUSE in g['feature_local_ids']and PORCH in g['feature_local_ids'])
    mask=geo.union_all([site.footprints[i].buffer(.36,join_style='mitre')for i in owner_ids])
    assert mask.geom_type=='MultiPolygon' and len(mask.geoms)==2
    measurements={}
    for key,tris,ids,assignment in accepted_owners(site,group):
        other=site.project_faces(tris[~np.isin(ids,owner_ids)])
        assert mask.disjoint(other) and model.disjoint(other),(key,model.intersection(other).area)
        obs={}
        for i in owner_ids:
            selected=tris[ids==i];projected=site.project_faces(selected)
            assert mask.covers(projected),(key,i,projected.difference(mask).area)
            assert model.intersection(projected).area>.63*projected.area,(key,i,model.intersection(projected).area)
            obs[i]=dict(triangles=len(selected),projected_m2=projected.area,inside_candidate_m2=model.intersection(projected).area,
                        max_source_height_m=float(selected[:,:,2].max()),all_vertices_in_mask=bool(mask.covers(geo.multipoints(selected[:,:,:2].reshape(-1,2)))))
        measurements[key]=dict(components=obs,assignment=assignment,other_triangles=int(sum(~np.isin(ids,owner_ids))),
            nearest_other_model_m=model.distance(other),nearest_other_mask_m=mask.distance(other))
    clearance=sorted((model.distance(p),mask.distance(p),i)for i,p in site.footprints.items()if i not in owner_ids)
    assert clearance[0][0]>1.40
    groups=[dict(macro_id=src['frozen_macro'],feature_local_id=i,key=source_rows[i]['key'])for i in owner_ids]
    tests=[('enclosed east drawing room',[-10,6],True),('enclosed west drawing room',[9,8],True),
           ('walkable front bay',[0,-3.0],False),('ground inside recessed entrance',[0,.54],False),
           ('closed oak door',[0,1.35],True),('first paired Tuscan shaft',[-2.10,-4.64],True),
           ('garden lawn',[0,-10.25],False),('east garden approach',[-14,-3.5],False)]
    ground_case=[]
    for n,xy,solid in tests:
        point=geo.Point(*xy);assert bool(collision.covers(point))==solid,(n,collision.distance(point))
        ground_case.append(dict(name=n,xy=xy,expected='building'if solid else None,
                                modelObstacle=solid,cut=bool(mask.covers(point))))
    contract=dict(id=ID,owner=groups[0],owners=groups,source_feature_ids=dict(building=[source_rows[i]['key'][9:]for i in owner_ids],building_part=[]),
        replacement_geometry=site.wgs(mask),collision_geometry=site.wgs(collision),lng=site.lon,lat=site.lat,
        heading=src['author_frame']['runtime_heading_deg'],scale=1,altitude=0,bounds_glb=bounds,
        model_geometry_sha256={k:r['sha256']for k,r in assets.items()},
        overviewBearing=166,overviewPitch=47,overviewZoom=19.05,maxDistance=490,lod_switch_in_m=560,lod_switch_out_m=710,
        navigation=dict(listed=False,status='瑞金宾馆1号楼庭院外观俯瞰。'),
        placement=dict(status='estimated',note='酒店总平面明确标1#。主屋不完整片1250及门廊片2335分别裁剪，保留799、栋间廊3003及现代酒店2513。'),partial_model=True,model_scope=read(args.manifest)['scope'])
    for k in ['replacement','collision']:checked_geometry(contract[k+'_geometry'],k,collision=k=='collision')
    case=dict(id=ID,previous='changning-xingguo-guesthouse-01',neighbors=RETAINED,addedOwners=owner_ids,
              groupTriangles=len(owner_ids)*sum(len(g.exterior.coords)-3 for g in mask.geoms),
              front=dict(center=[0,.27],elevation=3.20,pitch=54,zoom=19.61,bearingOffset=7),
              roof=dict(center=[0,8],elevation=4.6,pitch=34,zoom=19.16,bearingOffset=17),ground=ground_case,
              neighborGround={i:site.wgs(site.footprints[i].representative_point())['coordinates']for i in RETAINED})
    write(args.out/'final-placement-contract.json',contract)
    write(args.out/'map-case.json',case)
    write(args.out/'placement-geometry.json',dict(id=ID,asset_manifest_sha256=sha(args.manifest),assets=assets,
        owner_fragments=owner_ids,scanned=measurements,group=group,model_projection_m2=model.area,
        collision_m2=collision.area,source_mask_m2=mask.area,nearest_retained=[dict(local_id=i,model_gap_m=d,mask_gap_m=m)for d,m,i in clearance[:7]],
        ground_witnesses=ground_case,checker_sha256=sha(Path(__file__)),common_checker=sha(PROJECT/'tools/candidate_placement_meshes.py')))


if __name__=='__main__':
    main()
