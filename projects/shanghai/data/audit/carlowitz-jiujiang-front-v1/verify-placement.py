"""Verify the real packed arcades and construct the smallest collision/clip footprint compatible with the visible street wall."""
from pathlib import Path
from hashlib import sha256
import argparse,os,tempfile,json,sys
import numpy as np
import shapely as geo
from shapely.geometry import Point,LineString,Polygon,MultiLineString,box,shape,mapping
from shapely.ops import polygonize
p=Path(__file__).resolve().parents[3];a=Path(__file__).resolve().parent
model='huangpu-carlowitz-jiujiang-front'
sys.path.insert(0,str(p/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry,check_source_section_caps

def wall_section(tr,height):
    z=tr[:,:,2];crossings=tr[(z.min(1)<height)&(z.max(1)>height)];lines=[]
    for tri in crossings:
        pts=[]
        for start,end in zip(tri,np.roll(tri,-1,axis=0)):
            if (start[2]<height)!=(end[2]<height):
                t=(height-start[2])/(end[2]-start[2]);pts.append(start[:2]+t*(end[:2]-start[:2]))
        if len(pts)==2 and np.linalg.norm(pts[0]-pts[1])>.00001:lines.append(LineString(np.round(pts,4)))
    return geo.union_all(list(polygonize(geo.union_all(lines,grid_size=.001))))

arg=argparse.ArgumentParser();arg.add_argument('--macro',type=Path,required=True);arg.add_argument('--manifest',type=Path,default=p/'assets/models/candidates'/model/'manifest.json');arg.add_argument('--previous-source-cut',type=Path,default=a/'preliminary-source-cut.json');arg.add_argument('--out',type=Path,default=a);args=arg.parse_args();args.out.mkdir(exist_ok=True,parents=True)
r=read(p/'source/precise'/model/'footprint-review.json');m=read(args.manifest);cut=read(args.previous_source_cut);assert m['id']==r['id']==cut['id']==model
assert sha(p/'source/precise'/model/'footprint-review.json')==cut['source_metadata_sha256']
with tempfile.TemporaryDirectory()as tmp:
 work=Path(tmp)
 for b in r['frozen_bindings']:
  rel=b['repository_path'].split(r['frozen_macro']+'/',1)[1];file=args.macro/rel;assert sha(file)==b['sha256'];(work/file.name).symlink_to(file.resolve())
 mesh=PlacementMeshes(p,work,r);assets,bounds,profile,all_low=mesh.decode_model(args.manifest);mask=Polygon(cut['cut_ring'])
 assert mask.covers(profile),(mask.difference(profile).area,profile.difference(mask).area)
 layers=[]
 for asset in read(work/'delivered-decode.json'):
  tris=np.fromfile(asset['triangle_file'],np.float64).reshape(-1,3,3);local=tris[:,:,[0,2,1]]*[1,-1,1]
  layers.extend(wall_section(local,h) for h in (.78,1.67))
 # Only the area behind the recessed shopfront is closed throughout. South of the
 # glass, use the measured body-height section of the jambs and return piers.
 inner=box(-22.65,2.22,25.1,4.9)
 closed=all_low.intersection(inner);ground=geo.union_all([closed,*layers],grid_size=.001)
 collision=ground.buffer(.018,join_style='mitre').simplify(.018,preserve_topology=True)
 assert ground.difference(collision).area<.015
 b=44.5552/14;left=-44.5552/2;grid=[]
 for i in range(14):
  centre=left+(i+.5)*b
  grid.append((f'opening {i+1} centre at street line',centre,0.,False,True,False))
  grid.append((f'passage {i+1} behind pier line',centre,1.15,False,True,False))
  grid.append((f'shop {i+1} interior behind glazing',centre,3.5,True,True,False))
  grid.append((f'closed facade pier {i+1}',left+(i+.06)*b,.20,True,True,False))
 for row in [('west pavement',left-1.67,.82,False,False,False),('south sidewalk',0.,-1.75,False,False,False),('rounded opening at intersection',23.92,.95,False,True,False),('north wall of the retained part',0.,7.55,False,False,True)]:
  grid.append(row)
 for name,x,y,solid,under,is_old in grid:
  pt=Point(x,y)
  assert collision.covers(pt)==solid,(name,'collision',solid,collision.distance(pt))
  assert under==mask.covers(pt),(name,'cut')
  assert is_old==(mesh.footprints[2965].covers(pt)and not mask.covers(pt)),(name,'retained')
 probes=[dict(label=t,xy=[x,y],position=mesh.to_wgs(np.array([[x,y]]))[0].tolist(),model_collision=blocked,under_mask=scoped,retained_source=old)for t,x,y,blocked,scoped,old in grid]
 source_geo=cut['replacement_geometry'];seam=cut['cap_wgs'];owner=r['owner'];ready=read(args.macro/'READY.json')
 c={'id':model,**r['author_frame']['anchor'],'heading':r['author_frame']['runtime_heading_deg'],'altitude':0,'scale':1,'owner':{k:owner[k]for k in ('macro_id','feature_local_id')},'source_feature_ids':{'building':[owner['source_key'].split(':',1)[1]],'building_part':[]},'model_geometry_sha256':{k:s['sha256']for k,s in assets.items()},'bounds_glb':bounds,'replacement_geometry':source_geo,'collision_geometry':mesh.wgs(collision),'source_section_caps':{'geometry':seam,'base_m':0,'roof_m':cut['native_sources']['far']['height_m'],'far_sha256':sha(args.macro/'far.glb'),'height_reference':[ready['origin_longitude'],ready['origin_latitude']]},'overviewBearing':-32,'overviewPitch':39,'overviewZoom':19.8,'maxDistance':570,'lod_switch_in_m':580,'lod_switch_out_m':760,'partial_model':True,'model_scope':m['model_scope_zh'],'navigation':{'listed':False,'status':'从九江路望见连续砖券窗和三座山花，转角外廊可步行。'},'placement':{'status':'estimated','note':'按市文旅2022年公开照片、具名建筑轮廓和九江路路牌落位。南向临街体量、东南近角和底层外廊据照片估算，后楼及江西中路另一侧墙保留。'}}
 for k in ('replacement_geometry','collision_geometry'):checked_geometry(c[k],k,collision=k=='collision_geometry')
 check_source_section_caps(c,shape(source_geo))
 write(args.out/'final-placement-contract.json',c)
 write(args.out/'placement-geometry.json',{'id':model,'manifest_sha256':sha(args.manifest),'contract_sha256':sha(args.out/'final-placement-contract.json'),'source_cut_sha256':sha(args.previous_source_cut),'source_cut_m2':mask.area,'model_area_m2':profile.area,'collision_area_m2':collision.area,'computed_sections':len(layers),'ground_points':probes,'bounds_glb':bounds,'native_variants':cut['native_sources'],'other_owners':cut['other_group_owners'],'vector':cut['vector']})
 print('verified',len(probes),'walk/solid witnesses on both delivered meshes')
