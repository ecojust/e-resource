"""Classify archival image rays by their intersection with the delivered balcony mesh."""
import argparse,hashlib,json,struct
from pathlib import Path
import numpy as np
HERE=Path(__file__).parent
PREFIX='Cheng historic balcony | '
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def unpack(path):
 data=path.read_bytes()
 assert data[:4]==b'glTF'
 size,=struct.unpack_from('<I',data,12);doc=json.loads(data[20:20+size]);buf=memoryview(data)[28+size:]
 def accessor(index):
  a=doc['accessors'][index];view=doc['bufferViews'][a['bufferView']];dt=np.dtype({5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]);w={'SCALAR':1,'VEC3':3}[a['type']]
  return np.ndarray((a['count'],w),dt,buf,view.get('byteOffset',0)+a.get('byteOffset',0),strides=(view.get('byteStride',dt.itemsize*w),dt.itemsize))
 triangles=[];names=[]
 for node in doc['nodes']:
  assert not set(node)&{'matrix','rotation','translation','scale','children'},'flatten model transforms before checking'
  for g in doc['meshes'][node['mesh']]['primitives']:
   points=accessor(g['attributes']['POSITION'])[accessor(g['indices']).ravel()].reshape(-1,3,3)[:,:,[0,2,1]].astype(float)
   points[:,:,1]*=-1;triangles.extend(points);names.extend([doc['materials'][g['material']]['name']]*len(points))
 return np.array(triangles),np.array(names)
def inspect(camera,model,probe,edges):
 p=np.array(json.loads(camera.read_text())['P']);m=np.linalg.inv(p[:,:3]);eye= -m@p[:,3]
 t,mat=unpack(model);a=t[:,1]-t[:,0];b=t[:,2]-t[:,0];s=eye-t[:,0];q=np.cross(s,a)
 def first(xy):
  d=m@[*xy,1];d/=np.linalg.norm(d)
  pv=np.cross(d,b);det=np.einsum('ij,ij->i',a,pv);iv=np.divide(1.,det,out=np.zeros_like(det),where=abs(det)>1e-10)
  u=np.einsum('ij,ij->i',s,pv)*iv;v=(q@d)*iv;ds=np.einsum('ij,ij->i',b,q)*iv;ids=np.flatnonzero((abs(det)>1e-10)&(u>=-1e-8)&(v>=-1e-8)&(u+v<=1+1e-8)&(ds>0))
  if not len(ids):return 'open',None
  hit=mat[ids[np.argmin(ds[ids])]]
  return ('rib' if hit.startswith(PREFIX)else 'open'),str(hit)
 tests=json.loads(probe.read_text());out=[]
 for v in tests['points']:
  got,hit=first(v['pixel']);out.append({**v,'observed':got,'first_material':hit,'matches':got==v['expected']})
 edge_rows=[]
 for panel in json.loads(edges.read_bytes())['panels']:
  for rec in panel['points'][1:]:
   if not rec['eligible_contour_control']:continue
   xy=np.asarray(rec['pixel_640']);normal=np.asarray(rec['normal_xy'])
   hits=[first(xy+normal*dist)for dist in (-2,0,2)]
   edge_rows.append(dict(panel=panel['panel'],pixel=xy.tolist(),sample_distances_native_px=[-2,0,2],classes=[t[0]for t in hits],materials=[t[1]for t in hits],straddles_projected_opening=frozenset(t[0]for t in hits)=={'rib','open'}))
 return dict(model_sha256=sha(model),camera_sha256=sha(camera),pixels_sha256=sha(probe),source_edges_sha256=sha(edges),actual_triangles=len(t),sample_count=len(out),matches=sum(x['matches']for x in out),first_hits=out,edge_checks=edge_rows,method='取旧照相机P反投影，与交付网格全部面作不剔背面的首次交会。凡先遇花栏材质归前景；先遇后墙、窗或天空归孔后。标记光学明暗边的±2像素两侧供比，灰度并不能单独证明通孔。')
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('camera',type=Path);parser.add_argument('model',type=Path);parser.add_argument('output',type=Path)
 parser.add_argument('--probes',type=Path,default=HERE/'archival-railing-probe-pixels.json');parser.add_argument('--edges',type=Path,default=HERE/'old-gatehouse-railing-two-scans.json');a=parser.parse_args()
 report=inspect(a.camera,a.model,a.probes,a.edges);a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(report['matches'],report['sample_count'],[(n,sum(r['matches']for r in report['first_hits']if r['panel']==n))for n in range(1,5)],sum(r['straddles_projected_opening']for r in report['edge_checks']),len(report['edge_checks']))
