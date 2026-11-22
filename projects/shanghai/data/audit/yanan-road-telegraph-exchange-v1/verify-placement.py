"""Measure only the photographed East Yanan Road elevation against the original telegraph exchange and retained neighboring buildings."""
import argparse
from pathlib import Path
import sys
import runpy
import tempfile
import numpy as np
import shapely as geo
from shapely.geometry import Polygon, Point, MultiLineString, LineString, box, mapping, shape

audit=Path(__file__).resolve().parent
project=audit.parents[2]
sys.path.insert(0,str(project/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry,check_source_section_caps

model='huangpu-yanan-road-telegraph-exchange'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--macro',type=Path,required=True)
parser.add_argument('--vector',type=Path,required=True)
parser.add_argument('--manifest',type=Path,default=project/'assets/models/candidates'/model/'manifest.json')
parser.add_argument('--out',type=Path,default=audit)
args=parser.parse_args()
src=project/'source/precise'/model/'footprint-review.json'
ref,manifest,vector=read(src),read(args.manifest),read(args.vector)
assert vector['sha256']=='2cc557168a2d1e041735028eab34d233a0ed2c3bf04497e91cfa92dbf27cb48c'
owner=ref['owner'];group,=ref['near_tiles'];target=owner['feature_local_id']
assert target==1913 and set(group['feature_local_ids'])=={444,181,2544,1913}

with tempfile.TemporaryDirectory()as folder:
    scratch=Path(folder)
    for binding in ref['frozen_bindings']:
        suffix=binding['repository_path'].split(owner['macro_id']+'/')[1]
        (scratch/Path(suffix).name).symlink_to((args.macro/suffix).resolve())
    mesh=PlacementMeshes(project,scratch,ref)
    assets,bounds,profile,ground=mesh.decode_model(args.manifest)
    original=mesh.footprints[target]
    # The rear cut crosses both original side walls and lies behind the new short returns.
    mask=box(-14.94,-.48,14.94,3.18)
    grouped_sources=runpy.run_path(str(audit.parent/'metropole-hotel-v1/verify-placement.py'))['grouped_sources']
    nearfar={}
    for variant,trs,ids,ties in grouped_sources(mesh,group):
        assert set(ids)==set(group['feature_local_ids'])
        if ties.any():assert mesh.project_faces(trs[ties]).disjoint(mask)
        ours=trs[ids==target]
        # Quantify the margin of the target-centroid assignment separately from any ties at neighboring buildings.
        pts=geo.points(ours[:,:,:2].mean(1))
        own_d=geo.distance(pts,original)
        peer_ds=np.stack([geo.distance(pts,mesh.footprints[i])for i in group['feature_local_ids'] if i!=target])
        margin=float((peer_ds.min(axis=0)-own_d).min());assert margin>5.7 and float(own_d.max())<.10
        nearfar[variant]=(ours,trs[ids!=target],{'method':'_FEATURE_ID_0' if variant=='far' else 'four native members and centroid-to-footprint distances','ambiguous_faces_elsewhere':int(ties.sum()),'own_max_edge_excursion_m':float(own_d.max()),'minimum_margin_m':margin})
    assert mask.covers(profile),profile.bounds
    collision=ground.buffer(.018,join_style='mitre').simplify(.018,preserve_topology=True)
    assert ground.difference(collision).area<.01
    mask_geo=mesh.wgs(mask);exact=shape(mask_geo)
    neighboring={i:poly.distance(mask)for i,poly in mesh.footprints.items()if i!=target}
    assert min(neighboring.values())>7.9,sorted(neighboring.items(),key=lambda r:r[1])[:5]
    measured={};edges={}
    for name,(triangles,others,assignment)in nearfar.items():
        footprint=mesh.project_faces(triangles);peers=mesh.project_faces(others)
        removed=footprint.intersection(mask);kept=footprint.difference(mask)
        assert removed.area>87 and kept.area>1000 and peers.distance(mask)>7.8,(name,removed.area,kept.area,peers.distance(mask))
        seam=geo.line_merge(mask.boundary.intersection(footprint))
        assert seam.geom_type=='LineString'and 35.9<seam.length<36.6
        edges[name]=seam
        measured[name]={'original_m2':footprint.area,'removed_front_m2':removed.area,'retained_rear_m2':kept.area,'other_group_owner_gap_m':peers.distance(mask),'height_m':float(triangles[:,:,2].max()),'assignment':assignment}
    assert edges['near'].hausdorff_distance(edges['far'])<.10
    keys={};source_component=None
    for r in vector['nearby_features']:
        poly=geo.transform(shape(r['geometry']),mesh.to_xy)
        area=poly.intersection(mask).area
        k=f"{r['id']}/{r['component']}"
        if (r['id'],r['component'])==(194200050,11):
            source_component={'key':k,'area_m2':poly.area,'retained_m2':poly.difference(mask).area,'intersection_m2':area}
            assert area>85 and source_component['retained_m2']>1000
        else:assert area<.001,(k,area)
        keys[k]=area
    assert source_component
    far_native=mesh.project_faces(nearfar['far'][0])
    caps=exact.boundary.intersection(geo.transform(far_native,mesh.to_wgs))
    if caps.geom_type=='LineString':caps=MultiLineString([caps])
    assert caps.geom_type=='MultiLineString' and len(caps.geoms)==1
    current=read(args.macro/'READY.json')
    samples=[]
    for label,x,y,blocked,cut,keep in [
        ('central door and plinth',0,1.16,True,True,False),('western door',-11.7,1.42,True,True,False),
        ('eastern door',11.7,1.42,True,True,False),('western corner',-14.62,1.5,True,True,False),
        ('retained behind middle',0,4.4,False,False,True),('retained northwest room',-13,22,False,False,True),
        ('retained northeast room',13,28,False,False,True),('East Yanan Road pavement',0,-2.3,False,False,False),
        ('under projecting canopy',0,-.19,False,True,False),('outside eastern corner',16,1.8,False,False,False)]:
        pt=Point(x,y);assert collision.covers(pt)==blocked and mask.covers(pt)==cut
        assert (original.covers(pt)and not mask.covers(pt))==keep
        samples.append({'label':label,'xy':[x,y],'point':mesh.to_wgs(np.array([[x,y]]))[0].tolist(),'model_collision':blocked,'under_mask':cut,'retained_source':keep})
    roads={r['name']:LineString(mesh.to_xy(np.array(r['geometry']))).distance(mask)for r in ref['surveyed_streets']}
    assert min(roads.values())>3
    contract={'id':model,**ref['author_frame']['anchor'],'heading':ref['author_frame']['runtime_heading_deg'],'altitude':0,'scale':1,
              'owner':{'macro_id':owner['macro_id'],'feature_local_id':target},'source_feature_ids':{'building':[owner['source_key'].split(':')[1]],'building_part':[]},
              'model_geometry_sha256':{k:v['sha256']for k,v in assets.items()},'bounds_glb':bounds,'replacement_geometry':mask_geo,'collision_geometry':mesh.wgs(collision),
              'source_section_caps':{'geometry':mapping(caps),'base_m':0,'roof_m':measured['far']['height_m'],'far_sha256':sha(args.macro/'far.glb'),'height_reference':[current['origin_longitude'],current['origin_latitude']]},
              'overviewBearing':342.5,'overviewPitch':32,'overviewZoom':19.25,'maxDistance':560,'lod_switch_in_m':580,'lod_switch_out_m':760,
              'placement':{'status':'estimated','note':'南缘按延安东路、具名轮廓和第三批3A005正面照配准。门篷、字体、石饰与窗格据照片比例估计。'},
              'navigation':{'listed':False,'status':'从延安东路看三座门篷、中央六组窗、馆牌和两端女儿墙。'},'partial_model':True,'model_scope':manifest['model_scope_zh']}
    for k in ('replacement_geometry','collision_geometry'):checked_geometry(contract[k],k,collision=k=='collision_geometry')
    check_source_section_caps(contract,exact)
    args.out.mkdir(exist_ok=True,parents=True);write(args.out/'final-placement-contract.json',contract)
    write(args.out/'placement-geometry.json',{'id':model,'source_sha256':sha(src),'geometry_check_sha256':sha(Path(__file__)),'manifest_sha256':sha(args.manifest),'contract_sha256':sha(args.out/'final-placement-contract.json'),'assets':assets,'near_group':group,'native_variants':measured,'cut_area_m2':mask.area,'model_area_m2':profile.area,'ground_area_m2':ground.area,'collision_area_m2':collision.area,'cap_length_m':edges['far'].length,'cap_near_far_gap_m':edges['near'].hausdorff_distance(edges['far']),'street_gap_m':roads,'ground_points':samples,'nearby':sorted(neighboring.items(),key=lambda p:p[1])[:10],'osm_fallback':{'tile_sha256':vector['sha256'],'examined_near_components':len(keys),'intersecting_component':source_component,'other_component_max_cut_m2':max(a for k,a in keys.items()if k!=source_component['key'])}})
    print('Near and far retained rear area',measured['near']['retained_rear_m2'],measured['far']['retained_rear_m2'],flush=True)
