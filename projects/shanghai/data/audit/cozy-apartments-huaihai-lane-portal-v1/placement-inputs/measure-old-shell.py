"""Measure both decoded city meshes across the door, the second-story windows and the 16-metre roof."""
from pathlib import Path
import json,runpy,math
import numpy as np
import shapely as g
from shapely.geometry import box,shape,Point,LineString
w=Path(__file__).parent;lib=runpy.run_path(str(w/'decode-source.py'));cfg=lib['cfg'];decode=lib['decode'];polys=lib['polygons'];fid=2172;neg=set(cfg['checked_neighbors']);phase={};peer={};src=[]
def hits_along_y(tri,x,z):
 p=tri[:,0];e1=tri[:,1]-p;e2=tri[:,2]-p;den=e1[:,0]*e2[:,2]-e1[:,2]*e2[:,0];valid=np.abs(den)>1e-9
 vect=np.array([x,z])-p[:,[0,2]];den=np.where(valid,den,1);t=(vect[:,0]*e2[:,2]-vect[:,1]*e2[:,0])/den;u=(e1[:,0]*vect[:,1]-e1[:,2]*vect[:,0])/den;valid &= (t>=-1e-7)&(u>=-1e-7)&(t+u<=1+1e-7);d=(p+t[:,None]*e1+u[:,None]*e2)[:,1][valid];return sorted(set(np.round(d,5)))
mask=box(-1.81,-.35,1.81,4.175);upper=box(-2.70,-.35,2.41,1.18)
def cut(x,y,z):
 return (mask.covers(Point(x,y)) and -.12<=z<=3.24) or (upper.covers(Point(x,y)) and -.12<=z<=7.19)
for grp in cfg['groups']:
 for role,tri,owners,gap in decode(grp):
  for i in (set(grp['owners'])&({fid}|neg)):
   t=tri[owners==i];h=float(t[:,:,2].max());roofs=t[np.min(t[:,:,2],axis=1)>h-.17];roof=g.make_valid(g.union_all(g.polygons(roofs[:,:,:2])));area=roof.area;inter=roof.intersection(mask).area;dist=polys[i].distance(mask)
   if i!=fid:
    assert inter<1e-6 and dist>0
    peer.setdefault(i,{})[role]=dict(triangles=len(t),roof_m2=area,unchanged_roof_m2=area,distance_to_passage=dist);continue
   checks=[]
   for typ,xx,zz,expected in [('street-to-passage',[-1.72,-1.45,-.85,0,.85,1.45,1.72],[.10,.34,.85,1.55,2.10,2.85,3.20],True),('second-floor',[-2.43,-1.55,-.7,0,.7,1.55,2.23],[3.30,4.82,5.15,5.9,6.75,7.14],True),('roof-and-upper-wall',[-2.43,-1.55,-.7,0,.7,1.55,2.23],[7.28,8.15,9.2,11,14.5,15.8],False),('side-walls',[-4.1,-3.18,2.75,3.35,5.25],[.25,1.45,3,4.85,6.66,7.50,10.3,14.9],False)]:
    for x in xx:
     for z in zz:
      before=[y for y in hits_along_y(t,x,z) if -.9<=y<5];after=[y for y in before if not cut(x,y,z)]
      # Near old decorative brickwork protrudes and can leave gaps. An empty original does not simulate a clipped observation.
      checks.append(dict(test=typ,x=x,z=z,before=before,after=after,expected_open=expected))
   records={k:[q for q in checks if q['test']==k]for k in ('street-to-passage','second-floor','roof-and-upper-wall','side-walls')}
   for k,v in records.items():
    if k in ('street-to-passage','second-floor'):
     limit=4.15 if k=='street-to-passage'else 1.18
     assert not any(any(-.4<y<=limit for y in q['after'])for q in v),(k,role,[q for q in v if any(-.4<y<=limit for y in q['after'])][:5])
    else:assert all(q['before']==q['after'] for q in v)
   assert abs(h-16)<.03 and 1250<area<1330
   phase[role]=dict(source_group=grp['id'],source_triangles=len(t),original_top_m=h,actual_roof_total_m2=area,retained_roof_m2=area,ground_footprint_cut_inside_roof_projection_m2=inter,old_hits_summary={k:dict(rays=len(v),real_before=sum(bool(q['before'])for q in v),post_visible=sum(bool(q['after'])for q in v)) for k,v in records.items()},rays=checks)
  src.append(dict(role=role,file=grp['file'],sha256=grp['sha256'],decoded=len(tri),owner_inference_gap=gap))
assert set(phase)=={'near','far'} and len(peer)==13 and all(set(v)=={'near','far'}for v in peer.values())
res=dict(order=328,id='huangpu-cozy-apartments-494-lane-portal',owner=2172,macro='14-13720-6694',anchor=cfg['anchor'],heading=cfg['runtime_heading_degrees'],source_bounds={'ground':[-1.81,-.35,1.81,4.175],'restricted_height':[-.12,3.24],'facade':[-2.70,-.35,2.41,1.18],'facade_height':[-.12,7.19]},levels=phase,checked_neighbors=peer,source_groups=src)
(w/'decoded-source-bounds.json').write_text(json.dumps(res,indent=1)+'\n');print({r:(v['source_triangles'],v['actual_roof_total_m2'],v['old_hits_summary'])for r,v in phase.items()},flush=True)
