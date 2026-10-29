"""Partition decoded baseline buffers by unambiguous source footprint ownership.
Never regenerates vertices, normals, triangle winding or instance transforms.
Instance centres / continuous-triangle centroids must be within 0.6m of a
source footprint with a >0.01m nearest-owner margin. For the Sun residence
shared boundary only, an ambiguous point requires a unique generated reference:
TRS tolerance 0.05m translation, 0.001 scale, 0.0005 quaternion components
(up to quaternion sign); triangle vertices use 0.05m with preserved winding.
These bounds classify ownership only: original buffer values are never changed.
Original buffer views are retained; only index/instance subsets are appended.
"""
import argparse,copy,gzip,hashlib,json,math,struct
from pathlib import Path
import numpy as np
from shapely.geometry import shape,Point
from shapely.ops import transform
p=argparse.ArgumentParser();p.add_argument('--project',type=Path,required=True);p.add_argument('--decoded',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--id',default='xuhui-zikawei-south-building');p.add_argument('--instance-reference',type=Path);p.add_argument('--triangle-reference',type=Path);a=p.parse_args()
ID=a.id;g=json.loads((a.project/f'source/precise/{ID}/geometry-input.json').read_text());MACRO=g['macro'];LOCAL=g['feature_local_id']
D=a.project/'assets/city-detail/macros'/MACRO;ready=json.loads((D/'READY.json').read_text());near=next(n for n in ready['near'] if LOCAL in n['featureLocalIds']);table=json.loads(gzip.decompress((D/'feature-table.json.gz').read_bytes()));ids=near['featureLocalIds'];features={f['localId']:f for f in table['features'] if f['localId'] in ids}
lon0,lat0=table['origin'];R=6378137.;c=math.cos(math.radians(lat0));my=math.asinh(math.tan(math.radians(lat0)))
def xy(lon,lat,z=None):return (R*np.radians(np.asarray(lon)-lon0)*c,-R*(np.arcsinh(np.tan(np.radians(lat)))-my)*c)
polys={i:transform(xy,shape(features[i]['geometry'])) for i in ids};audit=[];counts={i:0 for i in ids}
refs=json.loads(a.instance_reference.read_text()) if a.instance_reference else []
trefs=json.loads(a.triangle_reference.read_text()) if a.triangle_reference else []
tpoints=np.array([r['points'] for r in trefs]);tcentres=tpoints.mean(1) if len(trefs) else []
def owner(x,z,kind,ref,trs=None,triangle=None):
 d=sorted((g.distance(Point(float(x),float(z))),i) for i,g in polys.items());resolved=None
 if d[1][0]-d[0][0]<=.01 and trs is not None:
  q=trs['R'].astype(float);q=q/32767 if np.max(np.abs(q))>2 else q
  hits={r['owner'] for r in refs if np.max(np.abs(np.asarray(r['T'])-trs['T']))<.05 and np.max(np.abs(np.asarray(r['S'])-trs['S']))<.001 and min(np.max(np.abs(np.asarray(r['R'])-q)),np.max(np.abs(np.asarray(r['R'])+q)))<.0005};assert len(hits)==1,('Ambiguous original instance',ref,hits);resolved=hits.pop();assert resolved in {i for distance,i in d if distance<.6}
 if d[1][0]-d[0][0]<=.01 and triangle is not None and len(trefs):
  candidates=np.where(np.max(np.abs(tcentres-triangle.mean(0)),axis=1)<.05)[0];hits={trefs[k]['owner'] for k in candidates if min(np.max(np.abs(np.roll(tpoints[k],shift,axis=0)-triangle)) for shift in range(3))<.05};assert len(hits)==1,('Ambiguous original triangle',ref,hits,triangle.tolist());resolved=hits.pop();assert resolved in {i for distance,i in d if distance<.6}
 assert d[0][0]<.6 and (d[1][0]-d[0][0]>.01 or resolved is not None),(kind,ref,d)
 if resolved is not None:d.sort(key=lambda row:row[1]!=resolved)
 audit.append({'kind':kind,'element':ref,'owner':d[0][1],'nearest_m':d[0][0],'runner_up_m':d[1][0],'resolved_by_bounded_generated_reference':resolved is not None});return d[0][1]
b=a.decoded.read_bytes();n=struct.unpack_from('<I',b,12)[0];j=json.loads(b[20:20+n]);blob=bytearray(b[28+n:]);assert not j.get('images');assert len(j['buffers'])==1
DT={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1',5120:'i1',5122:'<i2'};NC={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
def arr(i):
 ac=j['accessors'][i];v=j['bufferViews'][ac['bufferView']];dt=np.dtype(DT[ac['componentType']]);nc=NC[ac['type']];assert not ac.get('sparse');return np.ndarray((ac['count'],nc),dtype=dt,buffer=blob,offset=v.get('byteOffset',0)+ac.get('byteOffset',0),strides=(v.get('byteStride',dt.itemsize*nc),dt.itemsize)).copy()
def append(i,values):
 old=j['accessors'][i];values=np.asarray(values,dtype=DT[old['componentType']]);blob.extend(b'\0'*((-len(blob))%4));offset=len(blob);blob.extend(values.tobytes());vi=len(j['bufferViews']);j['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':values.nbytes});ac={k:v for k,v in old.items() if k not in ['bufferView','byteOffset','min','max']};ac.update(bufferView=vi,count=len(values));out=len(j['accessors']);j['accessors'].append(ac);return out
nodes=[];groups={i:[] for i in ids}
for ni,node in enumerate(copy.deepcopy(j['nodes'])):
 assert set(node)<= {'mesh','extensions','name'},'Unexpected baseline node transform'
 mesh=j['meshes'][node['mesh']];ins=node.get('extensions',{}).get('EXT_mesh_gpu_instancing')
 if ins:
  attrs={k:arr(v) for k,v in ins['attributes'].items()};owners=[owner(t[0],t[2],'instance',[ni,k],{'T':t,'R':attrs['ROTATION'][k],'S':attrs['SCALE'][k]}) for k,t in enumerate(attrs['TRANSLATION'])];tris=sum(j['accessors'][pr['indices']]['count']//3 for pr in mesh['primitives'])
  for i in ids:
   mask=np.array(owners)==i
   if not mask.any():continue
   new=copy.deepcopy(node);new['extensions']['EXT_mesh_gpu_instancing']['attributes']={k:append(ins['attributes'][k],v[mask]) for k,v in attrs.items()};groups[i].append(len(nodes));nodes.append(new);counts[i]+=int(mask.sum())*tris
 else:
  buckets={i:[] for i in ids}
  for pi,pr in enumerate(mesh['primitives']):
   idx=arr(pr['indices']).reshape(-1,3);verts=arr(pr['attributes']['POSITION']);centres=verts[idx].mean(1);owners=[owner(t[0],t[2],'triangle',[ni,pi,k],triangle=verts[idx[k]]) for k,t in enumerate(centres)]
   for i in ids:
    subset=idx[np.array(owners)==i]
    if not len(subset):continue
    new=copy.deepcopy(pr);new['indices']=append(pr['indices'],subset.reshape(-1,1));buckets[i].append(new);counts[i]+=len(subset)
  for i,prims in buckets.items():
   if not prims:continue
   mi=len(j['meshes']);j['meshes'].append({'primitives':prims});groups[i].append(len(nodes));nodes.append({'mesh':mi})
roots=[]
for i in ids:
 tag={'macro_id':MACRO,'landmark_id':ID,'local_ids':[i],'feature_keys':[features[i]['key']]} if i==LOCAL else None
 wrapper={'name':'city_target_'+ID if tag else 'preserved_'+str(i),'children':groups[i],'extras':{'cityReplacement':tag} if tag else {'cityPreservedLocalIds':[i]}}
 roots.append(len(nodes));nodes.append(wrapper)
j['nodes']=nodes;j['scenes']=[{'nodes':roots}];j['scene']=0;blob.extend(b'\0'*((-len(blob))%4));j['buffers']=[{'byteLength':len(blob)}];jb=json.dumps(j,separators=(',',':')).encode();jb+=b' '*((-len(jb))%4);raw=struct.pack('<4sII',b'glTF',2,28+len(jb)+len(blob))+struct.pack('<II',len(jb),0x4e4f534a)+jb+struct.pack('<II',len(blob),0x004e4942)+blob
a.out.mkdir(parents=True,exist_ok=True);(a.out/'partitioned.glb').write_bytes(raw);(a.out/'partitioned.glb.gz').write_bytes(gzip.compress(raw,mtime=0));assert sum(counts.values())==near['expandedTriangles'];report={'baseline_sha256':near['sha256'],'decoded_input_sha256':hashlib.sha256(b).hexdigest(),'output_sha256':hashlib.sha256(raw).hexdigest(),'triangles_by_source':counts,'assignment_method':__doc__,'assignments':audit,'instance_reference_sha256':hashlib.sha256(a.instance_reference.read_bytes()).hexdigest() if a.instance_reference else None,'triangle_reference_sha256':hashlib.sha256(a.triangle_reference.read_bytes()).hexdigest() if a.triangle_reference else None};(a.out/'partition.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'triangles':counts,'assignments':len(audit),'raw_bytes':len(raw)}))
