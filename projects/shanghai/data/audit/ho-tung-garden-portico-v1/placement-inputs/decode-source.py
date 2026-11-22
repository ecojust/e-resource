"""Decode the three real near groups and the far original; measure the surviving source around the proposed portico."""
from pathlib import Path
from contextlib import ExitStack
from tempfile import TemporaryDirectory
from urllib.request import urlopen
import json,os,gzip,hashlib,subprocess,math,sys
import numpy as np
import shapely as g
from shapely.geometry import shape,box,LineString,Point
w=Path(__file__).parent;p=Path(__file__).resolve().parents[4];cfg=json.loads((w/'garden-face.json').read_bytes());anchor=cfg['checked_source_frame']['anchor']
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
    cent=g.points(t[:,:,:2].mean(axis=1));ds=np.stack([g.distance(cent,polygons[int(i)])for i in ids],axis=1);owner=ids[ds.argmin(axis=1)];gaps=np.partition(ds,1,axis=1);lowest=float(np.min(gaps[:,1]-gaps[:,0]))
   else:owner=load('owners.u32',np.uint32);lowest=None
   yield role,t,owner,lowest
def main():
 site=box(-5.15,-.4,5.15,4.3);boundary=polygons[1292];ap=boundary.intersection(site);ids={1292,*cfg['checked_neighbors']};counts={};context=[]
 for group in cfg['groups']:
  detail={}
  for role,tri,owners,gap in decode(group):
   detail[role]=dict(decoded=len(tri),source_owner_inference_minimum_gap_m=gap)
   for ident in sorted(ids.intersection(group['owners'])):
    use=tri[owners==ident];assert len(use);high=float(use[:,:,2].max())
    upper=use[np.min(use[:,:,2],axis=1)>high-.16]
    assert len(upper)
    roof=g.union_all(g.polygons(upper[:,:,:2]));roof=g.make_valid(roof)
    touch=g.intersection(roof,site);area=float(g.area(touch))
    record=dict(triangles=len(use),top_z=high,roof_area=float(g.area(roof)),roof_within_cut=area,roof_outside_cut=float(g.area(roof.difference(site))),source_group=group['id'])
    if ident==1292:
     assert high>29.49 and 38<area<47 and record['roof_outside_cut']>500
     facade=[[-5.15,float(polygons[1292].boundary.intersection(LineString([(-5.15,-1),(-5.15,1)])).y)],[5.15,float(polygons[1292].boundary.intersection(LineString([(5.15,-1),(5.15,1)])).y)]]
     record['footprint_facade_line_local']=facade
     def front(x):
      cut=roof.intersection(LineString([(x,-2),(x,3)]))
      assert not cut.is_empty
      return [x,float(cut.bounds[1])]
     record['actual_roof_front_line_local']=[front(x)for x in [-5.15,0.0,5.15]]
    else:assert area<1e-7 and polygons[ident].distance(site)>0
    counts.setdefault(str(ident),{})[role]=record
  context.append(dict(group=group['id'],**detail))
 assert len(counts)==14 and all(set(r)=={'near','far'} for r in counts.values())
 a=math.degrees(theta)%360
 result=dict(order=326,owner=1292,anchor=anchor,heading=a,source_macro='14-13719-6694',cut_local=list(site.exterior.coords),provisional_source_cut=True,nominal_cut_area=site.area,city_footprint_area=boundary.area,original_intersection_area=ap.area,three_section_segments_local=[list(LineString([[-5.15,4.3],[5.15,4.3]]).coords),[[-5.15,4.3],counts['1292']['near']['actual_roof_front_line_local'][0]],[[5.15,4.3],counts['1292']['near']['actual_roof_front_line_local'][2]]],negative_neighbor_ids=cfg['checked_neighbors'],all_14_owners=counts,groups=context)
 (w/'original-near-far.json').write_text(json.dumps(result,indent=2)+'\n')
 print('source',counts['1292'],'near/far neighbor checks',len(counts)-1,flush=True)
if __name__=='__main__':main()
