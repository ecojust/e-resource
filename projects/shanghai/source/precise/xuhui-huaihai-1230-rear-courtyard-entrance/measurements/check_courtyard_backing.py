from pathlib import Path
from itertools import product
import argparse,hashlib,json,struct
import numpy as np
pa=argparse.ArgumentParser();pa.add_argument('mesh',type=Path);pa.add_argument('measurements',type=Path);pa.add_argument('out',type=Path);args=pa.parse_args()
data=args.mesh.read_bytes();n=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+n]);off=28+n
def acc(i):
 a=doc['accessors'][i];b=doc['bufferViews'][a['bufferView']];nt={'VEC3':3,'SCALAR':1}[a['type']]
 return np.frombuffer(data,{5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']],count=a['count']*nt,offset=off+b.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,nt)
shapes=[]
for p in doc['meshes'][0]['primitives']:
 mat=doc['materials'][p['material']]['name']
 if mat.startswith('1230 attachments'):continue
 xyz=acc(p['attributes']['POSITION'])[:,[0,2,1]].copy();xyz[:,1]*=-1
 shapes.append((mat,xyz[acc(p['indices']).reshape(-1,3)]))
def cast(x,z):
 res=[]
 for mat,t in shapes:
  a,b,c=t[:,0],t[:,1]-t[:,0],t[:,2]-t[:,0];den=b[:,0]*c[:,2]-c[:,0]*b[:,2];good=np.abs(den)>1e-7
  U=( (x-a[:,0])*c[:,2]-(z-a[:,2])*c[:,0])/np.where(good,den,1)
  V=(b[:,0]*(z-a[:,2])-b[:,2]*(x-a[:,0]))/np.where(good,den,1)
  y=a[:,1]+b[:,1]*U+c[:,1]*V;ok=good&(U>=0)&(V>=0)&(U+V<=1)&(y>=-.70)
  if np.any(ok):res.append((float(y[ok].min()),mat))
 return sorted(res)[0] if res else None
measure=json.loads(args.measurements.read_bytes());rows=[]
for item in measure['condenser_cases']:
 l,base,r,top=item['bounds_x0_z0_x1_z1']; fractions=(.22,.45) if item['name']=='west-of-portal' else (.22,.80);xx=[l+(r-l)*f for f in fractions]
 rows.append(dict(name=item['name'],xz=[[round(x,3),round(base+.03,3)]for x in xx],backing=[cast(x,base+.03)for x in xx]))
points=[]
for row in measure['cages']:
 l,base,r,top=row['bounds_x0_z0_x1_z1']
 for x in np.linspace(l,r if row['name']=='west-partial' else 4.078,12):
  points.append(dict(cage=row['name'],x=round(float(x),3),backing=[cast(x,h) for h in [base+.08,(base+top)/2,top-.06]]))
out=dict(source_sha256=hashlib.sha256(data).hexdigest(),condenser_supports=rows,guard_sections=points);args.out.write_text(json.dumps(out,indent=2)+'\n')
print([(r['name'],r['backing'])for r in rows]); print([(r['x'],r['backing'][1])for r in points])
