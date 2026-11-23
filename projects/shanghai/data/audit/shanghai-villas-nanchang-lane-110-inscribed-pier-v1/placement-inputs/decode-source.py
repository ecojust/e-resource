"""Decode the near groups and far original around the photographed street entrance."""
from pathlib import Path
from contextlib import ExitStack
from tempfile import TemporaryDirectory
from urllib.request import urlopen
import json,os,gzip,hashlib,subprocess,math,sys
import numpy as np
import shapely as g
from shapely.geometry import shape,box,LineString,Point
w=Path(__file__).parent;p=next(p for p in Path(__file__).resolve().parents if (p/'tools/package_architectural_model.py').is_file());cfg=json.loads((w/'portal-frame.json').read_bytes());anchor=cfg['checked_source_frame']['anchor']
theta=math.radians(cfg['runtime_heading_degrees']);c,s=math.cos(theta),math.sin(theta);axes=np.array([[c,-s],[s,c]])
rad=6371008.8*math.cos(math.radians(anchor['lat']));t0=math.asinh(math.tan(math.radians(anchor['lat'])))
def loc(coords):
 arr=np.column_stack((rad*np.radians(coords[:,0]-anchor['lng']),rad*(np.arcsinh(np.tan(np.radians(coords[:,1])))-t0)))
 return arr@axes.T
def take(name,expected):
 with urlopen(cfg['origin']+name,timeout=60)as r:b=r.read();assert r.status==200 and hashlib.sha256(b).hexdigest()==expected
 return b
hashes={r['repository_path'].rsplit('/',1)[-1]:r['sha256'] for r in cfg['source_hashes']}
table=json.loads(gzip.decompress(take('feature-table.json.gz',hashes['feature-table.json.gz'])))['features'];polygons={r['localId']:g.transform(shape(r['geometry']),loc) for r in table};far=take('far.glb',hashes['far.glb'])
def decode(group):
 with TemporaryDirectory()as directory,ExitStack()as stack:
  d=Path(directory)
  def mem(name,data=b''):
   fd=os.memfd_create(name);stack.callback(os.close,fd)
   with os.fdopen(fd,'wb',closefd=False)as out:out.write(data)
   (d/name).symlink_to('/proc/'+str(os.getpid())+'/fd/'+str(fd));return fd
  mem('baseline-far.glb',far);mem('baseline-near.glb.gz',take(group['file'],group['sha256']))
  mem('macro-READY.json',json.dumps(dict(zip(('origin_longitude','origin_latitude'),cfg['macro_origin']))).encode())
  mem('initial-local-frame.json',json.dumps({'anchor':anchor}).encode());mem('context-features.json',json.dumps([{'localId':i} for i in group['owners']]).encode())
  output={(k,n):mem(f'baseline-{k}-{n}') for k in ('near','far') for n in ('owners.u32','triangles.f64')};mem('source-decode.json')
  subprocess.run(['node',p/'data/audit/postal-office-v1/map-decode-source.mjs'],check=True,env={**os.environ,'POSTAL_MAPPING_WORK':str(d)},stdout=subprocess.DEVNULL)
  for role in ['near','far']:
   def load(n,dtype):
    fd=output[role,n];return np.frombuffer(os.pread(fd,os.fstat(fd).st_size,0),dtype)
   t=load('triangles.f64',np.float64).copy().reshape(-1,3,3);t[:,:,:2]=t[:,:,:2]@axes.T
   ids=np.asarray(group['owners'])
   if role=='near':
    assert len(t)==group['triangles']
    cent=g.points(t[:,:,:2].mean(axis=1));ds=np.stack([g.distance(cent,polygons[int(i)])for i in ids],axis=1);owner=ids[ds.argmin(axis=1)];lowest=None if len(ids)==1 else float(np.diff(np.partition(ds,1,axis=1)[:,:2],axis=1).min())
   else:owner=load('owners.u32',np.uint32);lowest=None
   yield role,t,owner,lowest
