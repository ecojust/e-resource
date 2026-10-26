#!/usr/bin/env python3
"""Decode actual uncompressed raw GLB and check genuine facade voids and normals."""
import argparse,hashlib,json,struct
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check(path):
 data=path.read_bytes();assert data[:4]==b'glTF' and len(data)<100_000_000
 assert struct.unpack_from('<II',data,4)==(2,len(data))
 jlen,jtype=struct.unpack_from('<II',data,12);assert jtype==0x4e4f534a
 doc=json.loads(data[20:20+jlen]);blen,btype=struct.unpack_from('<II',data,20+jlen);assert btype==0x004e4942
 buf=data[28+jlen:];assert len(buf)==blen
 assert all('uri' not in x for x in doc.get('buffers',[])) and not doc.get('images')
 for token in ['Fayhoo','CC BY-SA 3.0','East Asian Buildings','OFL']:assert token in doc['asset']['copyright']
 assert doc['extras']['source_geometry_sha256']==sha(HERE/'geometry-input.json')
 assert doc['extras']['calibration_sha256']==sha(HERE/'calibration.json')
 assert doc['extras']['source_photo_sha256']==sha(HERE/'photos/commons-33172025.jpg')
 def acc(i):
  a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']];n={'SCALAR':1,'VEC3':3}[a['type']]
  assert not v.get('byteStride')
  return np.frombuffer(buf,dtype={5126:'<f4',5125:'<u4'}[a['componentType']],offset=v.get('byteOffset',0)+a.get('byteOffset',0),count=a['count']*n).reshape(-1,n)
 meshes={};alltri=[];normmax=0;tris=0
 for prim in doc['meshes'][0]['primitives']:
  p=acc(prim['attributes']['POSITION']).astype(float);n=acc(prim['attributes']['NORMAL']).astype(float);t=acc(prim['indices']).ravel().reshape(-1,3)
  assert np.isfinite(p).all() and np.isfinite(n).all() and t.max()<len(p)
  tri=p[t];cross=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);length=np.linalg.norm(cross,axis=1);assert length.min()>1e-12
  cross/=length[:,None];ns=n[t[:,0]];ns/=np.linalg.norm(ns,axis=1)[:,None]
  err=np.degrees(np.arccos(np.clip(np.einsum('ij,ij->i',cross,ns),-1,1)));normmax=max(normmax,float(err.max()));assert err.max()<.001
  name=doc['materials'][prim['material']]['name'];enu=p[:,[0,2,1]]*[1,-1,1];meshes[name]=enu[t];alltri.append(enu[t]);tris+=len(t)
 g=json.loads((HERE/'geometry-input.json').read_text());assert g['replacement']['feature_local_ids']==[25]
 assert len(g['replacement']['retained_same_near_feature_local_ids'])==27
 O=np.r_[g['front_edge']['center_local_east_north_m'],0.];T=-np.r_[g['front_edge']['tangent_east_north'],0.];N=np.r_[g['front_edge']['outward_normal_east_north'],0.];W=g['front_edge']['length_m']
 def ray(mesh,u,z,d=.30,limit=.95):
  origin=O+T*u+N*d+[0,0,z];direction=-N
  e1=mesh[:,1]-mesh[:,0];e2=mesh[:,2]-mesh[:,0];h=np.cross(np.broadcast_to(direction,e2.shape),e2);det=np.einsum('ij,ij->i',e1,h)
  good=np.abs(det)>1e-10;inv=np.zeros(len(det));inv[good]=1/det[good];s=origin-mesh[:,0];q=np.cross(s,e1)
  a=inv*np.einsum('ij,ij->i',s,h);b=inv*np.einsum('ij,j->i',q,direction);t=inv*np.einsum('ij,ij->i',e2,q)
  return int(np.count_nonzero(good&(a>=-1e-7)&(b>=-1e-7)&(a+b<=1+1e-7)&(t>0)&(t<limit)))
 mortar=meshes['lime mortar'];masonry=np.concatenate([v for k,v in meshes.items() if k=='lime mortar' or k.startswith('grey brick')])
 voids=[]
 for i,u in enumerate([-W/3,0,W/3]):
  h=ray(masonry,u,1.70);negative=ray(mortar,u+1.10,1.70);assert h==0 and negative>0
  voids.append({'bay':i,'masonry_hits_inside_actual_arch':h,'negative_adjacent_wall_hits':negative})
 # At z5 the entire front gallery remains open until the recessed back joinery.
 full=np.concatenate(alltri);gallery=[]
 for i,u in enumerate([-W/3,0,W/3]):
  hits=ray(full,u,5.10,d=.30,limit=1.20);assert hits==0,(i,hits)
  gallery.append({'bay':i,'front_open_gallery_ray_hits':hits,'ray_from_d_m':.30,'ray_to_d_m':-.90})
 # Glass panes are cut around the actual bars; they are 20mm behind frame faces.
 gv=np.unique(meshes['quiet glass'].reshape(-1,3),axis=0);depth=(gv-O)@N
 front=depth[depth>-.5];upper=depth[depth<-.5]
 assert np.max(np.abs(np.unique(np.round(front,5))-np.array([-.158,-.145])))<1e-5
 assert np.max(np.abs(np.unique(np.round(upper,5))-np.array([-1.218,-1.205])))<1e-5
 return {'schema':'teahouse-actual-glb-independent-check-v7','passed':True,'raw_bytes':len(data),'raw_sha256':sha(path),'triangles':tris,'materials':len(doc['materials']),'self_contained':True,'embedded_images':0,'maximum_normal_deviation_deg':normmax,'actual_front_arch_voids':voids,'actual_open_gallery_rays':gallery,'glass_actual_depths_m':{'ground':[-.158,-.145],'upper':[-1.218,-1.205]},'glass_front_behind_actual_frame_front_m':.020,'source_photo_sha256':sha(HERE/'photos/commons-33172025.jpg'),'source_geometry_sha256':sha(HERE/'geometry-input.json'),'target_local_id':25,'retained_neighbors':27,'visual_acceptance':False,'browser_run':False,'scope':'Actual FLOAT32 positions/normals/indices, source identity/license/size/void checks. Not a visual acceptance, measured-height claim or check of unseen rear architecture.','checker_sha256':sha(__file__)}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--glb',type=Path,default=HERE/'output/qingpu-beidajie-208-212-raw.glb');p.add_argument('--output',type=Path,default=HERE/'audit/glb-check.json');a=p.parse_args();r=check(a.glb);a.output.parent.mkdir(exist_ok=True,parents=True);a.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:r[k] for k in ['passed','raw_bytes','triangles','maximum_normal_deviation_deg']}))
