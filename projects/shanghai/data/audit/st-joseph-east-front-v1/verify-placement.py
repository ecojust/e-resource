"""Check the east facade against the real 15-feature city tile, keeping the nave and court independent."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import numpy as np
import shapely as geo
from shapely.geometry import LineString, MultiLineString, Point, box

AUDIT=Path(__file__).resolve().parent
PROJECT=AUDIT.parents[2]
ID='huangpu-st-joseph-church-east-front'
OWNER=2923
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes, read, sha, write
from build_candidate_city_integrations import checked_geometry


def owner_meshes(layout,src):
    """Resolve the near tile geometrically; its exported per-triangle IDs are all zero."""
    group=src['near_tiles'][0];ids=group['feature_local_ids'];work=layout.work
    for name,f in [('baseline-far.glb','far.glb'),('baseline-near.glb.gz',Path(group['file']).name),('macro-READY.json','READY.json')]:layout.link(name,layout.files[f])
    write(work/'context-features.json',[{'localId':i} for i in ids]);script=layout.decoders/'map-decode-source.mjs'
    subprocess.run(['node',script],env=layout.env,check=True,stdout=subprocess.DEVNULL)
    results={}
    for role in ['near','far']:
        tri=np.fromfile(work/f'baseline-{role}-triangles.f64',np.float64).reshape(-1,3,3)
        tri[:,:,:2]=tri[:,:,:2]@layout.axes.T
        original=np.fromfile(work/f'baseline-{role}-owners.u32',np.uint32)
        if role=='far':
            chosen=original;method={'method':'per-vertex _FEATURE_ID_0'}
        else:
            assert set(original)=={0}
            centers=geo.points(tri[:,:,:2].mean(axis=1))
            dist=np.stack([geo.distance(centers,layout.footprints[i]) for i in ids],axis=1)
            chosen=np.asarray(ids)[np.argmin(dist,axis=1)];oi=ids.index(OWNER);own=chosen==OWNER
            r=dist[:,oi];other=np.min(np.delete(dist,oi,axis=1),axis=1)
            named_gap=min(layout.footprints[OWNER].distance(layout.footprints[i]) for i in ids if i!=OWNER)
            own_error=float(max(r[own]));own_lead=float(min((other-r)[own]));outside_lead=float(min((r-other)[~own]))
            # 1301 is only 1.25 metres away. Both sides must stay much farther apart than the decoder's observed centroid error.
            assert own_error<.12 and min(own_lead,outside_lead)>.85*named_gap and min(own_lead,outside_lead)>8*own_error
            method={'method':'nearest frozen group footprint, independent control on both sides of the 2923 boundary','largest_owner_centroid_error_m':own_error,'minimum_named_group_gap_m':named_gap,'minimum_lead_for_owner_m':own_lead,'minimum_lead_for_all_other_owners_m':outside_lead,'decoder_sha256':sha(script)}
        assert set(chosen)==set(ids)
        results[role]=(tri[chosen==OWNER],tri[chosen!=OWNER],method)
    return results


def run(args,work):
    src=read(PROJECT/'source/precise'/ID/'footprint-review.json');ready=read(args.macro/'READY.json')
    for b in src['frozen_bindings']:
        rel=b['repository_path'].split(src['frozen_macro']+'/')[1];f=args.macro/rel
        assert sha(f)==b['sha256'] and f.stat().st_size==b['bytes'];shutil.copy2(f,work/f.name)
    layout=PlacementMeshes(PROJECT,work,src);assets,bounds,model,ground=layout.decode_model(args.manifest)
    parts=owner_meshes(layout,src);end=6.11;cut=box(-11.72,-.57,11.72,end)
    assert model.difference(cut).area<.001 and ground.is_valid
    collision=ground
    profiles={};evidence={}
    for role,(mine,others,method)in parts.items():
        proj=layout.project_faces(mine);profiles[role]=proj
        neighbor=layout.project_faces(others);keep=proj.difference(cut)
        assert neighbor.intersection(cut).area<.001 and .76<keep.area/proj.area<.86
        evidence[role]={'owner_triangles':len(mine),'other_triangles':len(others),'owner_height_m':float(mine[:,:,2].max()),'footprint_m2':proj.area,'retained_m2':keep.area,'retained_fraction':keep.area/proj.area,'neighbor_clip_overlap_m2':neighbor.intersection(cut).area,'neighbor_distance_m':neighbor.distance(cut),'owner_assignment':method}
    nearby={i:{'ground_clearance_m':g.distance(collision),'clip_clearance_m':g.distance(cut),'clip_overlap_m2':g.intersection(cut).area} for i,g in layout.footprints.items() if i!=OWNER and g.distance(cut)<25}
    assert all(r['clip_overlap_m2']<.001 and r['ground_clearance_m']>.03 for r in nearby.values())
    slice_line=LineString([(-20,end),(20,end)])
    seam=profiles['far'].intersection(slice_line);near_seam=profiles['near'].intersection(slice_line)
    assert seam.geom_type=='LineString' and near_seam.geom_type in ('LineString','MultiLineString') and 21<seam.length<24
    near_parts=list(near_seam.geoms) if near_seam.geom_type=='MultiLineString' else [near_seam]
    assert seam.difference(near_seam.buffer(.005)).length<.005
    seam_mismatch=seam.hausdorff_distance(near_seam);assert seam_mismatch<.20
    for role,line_section in [('near',near_seam),('far',seam)]:
        parts_at_cut=near_parts if role=='near' else [line_section]
        evidence[role]['cut_line_segments_local_m']=[[list(pt)for pt in segment.coords]for segment in parts_at_cut]
        evidence[role]['cut_length_m']=line_section.length
    line=MultiLineString([seam]);h=evidence['far']['owner_height_m'];assert abs(evidence['near']['owner_height_m']-h)<.6
    cap={'base_m':0,'roof_m':h,'height_reference':[ready['origin_longitude'],ready['origin_latitude']],'far_sha256':ready['far']['sha256'],'geometry':layout.wgs(line)}
    probes=[]
    def check(label,x,y,source,collides,clipped):
        q=Point(x,y);pt=layout.to_wgs(np.asarray([[x,y]]))[0];assert collision.covers(q)==collides and cut.covers(q)==clipped,(label,x,y,collides,clipped)
        if source is not None:assert layout.footprints[source].covers(q)
        probes.append({'name':label,'xy':[x,y],'position':pt.tolist(),'expected':'building' if source is not None or collides else None,'modelObstacle':collides,'cut':clipped,'original_source_id':source})
    for i,x in enumerate([-7.36,0,7.36]):
        check('closed entrance '+str(i+1),x,1.20,OWNER,True,True);check('court before door '+str(i+1),x,-1.05,None,False,False)
    check('west nave',0,16,OWNER,False,False);check('far part of nave',0,36,OWNER,False,False);check('preserved edge behind model',0,7,OWNER,False,False)
    for i in [1301,2730,1990,1107,131]:
        q=layout.footprints[i].representative_point();check('neighbour '+str(i),q.x,q.y,i,False,False)
    frame=src['author_frame'];manifest=read(args.manifest);contract={'id':ID,**frame['anchor'],'heading':frame['runtime_heading_deg'],'scale':1,'altitude':0,'owner':{'macro_id':src['frozen_macro'],'feature_local_id':OWNER},'source_feature_ids':{'building':[src['owner']['source_key'].split(':')[1]],'building_part':[]},'model_geometry_sha256':{k:v['sha256']for k,v in assets.items()},'bounds_glb':bounds,'replacement_geometry':layout.wgs(cut),'collision_geometry':layout.wgs(collision),'source_section_caps':cap,'overviewBearing':args.bearing,'overviewPitch':args.pitch,'overviewZoom':19.4,'maxDistance':510,'lod_switch_in_m':550,'lod_switch_out_m':700,'navigation':{'listed':False,'status':'四川南路36号院内东立面与钟塔局部，供俯瞰。'},'placement':{'status':'estimated','note':'2009至2017年实照东立面取具名源2923院侧约6米。后方堂身、紧邻校舍以及原院内场地保持原图。源楼高6.4米，钟塔高约36.5米为照片估算。'},'partial_model':True,'model_scope':manifest['model_scope_zh']}
    for k in ['collision_geometry','replacement_geometry']:checked_geometry(json.loads(json.dumps(contract[k])),k,collision=k=='collision_geometry')
    args.out.mkdir(exist_ok=True,parents=True);write(args.out/'final-placement-contract.json',contract)
    write(args.out/'footprint-review.json',{'id':ID,'frozen_source_bindings':src['frozen_bindings'],'assets':assets,'bounds_glb':bounds,'model_projection_m2':model.area,'ground_collision_m2':ground.area,'source_variants':evidence,'other_owners':nearby,'seam_m':seam.length,'near_far_seam_hausdorff_m':seam_mismatch,'ground_checks':probes,'contract_sha256':sha(args.out/'final-placement-contract.json')});print(evidence,len(probes),seam.length)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--macro',type=Path,required=True);parser.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/ID/'manifest.json');parser.add_argument('--out',type=Path,default=AUDIT);parser.add_argument('--bearing',type=float,required=True);parser.add_argument('--pitch',type=float,required=True)
    args=parser.parse_args()
    with tempfile.TemporaryDirectory() as scratch:run(args,Path(scratch))
