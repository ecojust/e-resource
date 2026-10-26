#!/usr/bin/env python3
"""Read actual exported GLB: finite geometry/normals, wall-hole rays and glass fit."""
import argparse,json,struct,hashlib
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon
HERE=Path(__file__).resolve().parent

def main(out):
 p=out/'xuhui-wukang-210-raw.glb';data=p.read_bytes();assert len(data)<100_000_000;magic,version,size=struct.unpack_from('<4sII',data);assert (magic,version,size)==(b'glTF',2,len(data));jl=struct.unpack_from('<I',data,12)[0];g=json.loads(data[20:20+jl]);binary=data[28+jl:];assert not g.get('images') and not any('uri'in x for x in g['buffers'])
 def acc(i):
  a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];assert not v.get('byteStride');n={'VEC3':3,'SCALAR':1}[a['type']];dt={5126:'<f4',5125:'<u4'}[a['componentType']];return np.frombuffer(binary,dtype=dt,count=a['count']*n,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,n)
 meshes={};tris=0;maxnormal=0
 for prim in g['meshes'][0]['primitives']:
  v=acc(prim['attributes']['POSITION']).astype(float);ns=acc(prim['attributes']['NORMAL']).astype(float);idx=acc(prim['indices']).ravel().reshape(-1,3);assert np.isfinite(v).all() and np.isfinite(ns).all();t=v[idx];n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);ln=np.linalg.norm(n,axis=1);assert ln.min()>1e-12;n/=ln[:,None];stored=ns[idx[:,0]];stored/=np.linalg.norm(stored,axis=1)[:,None];ang=np.degrees(np.arccos(np.clip((n*stored).sum(1),-1,1)));maxnormal=max(maxnormal,float(ang.max()));assert ang.max()<.001
  meshes[g['materials'][prim['material']]['name']]=(v[:,[0,2,1]]*[1,-1,1],idx);tris+=len(idx)
 v,ix=meshes['cream stippled render'];wall=v[ix]
 def ray(o,d,limit=.8):
  e1=wall[:,1]-wall[:,0];e2=wall[:,2]-wall[:,0];h=np.cross(d,e2);det=(e1*h).sum(1);ok=abs(det)>1e-10;inv=np.zeros(len(det));inv[ok]=1/det[ok];s=o-wall[:,0];u=inv*(s*h).sum(1);q=np.cross(s,e1);vv=inv*(q*d).sum(1);t=inv*(e2*q).sum(1);return int(np.count_nonzero(ok&(u>=-1e-8)&(vv>=-1e-8)&(u+vv<=1+1e-8)&(t>0)&(t<limit)))
 rec=json.load(open(out/'opening-audit.json'));voids=[];glass=[]
 for w in rec['windows']:
  O=np.asarray(w['facade_origin']);T=np.asarray(w['facade_u']);N=np.asarray(w['facade_out']);poly=Polygon(w['opening']);x0,z0,x1,z1=poly.bounds;center=O+T*((x0+x1)/2)+[0,0,(z0+z1)/2];hole=ray(center+N*.35,-N);solid=ray(center-T*((x1-x0)/2+.10)+N*.35,-N);assert hole==0,(w['label'],hole);assert solid>0,(w['label'],'adjacent-wall-negative-control',solid);voids.append({'label':w['label'],'void_ray_hits':hole,'neighbor_solid_ray_hits':solid})
  points=[]
  for name in ['estimated muted glass','curtain glass']:
   if name not in meshes:continue
   v=meshes[name][0];off=v-O;u=off@T;d=off@N;z=v[:,2];sel=(u>x0-1e-5)&(u<x1+1e-5)&(z>z0-1e-5)&(z<z1+1e-5)&(d>-.14)&(d<.01);points.extend(d[sel].tolist())
  assert points,w['label'];lo,hi=min(points),max(points);assert abs(lo+.077)<5e-6 and abs(hi+.057)<5e-6,(w['label'],lo,hi);assert -.115<lo<hi<-.035;glass.append({'label':w['label'],'actual_depth_range_m':[lo,hi],'frame_depth_m':[-.115,-.035],'embedded_inside_frame':True})
 source=json.load(open(HERE/'geometry-input.json'));assert source['replacement']['feature_local_ids']==[563] and len(source['replacement']['retained_same_near_feature_local_ids'])==23;assert g['extras']['source_geometry_sha256']==hashlib.sha256((HERE/'geometry-input.json').read_bytes()).hexdigest()
 f=source['facade_frame'];O=np.asarray(f['origin_local_east_north_m']);T=np.asarray(f['u_east_north'])*-1;Y=np.asarray(f['inward_v_east_north']);W=f['front_width_m'];s=W/14.242;L=-2.4*s;R=2.05*s
 def curve(x):return -.38*(1-((x-(L+R)/2)/((R-L)/2))**2)
 x=-.2*s;center=np.r_[O+T*x+Y*curve(x),1.35];N=np.r_[-Y,0];assert ray(center+N*.35,-N)==0;outside=np.r_[O+T*(x-.80)+Y*curve(x-.80),1.35];assert ray(outside+N*.35,-N)>0
 # An arch shoulder above the spring must still be an actual wall opening.
 center=np.r_[O+T*x+Y*curve(x),2.25];assert ray(center+N*.35,-N)==0
 audit=json.load(open(out/'solid-audit.json'));assert audit['passed'] and audit['triangles']==tris
 report={'passed':True,'raw_sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'triangles':tris,'self_contained_glb':True,'images':0,'max_serialized_normal_error_deg':maxnormal,'window_void_checks':voids,'curved_entry_center_and_arch_void_check':True,'curved_entry_adjacent_solid_negative_control':True,'actual_glass_fit':glass,'solid_parts':audit['parts'],'exact_target_local_ids':[563],'retained_same_near_ids':source['replacement']['retained_same_near_feature_local_ids'],'claim_limit':'Geometry validation only; native visual and browser review remain root tasks.'};(out/'actual-glb-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['passed','bytes','triangles','max_serialized_normal_error_deg','images']},indent=2))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=HERE/'output');main(ap.parse_args().output)
