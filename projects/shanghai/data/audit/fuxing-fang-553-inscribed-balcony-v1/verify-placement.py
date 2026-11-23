"""Register the inscribed second-storey balcony using the underlying near and far geometry."""
import argparse,gzip,math,os,runpy,sys
from pathlib import Path
from contextlib import ExitStack
import numpy as np
import shapely as geo
from shapely.geometry import box,Point,LineString
P=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',str(Path(__file__).resolve().parents[3])));sys.path.insert(0,str(P/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
ID='huangpu-fuxing-fang-553-inscribed-balcony';OWNER=396
from shapely.geometry import shape
letters=read(Path(__file__).parents[1]/'author/source/painted-title.json') if (Path(__file__).parents[1]/'author/source/painted-title.json').is_file() else read(P/'source/precise'/ID/'source/painted-title.json')
ink=shape(letters['letters']['興'])
stable=max((ink.geoms if ink.geom_type=='MultiPolygon' else [ink]),key=lambda g:g.area).buffer(-.0048).representative_point()
T=[('red painted character', (stable.x,.0082,4.516+stable.y), ['red painted inscription']), ('left inset wing', (-1.035, 0.184, 4.58), ['recessed side panel']), ('right inset wing', (1.035, 0.184, 4.58), ['recessed side panel']), ('lower straight base', (0, -0.044, 4.048), ['light stone frame']), ('projecting top coping', (-0.28, -0.052, 4.972), ['light stone frame']), ('terracotta pier', (-0.72, 0.945, 6.487), ['red facing brick', 'weathered facing brick', 'brick mortar']), ('left wooden shutter', (-0.13, 0.99, 6.245), ['shutter blade', 'timber reveal']), ('shutter frame', (0.57, 0.973, 6.38), ['dark shutter timber'])]
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
 base=ground['raw'];assert base.is_empty and all(g.is_empty for g in ground.values());assert all(base.symmetric_difference(g).area<.002 for g in ground.values())
 owner={'macro_id':ref['frozen_macro'],'feature_local_id':OWNER};key=ref['owner']['source_key'].split(':',1)[1]
 bb=np.asarray(bounds)
 c=dict(id=ID,lng=s.lon,lat=s.lat,heading=ref['author_frame']['runtime_heading_deg'],scale=1,altitude=0,owner=owner,source_feature_ids=dict(building=[key],building_part=[]),replacement_geometry=None,collision_geometry=None,bounds_glb=dict(min=bb.min((0,1)).tolist(),max=bb.max((0,1)).tolist()),model_geometry_sha256={k:mf['assets'][a]['sha256']for k,a in [('raw','raw'),('web','full'),('lod','lod')]},overviewBearing=159.,overviewPitch=42,overviewZoom=21.6,maxDistance=540,lod_switch_in_m=300,lod_switch_out_m=395,navigation=dict(listed=False,status='从复兴中路面向553弄二层题名阳台。'),placement=dict(status='map-aligned',note='阳台位于原396及1118之间，其下净空及相邻两栋保留。'),model_scope=mf['scope'],partial_model=True)
 write(v.out/'final-placement-contract.json',c)
 with ExitStack()as st:
  for k in ('near','far'):
   for n in ('owners.u32','triangles.f64'):
    dest=v.work/('baseline-'+k+'-'+n);fd=os.memfd_create('fuxing341-'+n);st.callback(os.close,fd);dest.symlink_to(f'/proc/{os.getpid()}/fd/{fd}');st.callback(dest.unlink)
  decoded=s.decode_group(ref['near_tiles'][0],OWNER)
 originals={};oldstats={};bbwall=box(-1.273,-.061,1.273,1.152)
 for name,(own,other,assign) in decoded.items():
  ownfoot=s.project_faces(own);otherfoot=s.project_faces(other);margin=ownfoot.distance(bbwall)
  assert margin>1.8 and otherfoot.distance(bbwall)>1.8
  originals[name]=(own,other,ownfoot)
  oldstats[name]=dict(source_triangles=len(own),source_owner=OWNER,neighbor_triangles=len(other),margin_to_model_m=margin,nearest_neighbor_mesh_m=otherfoot.distance(bbwall),source_replacement=None,previous_collision_preserved=True,assignment=assign)
 checks=[]
 for x in [-2.7,-2.,-1.20,-.64,0,.73,1.22,2.,2.75]:
  for y in [-.58,.16,.58,.95,1.32]:
   pt=Point(x,y);oldfloor={k:g.covers(pt)for k,(_,_,g)in originals.items()};gg={k:g.covers(pt)for k,g in ground.items()};assert len(set(oldfloor.values()))==len(set(gg.values()))==1
   checks.append(dict(name=f'553弄过街楼下 {x:g},{y:g}',xy=[x,y],wgs84=s.to_wgs(np.asarray([[x,y]]))[0].tolist(),source_ground_occupied=oldfloor,model_obstacle=gg['raw'],expected_map='building'if gg['raw'] or any(oldfloor.values())else None))
 assert all(not z['model_obstacle']for z in checks);assert all(z['expected_map'] is None for z in checks if abs(z['xy'][0])<1.5)
 neighbors=[dict(owner=i,clearance_m=s.footprints[i].distance(bbwall)) for i in ref['selection']['checked_neighbors']];assert min(z['clearance_m'] for z in neighbors)>1.8
 write(v.out/'placement-geometry.json',dict(id=ID,passed=True,source_sha256=sha(v.source),manifest_sha256=sha(v.manifest),models=stats,source_variants=oldstats,neighbors=neighbors,ground_probes=checks,height_bands=[],limits='街面三折题名阳台最低托体在地面上方超过3.6米，通道地面与原396、1118等邻栋均保留。'))
 heights={r['localId']:r['height']for r in __import__('json').loads(gzip.decompress(s.files['feature-table.json.gz'].read_bytes()))['features']}
 volumes=[(i,geo.transform(g,lambda p:p@s.axes),heights[i])for i,g in s.footprints.items()if g.distance(Point(0,0))<130]
 probes=[(name,*map(float,np.asarray(pos[:2])@s.axes),pos[2])for name,pos,_ in T]
 rad=6371008.8*math.pi/180;views=[]
 candidates=[]
 for pitch in (42,38,44,33,29,24):
  for bearing in (160,164,154,170,148,178,142):
   c.update(overviewPitch=pitch,overviewBearing=bearing);views=[]
   for label,width,height,pad in cam['VIEWS']:
    view=cam['evaluate'](c,dict(width=width,height=height,insets=dict(zip(['left','right','top','bottom'],pad))),label,volumes,s.lon,s.lat,rad*math.cos(math.radians(s.lat)),rad,probes);views.append(view)
   candidates.append(dict(bearing=bearing,pitch=pitch,score=sum(k['clear_count']for k in views),views=views))
   if candidates[-1]['score']==len(T)*len(views):break
  if candidates[-1]['score']==len(T)*len(views):break
 selected=max(candidates,key=lambda z:z['score']);views=selected['views'];c.update(overviewBearing=selected['bearing'],overviewPitch=selected['pitch']);assert selected['score']==len(T)*len(views),[(a['bearing'],a['pitch'],a['score'])for a in candidates]
 write(v.out/'final-placement-contract.json',c)
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
     allowed=[]
     cities.append(dict(role=role,view=view['view'],feature=name,lod=lod,owner_hits=len(aa),removed_by_model=0,neighbors=len(xx),passed=len(aa)==len(allowed)and len(xx)==0))
 write(v.out/'model-sightlines.json',dict(passed=all(r['passed']for r in rows),targets=rows));write(v.out/'original-city-sightlines.json',dict(passed=all(r['passed']for r in cities),checks=cities))
 missing=[(r['view'],r['feature'],r['material'],r['endpoint'])for r in rows if r['role']=='raw'and not r['passed']]
 print('actual mesh views',missing,'source exceptions',[z for z in cities if not z['passed']][:4],flush=True)
 assert all(r['passed']for r in rows+cities)
if __name__=='__main__':main()
