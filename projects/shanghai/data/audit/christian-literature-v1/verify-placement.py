"""Check west street scope on a six-owner city tile with a shared 1930s party wall."""
from pathlib import Path
import argparse,sys,subprocess,runpy,numpy as np
import shapely as geo
from shapely.geometry import box,LineString,MultiLineString,Point
BASE=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(BASE/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry
ID='huangpu-christian-literature-building'
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);p.add_argument('--manifest',type=Path,default=BASE/'assets/models/candidates'/ID/'manifest.json');p.add_argument('--out',type=Path,default=Path(__file__).resolve().parent);a=p.parse_args();a.out.mkdir(exist_ok=True,parents=True)
 ref=BASE/'source/precise'/ID/'footprint-review.json';details=read(ref);ctx=PlacementMeshes(BASE,a.work,details);assets,bounds,mesh,feet=ctx.decode_model(a.manifest);grp=details['near_tiles'][0];ids=grp['feature_local_ids'];owner=3051;east=2954
 ctx.link('baseline-far.glb',ctx.files['far.glb']);ctx.link('baseline-near.glb.gz',ctx.files[Path(grp['file']).name]);ctx.link('macro-READY.json',ctx.files['READY.json'])
 write(a.work/'context-features.json',[{'localId':x}for x in ids]);subprocess.run(['node',ctx.decoders/'map-decode-source.mjs'],env=ctx.env,check=True,stdout=subprocess.DEVNULL)
 target=ctx.footprints[owner];end=2.87
 mask=target.buffer(.58,join_style=2).intersection(box(-10.55,-.65,10.55,end))
 assert mesh.difference(mask.buffer(.012)).area<.0005
 occupancy=geo.union_all([feet,box(-9.56,-.01,9.56,2.85)],grid_size=.001).simplify(.01,preserve_topology=True)
 # A shallow closed door can still have walkable pavement ahead of its leaf.
 # Measure all three serialized variants at waist height, including projecting hardware.
 first_hit=runpy.run_path(str(BASE/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['first_hit']
 depths={}
 for decoded in read(a.work/'delivered-decode.json'):
  tri=np.fromfile(decoded['triangle_file'],np.float64).reshape(-1,3,3)[:,:,[0,2,1]]*[1,-1,1]
  lo,hi=tri.min(1),tri.max(1);result={}
  for label,x in [('leaf',.035),('glass',.42),('handle',.13),('side',2.12)]:
   at=np.array([x,-3,1.15]);selector=(lo[:,0]<=x)&(hi[:,0]>=x)&(lo[:,2]<=1.15)&(hi[:,2]>=1.15)
   _,dist,_=first_hit(tri[selector],at,np.array([0.,1.,0.]));result[label]=round(float(dist)-3,4)
  depths[decoded['variant']]=result
 assert all(record==depths['raw']for record in depths.values())
 dep=depths['raw'];assert .54<dep['leaf']<.56 and .60<dep['side']<.62 and .45<dep['glass']<.48 and .36<dep['handle']<.39
 reveals=[box(-.83,-.20,.83,dep['leaf'])]
 details_front=[]
 for side in (-1,1):
  x=side*2.12;reveals.append(box(x-.35,-.2,x+.35,dep['side']))
  for label,cx,half in [('glass',side*.408,.315),('handle',side*.13,.017)]:
   details_front.append(box(cx-half,dep[label],cx+half,dep['leaf']+.01))
 occupancy=geo.union_all([occupancy.difference(geo.union_all(reveals)),*details_front],grid_size=.0005)
 counts={};surfaces={}
 for variant in ['far','near']:
  v=np.fromfile(a.work/f'baseline-{variant}-triangles.f64',np.float64).reshape(-1,3,3);v[:,:,:2]=v[:,:,:2]@ctx.axes.T
  if variant=='far':
   groups=np.fromfile(a.work/'baseline-far-owners.u32',np.uint32);certain=possible=(groups==owner);maybe_east=groups==east;ambiguous=np.zeros(len(v),dtype=bool)
  else:
   pt=geo.points(v.mean(1)[:,:2]);dist=np.stack([geo.distance(pt,ctx.footprints[i])for i in ids],axis=1)
   groups=np.array(ids)[np.argmin(dist,axis=1)];margin=np.sort(dist,axis=1);ambiguous=margin[:,1]-margin[:,0]<1.50;certain=(groups==owner)&~ambiguous
   possible=dist[:,ids.index(owner)]<=dist.min(1)+1.50;maybe_east=dist[:,ids.index(east)]<=dist.min(1)+1.50
  sure=ctx.project_faces(v[certain]);possible_owner=ctx.project_faces(v[possible]);known_east=ctx.project_faces(v[maybe_east]);amb=ctx.project_faces(v[ambiguous])if ambiguous.any()else None
  other=ctx.project_faces(v[~certain]);cut=sure.intersection(mask).area
  assert known_east.distance(mask)>14 and other.intersection(mask).area<.0005 and (amb is None or amb.distance(mask)>7)
  assert .08<cut/sure.area<.21
  surfaces[variant]=certain
  counts[variant]={'total_triangles':len(v),'certain_west_triangles':int(certain.sum()),'possible_west_triangles':int(possible.sum()),'ambiguous_party_wall_triangles':int(ambiguous.sum()),'eastern_half_possible_triangles':int(maybe_east.sum()),'certain_west_projected_m2':sure.area,'possible_west_projected_m2':possible_owner.area,'native_removed_m2':cut,'retained_fraction_interval':[1-cut/sure.area,1-cut/possible_owner.area],'possible_east_facade_mesh_clearance_m':known_east.distance(mesh),'possible_east_cut_clearance_m':known_east.distance(mask),'non_target_cut_m2':other.intersection(mask).area,'ambiguous_clearance_m':amb.distance(mask)if amb is not None else None,'actual_west_height':float(v[certain,:,2].max())}
  if variant=='far':far=sure
 neighbors={i:g.distance(mask)for i,g in ctx.footprints.items()if i!=owner and g.distance(mask)<35};assert min(neighbors.values())>3
 line=far.intersection(LineString([(-20,end),(20,end)]));assert line.geom_type=='LineString'and 18<line.length<21
 ready=read(ctx.files['READY.json']);sr=details['owner'];frame=details['author_frame'];doc=read(a.manifest)
 cap={'base_m':0,'roof_m':counts['far']['actual_west_height'],'height_reference':[ready['origin_longitude'],ready['origin_latitude']],'far_sha256':sha(ctx.files['far.glb']),'geometry':ctx.wgs(MultiLineString([line]))}
 witnesses=[]
 for label,x,y,expected in [('retained rear of west property',0,10,True),('open central door reveal',.035,.26,False),('closed double leaf',.035,.56,True),('in front of door pull',.13,.34,False),('bronze door pull',.13,.39,True),('in front of left side recess',-2.12,.45,False),('closed left side leaf',-2.12,.62,True),('in front of right side recess',2.12,.45,False),('closed right side leaf',2.12,.62,True),('fixed stone jamb',1.2,.15,True),('street pavement',.45,-2.1,False),('far side of street',0,-4.1,False),('unaffected east building',*ctx.footprints[east].representative_point().coords[0],True)]:
  probe=Point(x,y);hit=occupancy.covers(probe)or target.difference(mask).covers(probe)or any(g.covers(probe)for i,g in ctx.footprints.items()if i!=owner);assert hit==expected,(label,hit)
  witnesses.append({'label':label,'xy':[x,y],'point':ctx.to_wgs(np.array([[x,y]]))[0].tolist(),'expected':'building'if expected else None})
 c={'id':ID,**frame['anchor'],'heading':frame['runtime_heading_deg'],'scale':1,'altitude':0,'owner':{'macro_id':details['frozen_macro'],'feature_local_id':owner},'source_feature_ids':{'building':[sr['source_key'].split(':')[1]],'building_part':[]},'bounds_glb':bounds,'model_geometry_sha256':{k:v['sha256']for k,v in assets.items()},'replacement_geometry':ctx.wgs(mask),'collision_geometry':ctx.wgs(occupancy),'source_section_caps':cap,'overviewBearing':88,'overviewPitch':37,'overviewZoom':19.65,'maxDistance':550,'lod_switch_in_m':550,'lod_switch_out_m':700,'navigation':{'listed':False,'status':'广学大楼虎丘路立面，供俯瞰。'},'placement':{'status':'estimated','note':'取西楼3051临虎丘路的历史街面。与圆明园路真光楼2954的共同后侧边界均保留。'},'partial_model':True,'model_scope':doc['model_scope_zh']}
 for key in ['replacement_geometry','collision_geometry']:checked_geometry(c[key],key,collision=key=='collision_geometry')
 write(a.out/'final-placement-contract.json',c)
 write(a.out/'placement-geometry.json',{'id':ID,'script_sha256':sha(Path(__file__)),'reference_sha256':sha(ref),'manifest_sha256':sha(a.manifest),'model':assets,'native':counts,'cut_distances_other_vectors':neighbors,'native_seam_m':line.length,'original_source_area_m2':target.area,'retained_original_m2':target.difference(mask).area,'model_detail_projection_m2':mesh.area,'model_ground_projection_m2':feet.area,'ground_occupancy_m2':occupancy.area,'waist_high_depths_m':depths,'ground_probes':witnesses,'contract_sha256':sha(a.out/'final-placement-contract.json')})
 print(counts)
if __name__=='__main__':main()
