"""Read actual GLB triangles and the SHA-bound part table; never import builder code."""
from pathlib import Path
from collections import defaultdict, Counter
import hashlib,json,struct
import numpy as np
def need(ok,message):
 if not ok:raise ValueError(message)

def sha(data):return hashlib.sha256(data).hexdigest()

def filemeta(p):
 b=p.read_bytes();return {'file':str(p),'bytes':len(b),'sha256':sha(b)}

def loadraw(path):
 data=path.read_bytes();need(struct.unpack_from('<4sII',data)==(b'glTF',2,len(data)),'Bad GLB');n,k=struct.unpack_from('<II',data,12);need(k==0x4e4f534a,'Bad JSON chunk');doc=json.loads(data[20:20+n]);bn,bk=struct.unpack_from('<II',data,20+n);need(bk==0x004e4942 and 28+n+bn==len(data),'Bad BIN');binary=memoryview(data)[28+n:]
 sp=path.with_suffix('.geometry.json');sb=sp.read_bytes();side=json.loads(sb);need(side['sha256']==sha(data) and side['bytes']==len(data),'Sidecar/raw SHA mismatch')
 need(len(data)<100_000_000 and len(doc['nodes'])==1 and doc['nodes'][0].get('mesh')==0 and len(doc['meshes'])==1,'Unexpected size/scene');need(not any(x in doc['nodes'][0] for x in ['matrix','translation','rotation','scale']),'Node transform changed');need(not doc.get('images') and not doc.get('textures'),'Unexpected image payload')
 def acc(i):
  a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']];need(not v.get('extensions') and not v.get('byteStride') and 'sparse' not in a,'Compressed/strided raw unsupported');w={'SCALAR':1,'VEC3':3}[a['type']];return np.frombuffer(binary,dtype={5125:'<u4',5126:'<f4'}[a['componentType']],offset=v.get('byteOffset',0)+a.get('byteOffset',0),count=a['count']*w).reshape(-1,w)
 bymat=defaultdict(list)
 for row in side['part_summary']:bymat[row['material']].append(row)
 parts={};occurrences=Counter();mats={};triangles=0
 for pr in doc['meshes'][0]['primitives']:
  mat=doc['materials'][pr['material']];name=mat['name'];need(name not in mats,'Duplicate material name');mats[name]=mat;pos=acc(pr['attributes']['POSITION']);norm=acc(pr['attributes']['NORMAL']);ids=acc(pr['indices']).ravel().reshape(-1,3);cursor=0
  for row in bymat[name]:
   pair=(row['label'],name);ordinal=occurrences[pair];occurrences[pair]+=1;key=(*pair,ordinal);count=row['triangles'];parts[key]={'row':row,'pos':pos,'norm':norm,'indices':ids[cursor:cursor+count]};cursor+=count
  need(cursor==len(ids),'Part layout mismatch');triangles+=len(ids)
 need(triangles==side['triangles'] and len(parts)==side['parts'],'Global part counts differ')
 return {'path':path,'data':data,'doc':doc,'side':side,'parts':parts,'materials':mats,'side_sha256':sha(sb),'raw':{'file':str(path),'bytes':len(data),'sha256':sha(data)}}

def enu_tri(part):return part['pos'][part['indices']].astype(float)[:,:,[0,2,1]]*[1,-1,1]

def z(t,xy,top):
 a=t[:,0,:2];b=t[:,1,:2]-a;c=t[:,2,:2]-a;d=np.asarray(xy)-a;det=b[:,0]*c[:,1]-b[:,1]*c[:,0];ix=np.flatnonzero(det>1e-12 if top else det< -1e-12)
 if not len(ix):return None
 b,c,d,det,t=b[ix],c[ix],d[ix],det[ix],t[ix];u=(d[:,0]*c[:,1]-d[:,1]*c[:,0])/det;v=(b[:,0]*d[:,1]-b[:,1]*d[:,0])/det;ok=(u>=-1e-7)&(v>=-1e-7)&(u+v<=1+1e-7)
 if not ok.any():return None
 zz=t[:,0,2]+u*(t[:,1,2]-t[:,0,2])+v*(t[:,2,2]-t[:,0,2]);return float(max(zz[ok]) if top else min(zz[ok]))
