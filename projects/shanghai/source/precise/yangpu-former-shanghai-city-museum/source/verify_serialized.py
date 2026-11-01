"""Read actual serialized geometry, verify facade recesses and roof openings.

Compressed files must first be decoded by gltfpack. No construction code is
executed by this checker. Scene identity is asserted before mesh collection.
"""
from pathlib import Path
import argparse,hashlib,json,struct
import numpy as np
import trimesh

ID='yangpu-former-shanghai-city-museum'
def load(path,source_asset=None):
 data=path.read_bytes();n=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+n])
 if source_asset is None:assert doc.get('extras',{}).get('id')==ID, 'A gltfpack-decoded file without global extras requires --source-asset binding'
 else:
  src=source_asset.read_bytes();sn=struct.unpack_from('<I',src,12)[0];sd=json.loads(src[20:20+sn]);assert sd['extras']['id']==ID
 assert not any('EXT_meshopt_compression' in v.get('extensions',{}) for v in doc.get('bufferViews',[])), 'Decode compressed geometry before trimesh inspection'
 assert len(doc['scenes'])==1 and doc['scenes'][0]['nodes']==[0]
 assert len(doc['nodes'])==1 and doc['nodes'][0].get('mesh')==0
 assert not any(k in doc['nodes'][0] for k in ['translation','rotation','scale','matrix','extensions','children'])
 scene=trimesh.load(path,force='scene',process=False);triangles=[];tags=[];digests={}
 for mesh in scene.geometry.values():
  t=np.asarray(mesh.triangles);material=mesh.visual.material.name;triangles.append(t[:,:,[0,2,1]]*np.array([1,-1,1]));tags.extend([material]*len(t));digests.setdefault(material,[]).append(t)
 def digest(t):
  v=np.array(t,dtype='<f4');v[v==0]=0;starts=np.lexsort((v[:,:,2],v[:,:,1],v[:,:,0]),axis=-1)[:,0];v=v[np.arange(len(v))[:,None],(starts[:,None]+np.arange(3))%3];rows=np.ascontiguousarray(v.reshape(-1,9)).view(np.dtype((np.void,36))).ravel();return hashlib.sha256(np.sort(rows).tobytes()).hexdigest()
 return np.concatenate(triangles),np.array(tags),{k:digest(np.concatenate(v)) for k,v in digests.items()}

def check(path,probes,source_asset=None):
 triangles,tags,digests=load(path,source_asset);a=triangles[:,0];e1=triangles[:,1]-a;e2=triangles[:,2]-a
 def first(origin,direction,max_distance=100):
  origin=np.array(origin,float);direction=np.array(direction,float);direction/=np.linalg.norm(direction);h=np.cross(direction,e2);det=np.einsum('ij,ij->i',e1,h);valid=np.abs(det)>1e-10;inv=np.zeros(len(det));inv[valid]=1/det[valid];s=origin-a;u=inv*np.einsum('ij,ij->i',s,h);q=np.cross(s,e1);v=inv*np.einsum('j,ij->i',direction,q);t=inv*np.einsum('ij,ij->i',e2,q)
  idx=np.flatnonzero(valid&(u>=-1e-8)&(v>=-1e-8)&(u+v<=1+1e-8)&(t>1e-6)&(t<max_distance))
  if not len(idx):return None
  i=idx[np.argmin(t[idx])];return {'distance_m':float(t[i]),'material':str(tags[i]),'point_enu':(origin+direction*t[i]).tolist()}
 rows=[]
 for p in probes:
  if p.get('kind') in ['ray','void','solid']:
   hit=first(p['origin'],p['direction'],p['max_distance']);passed=(hit is None) if p['kind']=='void' else (hit is not None if p['kind']=='solid' else hit is not None and hit['material']==p['material']);rows.append({'label':p['label'],'origin':p['origin'],'direction':p['direction'],'expected_material':p.get('material'),'first_hit':hit,'passed':passed});continue
  normal=np.array(p['normal']);offset=.35;origin=np.array(p['point'])+normal*offset;hit=first(origin,-normal,5)
  passed=(hit is not None and p['depth']+offset<hit['distance_m']<p['maximum_depth']+offset) if p.get('kind')=='portal-clear-prefix' else (hit is not None and hit['material']==p['material'] and abs(hit['distance_m']-offset-p['depth'])<1e-4)
  rows.append({'label':p['label'],'origin':origin.tolist(),'direction':(-normal).tolist(),'expected_depth_m':p['depth'],'expected_material':p['material'],'first_hit':hit,'passed':passed})
 return {'id':ID,'file':path.name,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'triangles':len(triangles),'count':len(rows),'passed':all(r['passed'] for r in rows),'failures':[r for r in rows if not r['passed']],'records':rows,'oriented_float32_surface_digests_by_material':digests,'scene_identity_asserted':True,'compressed_source_asset':({'file':source_asset.name,'bytes':source_asset.stat().st_size,'sha256':hashlib.sha256(source_asset.read_bytes()).hexdigest()} if source_asset else None),'limitation':'Only exterior geometry; dark arch backstops bound unseen interior and do not claim exact existing gates or indoor museum access.'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--asset',type=Path,required=True);p.add_argument('--probes',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--source-asset',type=Path);a=p.parse_args();r=check(a.asset,json.loads(a.probes.read_text()),a.source_asset);a.out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:r[k] for k in ['file','triangles','count','passed','failures']},ensure_ascii=False));raise SystemExit(0 if r['passed'] else 1)
