"""Decode all three delivered variants and the real source near/far tiles, with their adjacent party-wall owner."""
import argparse
import gzip
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess

import numpy as np
import shapely as geo
from shapely.geometry import mapping, shape

AUDIT=Path(__file__).resolve().parent
PROJECT=AUDIT.parents[2]
MODEL='huangpu-yongnian-life-insurance-building'
SRC=PROJECT/'source/precise'/MODEL/'footprint-review.json'
DECODER=PROJECT/'data/audit/postal-office-v1'
GEOM=PROJECT/'data/audit/country-hospital-v1/verify-placement.py'


def read(p):return json.loads(p.read_bytes())
def write(p,data):p.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def link(source,path):
    path.unlink(missing_ok=True)
    path.symlink_to(source.resolve())


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/MODEL/'manifest.json')
    cli.add_argument('--macro',type=Path,required=True)
    cli.add_argument('--work',type=Path,required=True)
    cli.add_argument('--out',type=Path,default=AUDIT)
    args=cli.parse_args()
    work=args.work.resolve();out=args.out.resolve()
    work.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
    spec=importlib.util.spec_from_file_location('projection',GEOM)
    g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
    src=read(SRC);manifest=read(args.manifest)
    for name,ref in src['frozen_bindings'].items():
        p=args.macro/name
        assert sha(p)==ref['sha256'] and p.stat().st_size==ref['bytes']
    records=json.loads(gzip.decompress((args.macro/'feature-table.json.gz').read_bytes()))['features']
    ready=read(args.macro/'READY.json')
    by_id={r['localId']:r for r in records}
    anchor=src['anchor'];lon,lat=anchor['lng'],anchor['lat']
    k=6371008.8*math.cos(math.radians(lat));phi=math.asinh(math.tan(math.radians(lat)))
    def xy(p):
        return np.column_stack((np.radians(p[:,0]-lon)*k,(np.arcsinh(np.tan(np.radians(p[:,1])))-phi)*k))
    def wgs(p):
        return np.column_stack((lon+np.degrees(p[:,0]/k),np.degrees(np.arctan(np.sinh(phi+p[:,1]/k)))))
    def polygon(p):return mapping(geo.transform(p,wgs))
    def op(i):return geo.transform(shape(by_id[i]['geometry']),xy)
    env=dict(os.environ,POSTAL_REPO=str(PROJECT.parents[1]),POSTAL_MAPPING_WORK=str(work),POSTAL_ASSET_PREFIX='')
    assets={};bounds=[];models=[];ground=[]
    for v,role in [('raw','raw'),('web','full'),('lod','lod')]:
        rec=manifest['assets'][role];p=args.manifest.parent/rec['file']
        assert sha(p)==rec['sha256'] and p.stat().st_size==rec['bytes']
        assets[v]={k:rec[k] for k in ['bytes','sha256','triangles']}
        link(p,work/(v+'.glb'))
    subprocess.run(['node',DECODER/'map-decode-delivered.mjs',work],check=True,env=env,stdout=subprocess.DEVNULL)
    for rec in read(work/'delivered-decode.json'):
        tris=np.fromfile(rec['triangle_file'],np.float64).reshape(-1,3,3)
        assert len(tris)==assets[rec['variant']]['triangles'] and np.isfinite(tris).all()
        bounds.append([tris.min((0,1)),tris.max((0,1))])
        local=tris[:,:,[0,2,1]]*[1,-1,1]
        h=math.radians(-17.85)
        local[:,:,:2]=local[:,:,:2]@np.array([[math.cos(h),-math.sin(h)],[math.sin(h),math.cos(h)]])
        models.append(g.project_triangles(local))
        ground.append(g.ground_projection(local))
    model=geo.union_all(models,grid_size=.0001)
    structure=geo.union_all(ground,grid_size=.001)
    # Use a 14 cm pedestrian envelope around the ground-floor walls, display surrounds and corner piers.
    # The 13 cm simplification keeps the exterior inside the renderer’s 256-vertex bound.
    collision=structure.buffer(.140,join_style='mitre').simplify(.130,preserve_topology=True)
    assert collision.is_valid and structure.difference(collision).area<.001
    link(args.macro/'far.glb',work/'baseline-far.glb')
    link(args.macro/'READY.json',work/'macro-READY.json')
    write(work/'initial-local-frame.json',{'anchor':anchor})
    near=src['near']
    ids=near['local_ids'];owner_id=src['owner']['feature_local_id']
    # The Former the retained west property shares the Union Building's northern party line.
    # Expand the second source group too: far IDs are explicit, near layer is filtered per tile.
    adjacent=1397
    second=next(t for t in ready['near'] if adjacent in t['featureLocalIds'])
    assert owner_id not in second['featureLocalIds']
    target={};peer={};neighbor={};ownership={};nearest_margins={};retained_near_group=None
    for group_ids,file,label in [(ids,near['file'],'target group'),(second['featureLocalIds'],second['file'],'party-wall group')]:
        source_tile=args.macro/file
        assert sha(source_tile)==next(t['sha256']for t in ready['near'] if t['file']==file)
        write(work/'context-features.json',[{'localId':i}for i in group_ids])
        link(source_tile,work/'baseline-near.glb.gz')
        subprocess.run(['node',DECODER/'map-decode-source.mjs'],check=True,env=env,stdout=subprocess.DEVNULL)
        for v in ['near','far']:
            tris=np.fromfile(work/f'baseline-{v}-triangles.f64',np.float64).reshape(-1,3,3)
            if v=='near':
                centers=geo.points(tris[:,:,:2].mean(axis=1))
                ds=np.stack([geo.distance(centers,op(i))for i in group_ids],axis=1)
                who=np.asarray(group_ids)[ds.argmin(axis=1)]
                target_index=owner_id if label=='target group' else adjacent
                if label=='party-wall group':
                    # Its eastern bank shares edges with other retained buildings in
                    # this separate near file. Preserve every triangle in the file,
                    # without assigning an ambiguous party-wall triangle to one owner.
                    retained_near_group=g.project_triangles(tris)
                    possible=ds[:,group_ids.index(adjacent)]<=ds.min(axis=1)+.30
                    neighbor[v]=g.project_triangles(tris[possible])
                    ownership[label+' '+v]={'ids':group_ids,'input':file,'sha256':sha(source_tile),
                        'triangle_count':len(tris),'possible_west_neighbor_triangles':int(possible.sum()),
                        'method':'All triangles retained. For the overlap bound, include every triangle within 0.30 m of the closest source polygon for the retained west property.'}
                    continue
                ordered=np.sort(ds[who==target_index],axis=1)
                offset=float(ordered[:,0].max());gap=float((ordered[:,1]-ordered[:,0]).min())
                # Require positive separation from the next owner even after allowing four times
                # the maximum observed source-to-footprint offset. Check the whole retained group below.
                assert offset<.30 and gap>max(.25,4*offset),(label,offset,gap)
                nearest_margins[label]={'max_assigned_distance_m':offset,'min_runner_up_gap_m':gap}
            else:who=np.fromfile(work/'baseline-far-owners.u32',np.uint32)
            assert set(who)==set(group_ids)
            if label=='target group':
                target[v]=g.project_triangles(tris[who==owner_id])
                peer[v]=g.project_triangles(tris[who!=owner_id])
            else:neighbor[v]=g.project_triangles(tris[who==adjacent])
            ownership[label+' '+v]={'ids':group_ids,'input':file if v=='near' else 'far.glb',
                'sha256':sha(source_tile if v=='near' else args.macro/'far.glb'),
                'pass':True,'triangles_per_owner':{int(i):int(np.sum(who==i))for i in group_ids}}
    # A compact owner-scoped contour covers all projected source wall/ornament triangles, including facade offsets.
    mask=geo.union_all([op(owner_id),*target.values()],grid_size=.002).buffer(.15,join_style='mitre').simplify(.07,preserve_topology=True)
    assert all(m.difference(mask).area<.00001 for m in target.values())
    assert all(mask.distance(x)>1 for x in peer.values())
    polygons=[collision] if collision.geom_type=='Polygon' else list(collision.geoms)
    assert all(len(g.exterior.coords)<=256 for g in polygons)
    b=np.asarray(bounds)
    shared=op(owner_id).intersection(op(adjacent)).area
    all_owners=[(i,op(i)) for i in by_id if i!=owner_id and shape(by_id[i]['geometry']).distance(geo.Point(lon,lat))<.0017]
    neighbors=[{'id':i,'mask_overlap_m2':mask.intersection(p).area,'model_overlap_m2':model.intersection(p).area} for i,p in all_owners if mask.intersects(p)]
    assert {q['id']for q in neighbors}=={adjacent},neighbors
    # The adjoining five-member near group is wholly retained, even independently of the
    # per-triangle attribution. No foreground replacement mesh may enter its projection.
    assert retained_near_group is not None and model.intersection(retained_near_group).area<.01, ('model crossing entire adjacent near group',model.intersection(retained_near_group).area)
    # Independent per-tile scope and explicit far IDs protect the shared neighbor from the owner-only mask.
    assert all(model.intersection(x).area<.01 for x in neighbor.values()),[(k,model.intersection(x).area)for k,x in neighbor.items()]
    # The runtime straightens segments in WGS84. Subtract there to preserve exact containment
    # across newly introduced party-wall vertices even after the Mercator conversion.
    adjoining_outline=shape(by_id[adjacent]['geometry'])
    adjoining_mvt=shape(src['fallback_vector']['neighbor_geometry'])
    native_wgs=shape(polygon(mask))
    write(work/'measured-native-replacement-wgs84.json',mapping(native_wgs))
    # Add a one millimetre clearance to avoid a zero-width spike where the
    # WGS84 source and separately quantized vector edge almost coincide.
    # Work in native units for the clearance, then subtract on the published coordinates.
    around=geo.transform(geo.transform(geo.union_all([adjoining_outline,adjoining_mvt]),xy).buffer(.001,join_style='mitre'),wgs)
    osm_wgs=native_wgs.difference(geo.union_all([adjoining_outline,adjoining_mvt,around]))
    if not osm_wgs.is_valid:raise AssertionError(geo.is_valid_reason(osm_wgs))

    assert osm_wgs.intersection(adjoining_mvt).area<1e-18
    osm_mask=geo.transform(osm_wgs,xy)
    assert osm_mask.is_valid and osm_wgs.intersection(shape(by_id[adjacent]['geometry'])).area<1e-19,(geo.is_valid_reason(osm_mask),osm_wgs.intersection(adjoining_outline).area)
    contract={'id':MODEL,'owner':{'macro_id':src['owner']['macro_id'],'feature_local_id':owner_id},
        'source_feature_ids':{'building':[src['owner']['key'].split(':')[1]],'building_part':[]},
        'replacement_geometry':polygon(mask),'osm_replacement_geometry':mapping(osm_wgs),'collision_geometry':polygon(collision),
        'lng':lon,'lat':lat,'heading':-17.85,'scale':1,'altitude':0,
        'bounds_glb':{'min':b[:,0].min(0).tolist(),'max':b[:,1].max(0).tolist()},
        'model_geometry_sha256':{k:v['sha256']for k,v in assets.items()},
        'overviewBearing':-133,'overviewPitch':57,'overviewZoom':19.06,'maxDistance':500,'lod_switch_in_m':550,'lod_switch_out_m':700,
        'navigation':{'listed':False,'status':'广东路与四川中路路口的方门、爱奥尼克式红花岗石柱及双街券窗。'},
        'placement':{'status':'estimated','note':'广东路93号。外墙按2011年两幅街照，局部第四层按地方志和2018、2021、2024三期发布航片。西侧1397和同组另外五栋均保留。'},
        'partial_model':False,'model_scope':'东北转角方门、磨光花岗石柱与两街券窗，上两层爱奥尼克柱、三角与弧状窗楣和局部第四层。背墙、局部屋盖及标高估计。'}
    write(out/'final-placement-contract.json',contract)
    report={'id':MODEL,'source_sha256':sha(SRC),'manifest_sha256':sha(args.manifest),'script_sha256':sha(Path(__file__)),
            'decoders_sha256':{str(p.relative_to(PROJECT)):sha(p) for p in [DECODER/'map-decode-source.mjs',DECODER/'map-decode-delivered.mjs',GEOM]},
            'contract_sha256':sha(out/'final-placement-contract.json'),'assets':assets,'registered_owner_area_m2':op(owner_id).area,
            'collision_area_m2':collision.area,'model_projected_area_m2':model.area,'cut_area_m2':mask.area,
            'original_shared_source_overlap_m2':shared,'osm_vector_mask_area_m2':osm_mask.area,
            'adjacent_source_overlap_with_osm_mask_m2':osm_mask.intersection(op(adjacent)).area,'all_macro_neighbors_crossing_mask':neighbors,
            'party_wall_preservation':{v:{'neighbor_id':adjacent,'neighbor_area_m2':x.area,
                  'model_overlap_m2':model.intersection(x).area,'model_clearance_m':model.distance(x),'clip_overlap_before_owner_filter_m2':mask.intersection(x).area,
                  'exclusion':'Explicit native far feature ID' if v=='far' else 'Separate source near tile without target owner'}for v,x in neighbor.items()},
            'adjoining_entire_near_group':{'ids':second['featureLocalIds'],'projected_area_m2':retained_near_group.area,'model_overlap_m2':model.intersection(retained_near_group).area,'clearance_m':model.distance(retained_near_group)},
            'owner_classification_margins':nearest_margins,'target_variants':{v:{'original_area_m2':p.area,'retained_m2':p.difference(mask).area,
                       'closest_shared_group_neighbor_m':mask.distance(peer[v])}for v,p in target.items()},'source_decode':ownership}
    write(out/'placement-geometry.json',report)
    print('verified',MODEL,neighbors,collision.area)


if __name__=='__main__':main()
