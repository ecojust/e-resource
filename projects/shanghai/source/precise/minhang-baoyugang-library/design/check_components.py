"""Small CPU authoring-component smoke test; does not generate a model/raw/native."""
from pathlib import Path
import sys,json,hashlib
from collections import Counter
import numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P))
from build_model import Library,Facade,rect

def check(name,parts):
 bad=[];triangles=0
 for p in parts:
  v=np.asarray(p['vertices'],dtype=np.float32).astype(float);tri=p['triangles'];triangles+=len(tri);lookup={};ids=[]
  for xyz in v:
   key=tuple(xyz);lookup.setdefault(key,len(lookup));ids.append(lookup[key])
  edges=Counter();signed=0;small=0
  for face in tri:
   a,b,c=v[list(face)];signed+=np.dot(a,np.cross(b,c))/6
   if np.linalg.norm(np.cross(b-a,c-a))<1e-10:small+=1
   f=tuple(ids[j] for j in face)
   for a,b in zip(f,f[1:]+f[:1]):edges[tuple(sorted((a,b)))]+=1
  if signed<=1e-10 or small or any(n!=2 for n in edges.values()):bad.append({'label':p['label'],'volume_m3':signed,'small_triangles':small,'non_two_face_edges':sum(n!=2 for n in edges.values())})
 return {'component':name,'parts':len(parts),'triangles':triangles,'failure_count':len(bad),'failures':bad[:25]}
results=[]
l=Library();f=Facade(l.b,[-4,0],[4,0],'unit/slanted-facade');l.window_grid(f,rect(-2,5,2,7.4),1,'unit/tilted-glazing',True);results.append(check('one slanted opening/frame/reveal',l.b.parts))
l=Library();l.face(Facade(l.b,[-24,-14],[-17,-14],'unit/full-tilted-wall'),1);results.append(check('one complete slanted wall with real holes and clipped tile joints',l.b.parts))
l=Library();l.entry();results.append(check('entry curtain/doors/columns/curved glass canopy',l.b.parts))
l=Library();l.terraces();results.append(check('terrace decks/columns/rails/pergola',l.b.parts))
l=Library();l.west_returns_and_roof_raised_volume();results.append(check('open west return walls and raised roof volume',l.b.parts))
report={'schema':'library-bounded-component-source-check-v1','builder_sha256':hashlib.sha256((P/'build_model.py').read_bytes()).hexdigest(),'calibration_sha256':hashlib.sha256((P/'calibration.json').read_bytes()).hexdigest(),'scope':'Bounded construction methods in memory only; float32-rounded triangle edge counts/volumes for selected components. No complete model, GLB, native, independent contact audit or acceptance.','results':results,'component_checks_passed':all(r['failure_count']==0 for r in results)}
(P/'design/component-source-check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if not report['component_checks_passed']:raise SystemExit(1)
