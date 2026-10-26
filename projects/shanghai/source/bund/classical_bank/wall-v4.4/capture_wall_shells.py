"""Capture only original Builder.bay structural faces, match frozen photo native."""
import bpy,sys,argparse,json,hashlib,importlib.util,numpy as np
from pathlib import Path
from collections import defaultdict,Counter
P=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--project',required=True,type=Path);ap.add_argument('--input',required=True,type=Path);ap.add_argument('--building',choices=['bund12','bund15'],default='bund12');ap.add_argument('--output',type=Path,default=P/'captured-wall-shells.json');args=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);R=args.project
spec=importlib.util.spec_from_file_location('bank_source',R/'source/bund/classical_bank/build_classical_banks.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s);G=json.loads((R/'source/bund/classical_bank/geometry-input.json').read_text())[args.building]
class Capture(s.Builder):
 def __init__(self):super().__init__();self.shells=[];self.active=None;self.capture_secondary=False
 def bay(self,*a,**kw):
  self.active={'source_kind':'bay','face_start':len(self.faces),'origin':list(self.origin),'u':list(self.u),'v':list(self.v),'bay_args':list(a),'bay_kwargs':kw,'front_y':a[2] if len(a)>2 else kw['y'],'depth':.62}
  super().bay(*a,**kw);assert 'face_end' in self.active;self.shells.append(self.active);self.active=None
 def box(self,x,y,z,w,d,h,mat=0):
  start=len(self.faces);origin=list(self.origin);u=list(self.u);v=list(self.v)
  super().box(x,y,z,w,d,h,mat)
  if self.capture_secondary and self.active is None and mat==0 and abs(d-.62)<1e-8 and len(self.faces)>start:
   self.shells.append({'source_kind':'solid_secondary_wall','face_start':start,'face_end':len(self.faces),'origin':origin,'u':u,'v':v,'bay_args':[x,w,y-d/2,z-h/2,z+h/2],'bay_kwargs':{},'front_y':y-d/2,'depth':d})
 def window(self,*a,**kw):
  if self.active is not None and 'face_end' not in self.active:self.active['face_end']=len(self.faces)
  return super().window(*a,**kw)
original_other_walls=s.roof_and_other_walls
def capture_other_walls(b,*a,**kw):
 b.capture_secondary=True
 try:return original_other_walls(b,*a,**kw)
 finally:b.capture_secondary=False
s.roof_and_other_walls=capture_other_walls
b=Capture();(s.hsbc if args.building=='bund12' else s.russo)(b,G)
u=G['world_basis_u'];v=G['world_basis_v']
def baked(pt):
 x,y,z=np.array(pt,dtype=np.float32);return tuple(float(c) for c in np.array((u[0]*float(x)+v[0]*float(y),u[1]*float(x)+v[1]*float(y),z),dtype=np.float32))
def key(vs):
 vv=[tuple(float(c) for c in p) for p in vs];return min(tuple(vv[i:]+vv[:i]) for i in range(len(vv)))
world=[baked(p) for p in b.verts]
bpy.ops.wm.open_mainfile(filepath=str(args.input));O=bpy.data.objects['HSBC Bund 12' if args.building=='bund12' else 'Russo Chinese Bank Bund 15'];old=O.data;lookup=defaultdict(list)
for f in old.polygons:
 if f.material_index==0:lookup[key([old.vertices[i].co for i in f.vertices])].append(f.index)
removed=[];records=[]
for i,sh in enumerate(b.shells):
 U=np.array(sh['u']);V=np.array(sh['v']);origin=np.array(sh['origin']);offset=float(origin@V+sh['front_y']);front=[];face_ids=[]
 for fi in range(sh['face_start'],sh['face_end']):
  assert b.material[fi]==0
  face=b.faces[fi];k=key([world[j] for j in face]);assert lookup.get(k),(i,fi,'source wall face not found exactly in native');native_id=lookup[k].pop();face_ids.append(native_id);removed.append(native_id)
  vs=np.array([b.verts[j] for j in face],float)
  if np.max(np.abs(vs[:,:2]@V-offset))<1e-7:
   # Original exposed front patches, including the polygonal arch spandrels.
   front.append(np.column_stack([vs[:,:2]@U,vs[:,2]]).tolist())
 assert front,(i,'no front found')
 records.append({'source_bay':i,'source_kind':sh['source_kind'],'origin':sh['origin'],'u':sh['u'],'v':sh['v'],'front_plane_offset':offset,'depth':sh['depth'],'front_polygons':front,'old_face_ids':face_ids,'bay_args':sh['bay_args']})
assert len(removed)==len(set(removed));report={'input_native':args.input.name,'input_native_sha256':hashlib.sha256(args.input.read_bytes()).hexdigest(),'source_generator_sha256':hashlib.sha256((R/'source/bund/classical_bank/build_classical_banks.py').read_bytes()).hexdigest(),'geometry_input_sha256':hashlib.sha256((R/'source/bund/classical_bank/geometry-input.json').read_bytes()).hexdigest(),'world_basis_u':u,'world_basis_v':v,'matched_face_count':len(removed),'native_face_count':len(old.polygons),'native_vertex_count':len(old.vertices),'building':args.building,'bay_count':sum(r['source_kind']=='bay' for r in records),'solid_wall_count':sum(r['source_kind']!='bay' for r in records),'all_source_wall_faces_match_native_exactly':True,'shells':records}
args.output.write_text(json.dumps(report,ensure_ascii=False,separators=(',',':'))+'\n');print('CAPTURED',len(records),'bays',len(removed),'native faces exact')
