"""Measure a height-scoped display cut, retained ground and source-specific visibility on the two original meshes."""
from pathlib import Path
from contextlib import ExitStack
import argparse,gzip,json,hashlib,math,os,runpy,sys
import numpy as np
import shapely as geo
from shapely.geometry import Point,box,LineString,shape
HERE=Path(__file__).resolve().parent
PROJECT=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',HERE.parents[2]))
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
ID='huangpu-cathay-apartments-east-window-bay'
OWNER=4093
MARKS=[
 ('lower stone jamb',(-2.101,-.115,6.67),['buff stone','stone shadow']),
 ('second-storey middle light',(-.97,.111,6.31),['grey glass','smoke blue glass','muted green glass']),
 ('second-storey stone sill',(1.02,-.205,5.747),['stone lip']),
 ('third-storey mullion',(.42,-.128,10.26),['buff stone']),
 ('third-storey last light',(.93,.11,10.32),['grey glass','smoke blue glass','muted green glass']),
 ('projecting horizontal band',(-.95,-.488,9.085),['painted rack']),
 ('fourth-storey stone head',(.78,-.14,14.81),['buff stone']),
 ('fourth-storey green glazing',(.92,.110,13.31),['grey glass','smoke blue glass','muted green glass']),
 ('fourth-storey rail',(0.,-.487,12.695),['painted rack']),
 ('extended corner quoin',(2.51,-.0645,9.932),['buff stone']),
 ('exposed running bond',(1.84,0,8.48),['brown facing brick']),
 ('drip and cornice',(1.,-.530,16.),['grey eave trim'])]
def main():
 ap=argparse.ArgumentParser()
 for n in ['manifest','source','work','out']:ap.add_argument('--'+n,type=Path,required=True)
 a=ap.parse_args();a.out.mkdir(exist_ok=True,parents=True);s=PlacementMeshes(PROJECT,a.work,read(a.source));ref=read(a.source);mf=read(a.manifest);assert mf['id']==ID
 R=runpy.run_path(str(PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))
 cross=runpy.run_path(str(PROJECT/'data/audit/daxin-tobacco-northeast-tower-v1/check-physical-city-rays.py'))['crossings']
 cam=runpy.run_path(str(PROJECT/'data/audit/pure-heart-church-v1/check-overview-sightlines.py'))
 cut=box(-2.75,-.185,2.805,.91);owner={'macro_id':ref['frozen_macro'],'feature_local_id':OWNER}
 owned_ref=next(x for x in ref['owners']if x['local_id']==OWNER)
 mesh={};bounds=[];models={}
 for role,file in [('raw','raw.glb'),('full','decoded-full.glb'),('lod','decoded-lod.glb')]:
  tri,mi,names,doc=R['load_triangles'](a.manifest.parent/file)
  if role=='raw':assert doc['sha256']==mf['assets']['raw']['sha256']
  assert len(tri)==mf['assets'][role]['triangles']and tri[:,:,2].min()>5.48
  lo,hi=tri.min((0,1)),tri.max((0,1));bounds.append([lo[[0,2,1]]*[1,1,-1],hi[[0,2,1]]*[1,1,-1]])
  models[role]=(tri,mi,names);obs=s.ground_faces(tri);assert obs.is_empty
  mesh[role]=dict(file_sha256=doc['sha256'],source_asset=mf['assets'][role]['sha256'],min_z=float(tri[:,:,2].min()),max_z=float(tri[:,:,2].max()),ground_area=obs.area,triangles=len(tri))
 bbox=np.array(bounds);mins, maxs=bbox.min((0,1)),bbox.max((0,1))
 pr=ref['owner'];heading=ref['author_frame']['runtime_heading_deg'];source=[pr['source_key'].split(':',1)[1]]
 contract=dict(id=ID,lng=s.lon,lat=s.lat,heading=heading,scale=1,altitude=0,owner=owner,source_feature_ids=dict(building=source,building_part=[]),replacement_geometry=None,collision_geometry=None,display_height_clips=[dict(id=ID+'-upper-window-face',owner=owner,geometry=s.wgs(cut),min_height=5.55,max_height=16.42,height_reference=[s.lon,s.lat])],bounds_glb=dict(min=mins.tolist(),max=maxs.tolist()),model_geometry_sha256={k:mf['assets'][role]['sha256']for k,role in [('raw','raw'),('web','full'),('lod','lod')]},overviewBearing=327.,overviewPitch=59.,overviewZoom=20.6,maxDistance=720,lod_switch_in_m=520,lod_switch_out_m=675,navigation=dict(listed=False,status='从淮海中路看东端四联直窗、石角和砖檐。'),placement=dict(status='map-aligned',note='仅对4093南楼东端的窗口做有高度的显示裁切。旧底商、原屋有向地面碰撞与整条院路保持原状。'),model_scope=mf['scope'],partial_model=True)
 write(a.out/'final-placement-contract.json',contract)
 with ExitStack()as hold:
  for lod in ('near','far'):
   for ext in ('owners.u32','triangles.f64'):
    f=a.work/f'baseline-{lod}-{ext}';fd=os.memfd_create('cathay-city-'+ext);hold.callback(os.close,fd);f.symlink_to(f'/proc/{os.getpid()}/fd/{fd}');hold.callback(f.unlink)
  decoded=s.decode_group(ref['near_tiles'][0],OWNER)
 owners={};original={}
 for role,(own,other,method)in decoded.items():
  planar=s.project_faces(own);world=geo.polygons(own[:,:,:2]);z=own[:,:,2];changed=geo.intersects(world,cut)&(z.max(axis=1)>5.55)&(z.min(axis=1)<16.42)
  assert changed.any() and changed.sum()<len(own) and 12.75<z.max()<12.85
  area=planar.intersection(cut).area;assert 2<area<7
  other_projection=s.project_faces(other);assert other_projection.distance(cut)>10.
  owners[role]=dict(source_triangles=len(own),affected_render_triangles=int(changed.sum()),source_area_m2=planar.area,upper_mask_intersection_m2=area,retained_at_ground_m2=planar.area,unchanged_neighbor_triangles=len(other),other_clearance_m=other_projection.distance(cut),original_top_m=float(z.max()),assignment=method)
  original[role]=(own,other,planar)
 print('source sections',[(k,v['affected_render_triangles'],v['upper_mask_intersection_m2'])for k,v in owners.items()],flush=True)
 neighbors=[dict(owner=i,clearance_to_cut_m=s.footprints[i].distance(cut),ground_unchanged=True)for i in ref['selection']['checked_neighbors']];assert min(v['clearance_to_cut_m']for v in neighbors)>3.
 centers=[('street pavement',x,-1.6,False)for x in (-4,-2.7,-1,0,1,2.6,4)]+[('underlying ground-floor shop',x,.5,True)for x in (-3,-1.6,0,1.6,2.40)]+[('passage into courtyard',3.7,y,False)for y in (-.5,.5,1.5,2.5,4.,6.,8.)]+[('southern block interior',x,2.,True)for x in (-11.,-6.,-3.,-1.,.7,2.10)]
 trials=[]
 for label,x,y,want in centers:
  pt=Point(x,y)
  checks={role:grid.covers(pt)for role,(_,_,grid)in original.items()};assert all(h==want for h in checks.values()),(label,x,y,checks)
  trials.append(dict(name=label,xy=[x,y],wgs84=s.to_wgs(np.array([[x,y]]))[0].tolist(),source_ground_occupied=checks,model_obstacle=False,source_cut=False,expected_map='building'if want else None))
 write(a.out/'placement-geometry.json',dict(id=ID,passed=True,source_sha256=sha(a.source),manifest_sha256=sha(a.manifest),height_clip_m=[5.55,16.42],contract_sha256=sha(a.out/'final-placement-contract.json'),models=mesh,source_variants=owners,neighbors=neighbors,ground_probes=trials))
 heights={v['localId']:v['height']for v in json.loads(gzip.decompress(s.files['feature-table.json.gz'].read_bytes()))['features']}
 def en(g):return geo.transform(g,lambda xy:xy@s.axes)
 volumes=[(i,en(g.difference(cut) if i==OWNER else g),heights[i])for i,g in s.footprints.items()if g.distance(Point(0,0))<130]
 pts=[(name,*map(float,np.asarray(pos[:2])@s.axes),pos[2])for name,pos,_ in MARKS]
 rad=math.pi/180*6371008.8;answer=[]
 for label,w,h,pad in cam['VIEWS']:
  ans=cam['evaluate'](contract,dict(width=w,height=h,insets=dict(zip(['left','right','top','bottom'],pad))),label,volumes,s.lon,s.lat,rad*math.cos(math.radians(s.lat)),rad,pts);answer.append(ans)
 write(a.out/'overview-sightlines.json',dict(views=answer,contract_sha256=sha(a.out/'final-placement-contract.json'),camera_sha256=sha(PROJECT/'src/candidate-overview-camera.js')))
 print('camera',[(v['view'],v['clear_count'],[(p['feature'],p['obstructions'])for p in v['probes']if not p['clear']])for v in answer],flush=True)
 assert all(v['clear_count']==len(MARKS)for v in answer)
 rows=[];city=[]
 for role,(tri,mi,names)in models.items():
  for v in answer:
   e,n,z=v['camera_enu'];eye=np.r_[np.array([e,n])@s.axes.T,z]
   for label,pos,mats in MARKS:
    pos=np.array(pos);vec=pos-eye;idx,dist,end=R['first_hit'](tri,eye,vec)
    hit=names[mi[idx]] if np.isfinite(dist)else None
    assert hit in mats and np.linalg.norm(end-pos)<.12,(role,v['view'],label,hit,np.round(end,3))
    rows.append(dict(role=role,view=v['view'],feature=label,first_material=hit,distance=float(dist),local_endpoint=end.round(5).tolist()))
    for vr,(own,other,_)in original.items():
     _,aa=cross(eye,end,own);_,bb=cross(eye,end,other);allowed=[q for q in aa if 5.55-.002<=q[2]<=16.42+.002 and cut.buffer(.0004).covers(Point(q[:2]))]
     assert len(aa)==len(allowed)and not len(bb),(vr,v['view'],label,len(aa),len(allowed),len(bb))
     city.append(dict(role=role,view=v['view'],feature=label,source_lod=vr,source_intersections=len(aa),clipped_above_shop=len(allowed),other_blockers=len(bb)))
 write(a.out/'model-sightlines.json',dict(passed=True,targets=rows));write(a.out/'original-city-sightlines.json',dict(passed=True,checks=city))
 print('sightlines',len(rows),len(city),flush=True)
if __name__=='__main__':main()
