#!/usr/bin/env python3
"""Finite ray-segment checks against actual serialized GLB triangles.

Checks wall material is absent inside selected real windows and present beside
them; glazing/frames intentionally remain. Also checks true flower vent holes
against the wall and ceramic screen. This is not runtime collision support.
"""
import argparse,json,struct,hashlib,math
from pathlib import Path
import numpy as np

def read(path):
 data=path.read_bytes();n,kind=struct.unpack_from('<II',data,12);doc=json.loads(data[20:20+n]);size,kind=struct.unpack_from('<II',data,20+n);blob=data[28+n:28+n+size]
 def accessor(index):
  a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']];types={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'};cols={'VEC3':3,'VEC2':2,'SCALAR':1}[a['type']];dt=np.dtype(types[a['componentType']]);start=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',cols*dt.itemsize)
  return np.ndarray((a['count'],cols),dtype=dt,buffer=blob,offset=start,strides=(stride,dt.itemsize)).copy()
 mats={}
 assert len(doc['nodes'])==1 and 'matrix' not in doc['nodes'][0], 'Audit expects the authored single identity node'
 for p in doc['meshes'][0]['primitives']:
  xyz=accessor(p['attributes']['POSITION']).astype(float);xyz=xyz[:,[0,2,1]]*np.array([1,-1,1]);tri=xyz[accessor(p['indices']).reshape(-1,3)]
  mats[doc['materials'][p['material']]['name']]=tri
 return mats

def hits(tri,origin,direction,length):
 a,b,c=tri[:,0],tri[:,1],tri[:,2];e1=b-a;e2=c-a;p=np.cross(np.broadcast_to(direction,e2.shape),e2);det=np.einsum('ij,ij->i',e1,p);ok=np.abs(det)>1e-10
 inv=np.zeros_like(det);inv[ok]=1/det[ok];t=origin-a;u=np.einsum('ij,ij->i',t,p)*inv;q=np.cross(t,e1);v=q@direction*inv;dist=np.einsum('ij,ij->i',e2,q)*inv
 return int(np.count_nonzero(ok&(u>=-1e-8)&(v>=-1e-8)&(u+v<=1+1e-8)&(dist>1e-6)&(dist<length-1e-6)))

def main():
 p=argparse.ArgumentParser();p.add_argument('raw',type=Path);p.add_argument('probe_input',type=Path);p.add_argument('output',type=Path);a=p.parse_args();m=read(a.raw);data=json.loads(a.probe_input.read_text());angle=data['rotation_radians'];R=np.array([[math.cos(angle),-math.sin(angle),0],[math.sin(angle),math.cos(angle),0],[0,0,1.]])
 walls=np.concatenate([m[n] for n in ['historic rough stucco','east addition stucco'] if n in m]);screens=np.concatenate([walls,m['dark grey grille'] if 'dark grey grille' in m else m['green ceramic']]);results=[]
 def check(label,point,normal,solid,geometry=walls):
  point=R@np.array(point);normal=R@np.array(normal);count=hits(geometry,point+normal*.36,-normal,.80);passed=(count>0)==solid
  results.append({'label':label,'expect':'solid material hit' if solid else 'through aperture in selected material','hits':count,'passed':passed,'segment_start_enu':(point+normal*.36).tolist(),'segment_end_enu':(point-normal*.44).tolist()})
 selected=('south-arch-','west-ground-arch-','west-upper-','central-upper-','east-ground-curved-door','northwest-office/front/rect-window-','northeast-office/front/rect-window-')
 for q in data['probes']:
  if not q['label'].startswith(selected):continue
  c=np.array(q['center_principal_enu']);n=np.array(q['outward_principal_enu']);t=np.array([-n[1],n[0],0.]);check(q['label']+'/wall-opening',c,n,False);check(q['label']+'/adjacent-solid-jamb',c+t*(q['width_m']/2+.08),n,True)
 # Eleven groups of three known pierced ceramic cells. Points are selected from
 # the authored feature specification; outcomes come only from actual buffers.
 width=335/12;center=np.array([((176+511)/2-377)/12,(310-441)/12,5.78]);n=[0,-1,0]
 for j in range(11):
  for k in [-1,0,1]:
   c=center+[(j-5)*width/11+k*.47,0,0]
   check(f'flower-vent-{j}-{k}/central-hole',c,n,False,screens)
   check(f'flower-vent-{j}-{k}/solid-corner',c+[.19,0,.19],n,True,screens)
 report={'scope':'Finite feature ray probes on actual raw triangles; does not claim movement collision or staircase traversal in the browser','raw_sha256':hashlib.sha256(a.raw.read_bytes()).hexdigest(),'probes':len(results),'passed':all(r['passed'] for r in results),'failures':[r for r in results if not r['passed']],'results':results}
 a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['probes','passed','failures']}));assert report['passed']
if __name__=='__main__':main()
