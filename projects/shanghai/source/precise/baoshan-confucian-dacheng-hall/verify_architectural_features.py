#!/usr/bin/env python3
"""Probe actual final raw GLB triangles for openings, solid controls, benches and stairs."""
from pathlib import Path
import argparse,json,struct,hashlib,math
import numpy as np

def main():
 p=argparse.ArgumentParser();p.add_argument('--glb',type=Path,required=True);p.add_argument('--geometry',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
 b=a.glb.read_bytes();n,k=struct.unpack_from('<II',b,12);d=json.loads(b[20:20+n]);binary=b[28+n:]
 def arr(i):
  ac=d['accessors'][i];v=d['bufferViews'][ac['bufferView']];dt={5126:'<f4',5125:'<u4',5123:'<u2'}[ac['componentType']];cols={'VEC3':3,'SCALAR':1}[ac['type']]
  return np.ndarray((ac['count'],cols),dtype=dt,buffer=binary,offset=v.get('byteOffset',0)+ac.get('byteOffset',0),strides=(v.get('byteStride',np.dtype(dt).itemsize*cols),np.dtype(dt).itemsize))
 tris=[]
 for m in d['meshes']:
  for q in m['primitives']:
   pos=arr(q['attributes']['POSITION']);ids=arr(q['indices']).ravel().reshape(-1,3);tris.append(pos[ids].astype(float))
 tri=np.concatenate(tris);low=tri.min(1);high=tri.max(1)
 g=json.loads(a.geometry.read_text());points=np.array(g['model_geometry_local_east_north_m']['coordinates'][0]);v=points[1]-points[0];theta=math.atan2(v[1],v[0]);c,s=math.cos(theta),math.sin(theta)
 def gltf(p):x,y,z=p;return np.array([c*x-s*y,z,-s*x-c*y])
 def hits(start,end):
  o=gltf(start);e=gltf(end);direction=e-o;length=np.linalg.norm(direction);direction/=length
  mask=np.all(high>=np.minimum(o,e)-1e-7,axis=1)&np.all(low<=np.maximum(o,e)+1e-7,axis=1)
  t=tri[mask];e1=t[:,1]-t[:,0];e2=t[:,2]-t[:,0];h=np.cross(np.broadcast_to(direction,e2.shape),e2);det=np.einsum('ij,ij->i',e1,h);valid=np.abs(det)>1e-10;inv=np.zeros(len(det));inv[valid]=1/det[valid]
  dv=o-t[:,0];u=inv*np.einsum('ij,ij->i',dv,h);q=np.cross(dv,e1);vv=inv*(q@direction);dist=inv*np.einsum('ij,ij->i',e2,q)
  valid &= (u>=-1e-8)&(vv>=-1e-8)&(u+vv<=1+1e-8)&(dist>=-1e-8)&(dist<=length+1e-8)
  return dist[valid]
 rows=[]
 def probe(kind,p0,p1,clear):
  h=hits(p0,p1);assert (len(h)==0)==clear,(kind,p0,len(h));rows.append({'kind':kind,'start_principal_xyz':list(p0),'end_principal_xyz':list(p1),'triangle_hits':len(h),'expected':'clear' if clear else 'solid','passed':True})
 for bay,(left,right,count) in enumerate([(-6.16,-2.95,4),(-2.55,2.55,8),(2.95,6.16,4)]):
  w=(right-left)/count-.018
  for leaf in range(count):
   x0=left+leaf*(right-left)/count;ox=x0+.055;ex=x0+w-.055;oz=2.18;ez=3.93
   for i,j in [(0,0),(2,7),(5,14)]:
    x=ox+(ex-ox)*(i+.5)/6;z=oz+(ez-oz)*(j+.5)/15;probe(f'door-bay{bay}-leaf{leaf}-lattice-{i}-{j}',(x,-4.45,z),(x,-4.0,z),True)
   probe(f'door-bay{bay}-leaf{leaf}-lower-solid-control',(x0+w/2,-4.45,1.7),(x0+w/2,-4.0,1.7),False)
 railfaces=[((-8.04,-9.20),(-3.40,-9.20)),((3.40,-9.20),(8.04,-9.20)),((-8.04,-6.3),(-8.04,-9.2)),((8.04,-9.2),(8.04,-6.3))]
 for k,(p0,p1) in enumerate(railfaces):
  p0=np.array(p0);p1=np.array(p1);length=np.linalg.norm(p1-p0);t=(p1-p0)/length;n=np.array([t[1],-t[0]]);count=max(2,round(length/1.25));step=length/count
  for j in range(count):
   pt=p0+t*(j+.5)*step;aa=pt+n*.15;bb=pt-n*.15;probe(f'balustrade{k}-actual-hole{j}',(*aa,1.55),(*bb,1.55),True)
 for side in [-1,1]:
  h=hits((side*7.725,0,1.8),(side*7.725,0,1.2));top=1.8-min(h);assert abs(top-1.48)<1e-5
  rows.append({'kind':'official-bench-top','side':side,'measured_model_top_m':top,'floor_m':1.,'model_height_m':top-1.,'required_m':.48,'passed':True})
 for rear in [False,True]:
  for j in range(6):
   y=(6.22+(6-j-.5)*.3) if rear else (-9.35-(6-j-.5)*.3);x=0 if rear else 2.
   h=hits((x,y,1.5),(x,y,-.1));z=1.5-min(h);expected=(j+1)/6;assert abs(z-expected)<1e-5,(rear,j,z,expected)
   rows.append({'kind':'actual-stair-tread','side':'rear' if rear else 'front','index':j,'sample_principal_xy':[x,y],'top_m':z,'expected_m':expected,'passed':True})
 report={'passed':True,'raw':str(a.glb.resolve()),'raw_bytes':len(b),'raw_sha256':hashlib.sha256(b).hexdigest(),'triangles':len(tri),'probe_count':len(rows),'probes':rows,'scope':'Actual raw triangle segments through48lattice openings with16solid-panel controls,12balustrade apertures,2bench tops and12stair tread heights. Not a survey accuracy or every decorative detail check.'}
 a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['passed','raw_sha256','triangles','probe_count']}))
if __name__=='__main__':main()
