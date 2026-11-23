"""Survey the baseline wall, the four-metre entrance and the closed street gate in metres."""
import argparse,gzip,math,os,runpy,sys
from pathlib import Path
from contextlib import ExitStack
import numpy as np
import shapely as geo
from shapely.geometry import box,Point,LineString
P=Path(os.environ.get('SHANGHAI_PROJECT_ROOT') or next(p for p in Path(__file__).resolve().parents if (p/'tools/package_architectural_model.py').is_file()));sys.path.insert(0,str(P/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
ID='huangpu-park-terrace-nanchang-124-portal';OWNER=3695
T=[('arch crown moulding',(0.,-.059,3.989),['cream moulding']),('western arch moulding',(-.591,-.047,3.59),['cream moulding']),('eastern arch moulding',(.60,-.047,3.57),['cream moulding']),('left stone jamb',(-.757,-.046,2.99),['cream moulding']),('inner transom pane',(.13,.325,2.818),['shadowed window']),('numbered pier green plaque',(1.89,-1.168,1.683),['enamel green','enamel white']),('closed street gate',(.68,-.787,1.60),['painted iron','worn iron edge']),('west projecting pier cornice',(-.35,-.987,2.287),['stone relief','cream moulding'])]
def main():
 a=argparse.ArgumentParser()
 for n in ['manifest','source','work','out']:a.add_argument('--'+n,type=Path,required=True)
 v=a.parse_args();v.out.mkdir(parents=True,exist_ok=True);ref=read(v.source);mf=read(v.manifest);s=PlacementMeshes(P,v.work,ref);assert mf['id']==ID
 R=runpy.run_path(str(P/'data/audit/postal-office-v1/independent-glb-review-helpers.py'));cam=runpy.run_path(str(P/'data/audit/pure-heart-church-v1/check-overview-sightlines.py'))
 crossings=runpy.run_path(str(P/'data/audit/daxin-tobacco-northeast-tower-v1/check-physical-city-rays.py'))['crossings']
 models={};ground={};bounds=[];stats={}
 for role,name in [('raw','raw.glb'),('full','decoded-full.glb'),('lod','decoded-lod.glb')]:
  tri,mi,names,doc=R['load_triangles'](v.manifest.parent/name);assert len(tri)==mf['assets'][role]['triangles']
  xyz=tri.reshape(-1,3);lo,hi=xyz.min(0),xyz.max(0);bounds.append([lo[[0,2,1]]*[1,1,-1],hi[[0,2,1]]*[1,1,-1]])
  models[role]=(tri,mi,names);ground[role]=s.ground_faces(tri);stats[role]=dict(input_sha256=doc['sha256'],ground_face_area=ground[role].area,triangles=len(tri))
 base=ground['raw'];assert all(base.symmetric_difference(g).area<.002 for g in ground.values())
 # Each rectangular height band stays inside the recessed door opening even at its narrow top.
 sections=[(.04,3.28,.59),(3.28,3.48,.558),(3.48,3.64,.475),(3.64,3.74,.38),(3.74,3.81,.273),(3.81,3.855,.153),(3.855,3.872,.085)]
 patches=[(lo,hi,box(-hw,.027,hw,.437)) for lo,hi,hw in sections]
 owner={'macro_id':ref['frozen_macro'],'feature_local_id':OWNER};key=ref['owner']['source_key'].split(':',1)[1]
 bb=np.asarray(bounds)
 c=dict(id=ID,lng=s.lon,lat=s.lat,heading=ref['author_frame']['runtime_heading_deg'],scale=1,altitude=0,owner=owner,source_feature_ids=dict(building=[key],building_part=[]),replacement_geometry=None,collision_geometry=s.wgs(base.simplify(.0002,preserve_topology=True)),display_height_clips=[dict(id=ID+'-recess-'+str(i+1),owner=owner,geometry=s.wgs(p),min_height=lo,max_height=hi,height_reference=[s.lon,s.lat])for i,(lo,hi,p)in enumerate(patches)],bounds_glb=dict(min=bb.min((0,1)).tolist(),max=bb.max((0,1)).tolist()),model_geometry_sha256={k:mf['assets'][a]['sha256']for k,a in [('raw','raw'),('web','full'),('lod','lod')]},overviewBearing=335.4,overviewPitch=48,overviewZoom=21.4,maxDistance=540,lod_switch_in_m=300,lod_switch_out_m=395,navigation=dict(listed=False,status='街外观察南昌路124号半圆门券与门牌。'),placement=dict(status='map-aligned',note='只在124号内门洞范围分高度剔除原粗墙；上层、隔壁门户和110弄保留。闭合街门、两街柱及原有主墙有各自实测占地。'),model_scope=mf['scope'],partial_model=True)
 write(v.out/'final-placement-contract.json',c)
 with ExitStack()as st:
  for k in ('near','far'):
   for n in ('owners.u32','triangles.f64'):
    dest=v.work/('baseline-'+k+'-'+n);fd=os.memfd_create('nanchang333-'+n);st.callback(os.close,fd);dest.symlink_to(f'/proc/{os.getpid()}/fd/{fd}');st.callback(dest.unlink)
  decoded=s.decode_group(ref['near_tiles'][0],OWNER)
 originals={};oldstats={};cut=patches[0][2]
 for k,(own,other,assignment) in decoded.items():
  poly=s.project_faces(own);margin=s.project_faces(other).distance(cut);assert margin>12 and poly.intersection(cut).area>.13
  original_overlap=poly.intersection(cut).area;ground_source=poly.area;assert ground_source>800 and original_overlap<1
  region=geo.polygons(own[:,:,:2]);z=own[:,:,2];idx=np.logical_or.reduce([geo.intersects(region,p)&(z.max(1)>lo)&(z.min(1)<hi)for lo,hi,p in patches]);assert idx.any() and idx.sum()<len(idx)
  oldstats[k]=dict(previous_triangles=len(own),triangles_intersecting_recess=int(idx.sum()),neighbor_triangles_unchanged=len(other),nearest_neighbor_mesh_m=margin,original_wall_area_m2=ground_source,first_band_plan_area_m2=original_overlap,original_wall_collision_untouched=True,assignment=assignment)
  originals[k]=(own,other,poly)
 checks=[]
 for x in [-1.5,-.79,-.35,.2,.9,1.79,2.45]:
  for y in [-1.55,-.91,-.72,-.20,.55]:
   pt=Point(x,y);source={k:poly.covers(pt)for k,(_,_,poly)in originals.items()};model={k:g.covers(pt)for k,g in ground.items()};assert len(set(model.values()))==1 and len(set(source.values()))==1
   checks.append(dict(name=f'124门及相邻路面 {x:g},{y:g}',xy=[x,y],wgs84=s.to_wgs(np.asarray([[x,y]]))[0].tolist(),source_ground_occupied=source,model_obstacle=model['raw'],expected_map='building'if any([*source.values(),model['raw']])else None))
 assert all(not z['expected_map'] for z in checks if z['xy'][1]==-1.55)
 neighbors=[dict(owner=i,clearance_m=s.footprints[i].distance(cut))for i in ref['selection']['checked_neighbors']];assert min(r['clearance_m']for r in neighbors)>12
 write(v.out/'placement-geometry.json',dict(id=ID,passed=True,source_sha256=sha(v.source),manifest_sha256=sha(v.manifest),contract_sha256=sha(v.out/'final-placement-contract.json'),models=stats,source_variants=oldstats,neighbors=neighbors,ground_probes=checks,height_bands=sections,limits='原体近档15,590面与远档20面分别接受高度带。124近街铁门按实照闭合，门后至整排屋的原有碰撞保留。'))
 heights={r['localId']:r['height']for r in __import__('json').loads(gzip.decompress(s.files['feature-table.json.gz'].read_bytes()))['features']}
 # The original broad-phase footprint is tested without the doorway; 3-D tests below restore each wall outside its exact height band.
 volumes=[(i,geo.transform(g.difference(cut) if i==OWNER else g,lambda p:p@s.axes),heights[i])for i,g in s.footprints.items()if g.distance(Point(0,0))<130]
 probes=[(name,*map(float,np.asarray(pos[:2])@s.axes),pos[2])for name,pos,_ in T]
 rad=6371008.8*math.pi/180;views=[]
 for label,width,height,pad in cam['VIEWS']:
  view=cam['evaluate'](c,dict(width=width,height=height,insets=dict(zip(['left','right','top','bottom'],pad))),label,volumes,s.lon,s.lat,rad*math.cos(math.radians(s.lat)),rad,probes);views.append(view)
 write(v.out/'overview-sightlines.json',dict(views=views,contract_sha256=sha(v.out/'final-placement-contract.json'),camera_sha256=sha(P/'src/candidate-overview-camera.js')))
 rows=[];cities=[]
 for role,(tri,mi,names)in models.items():
  for view in views:
   e,n,z=view['camera_enu'];eye=np.r_[np.array([e,n])@s.axes.T,z]
   for name,pos,mats in T:
    vpos=np.asarray(pos);i,dist,end=R['first_hit'](tri,eye,vpos-eye);material=names[mi[i]] if np.isfinite(dist)else None
    accepted=material in mats and np.linalg.norm(end-vpos)<.10
    rows.append(dict(role=role,view=view['view'],feature=name,material=material,endpoint=end.round(4).tolist()if np.isfinite(dist)else None,passed=bool(accepted)))
    if not np.isfinite(dist):continue
    for lod,(own,other,_)in originals.items():
     _,aa=crossings(eye,end,own);_,xx=crossings(eye,end,other)
     allowed=[pt for pt in aa if any(l-.002<=pt[2]<=h+.002 and p.buffer(.0004).covers(Point(pt[:2]))for l,h,p in patches)]
     cities.append(dict(role=role,view=view['view'],feature=name,lod=lod,owner_hits=len(aa),removed_inside_124=len(allowed),neighbors=len(xx),passed=len(aa)==len(allowed)and len(xx)==0))
 write(v.out/'model-sightlines.json',dict(passed=all(r['passed']for r in rows),targets=rows));write(v.out/'original-city-sightlines.json',dict(passed=all(r['passed']for r in cities),checks=cities))
 missing=[(r['view'],r['feature'],r['material'],r['endpoint'])for r in rows if r['role']=='raw'and not r['passed']]
 print('actual mesh views',missing,'source exceptions',[z for z in cities if not z['passed']][:4],flush=True)
 assert all(r['passed']for r in rows+cities)
if __name__=='__main__':main()
