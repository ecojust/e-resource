#!/usr/bin/env python3
"""Bounded actual GLB reading: six F5 cap levels versus actual F6 paving."""
from pathlib import Path
import argparse,struct,json,hashlib
import numpy as np
ap=argparse.ArgumentParser();ap.add_argument('--raw',type=Path,required=True);ap.add_argument('--native-dir',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
b=a.raw.read_bytes();size=struct.unpack_from('<I',b,12)[0];d=json.loads(b[20:20+size]);buf=memoryview(b)[20+size+8:]
def array(ai):
 ac=d['accessors'][ai];bv=d['bufferViews'][ac['bufferView']];dt={5126:'<f4',5125:'<u4',5123:'<u2'}[ac['componentType']];k={'VEC3':3,'SCALAR':1}[ac['type']]
 return np.frombuffer(buf,dtype=dt,count=ac['count']*k,offset=bv.get('byteOffset',0)+ac.get('byteOffset',0)).reshape(ac['count'],k)
def desc(p):return {'file':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
records=[]
for m in d['meshes']:
 for pr in m['primitives']:
  wanted=[q for q in pr.get('extras',{}).get('semanticParts',[]) if q['label'].startswith('colonnade/F5/round-column-') or q['label']=='terrace/F6/colonnade-walking-surface']
  if not wanted:continue
  pos=array(pr['attributes']['POSITION']);ix=array(pr['indices']).ravel()
  for q in wanted:
   pts=pos[ix[q['firstIndex']:q['firstIndex']+q['indexCount']]];records.append({'label':q['label'],'actual_z_min_m':float(pts[:,1].min()),'actual_z_max_m':float(pts[:,1].max())})
assert len(records)==7
paving=next(r for r in records if 'walking-surface' in r['label']);caps=[r for r in records if 'round-column' in r['label']]
report={'schema':'library-actual-v1-colonnade-cap-coplanarity-v1','raw':desc(a.raw),'records':records,'six_caps_exactly_coplanar_with_paving_top':all(r['actual_z_max_m']==paving['actual_z_max_m'] for r in caps),'native_images_actually_viewed_by_author':[desc(a.native_dir/f'minhang-baoyugang-library-{v}.png') for v in ['full','rear']],'visual_observation':'Six regular dark round patches on upper terrace align with F5 column caps. Root independently confirmed and authorized lower cap termination inside deck.','measurement_scope':'Actual serialized FLOAT32 positions only; not source formula. No newraw or material change performed.','not_global_model_acceptance':True,'proposed_minimal_fix':'Only six F5 shaft cap levels20.98→20.70m; base/section/xy unchanged; verify actual newcap→deck positivevolume and positive clearance to paving.'}
a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'file':str(a.output),'sha256':hashlib.sha256(a.output.read_bytes()).hexdigest(),'caps':len(caps),'coplanar':report['six_caps_exactly_coplanar_with_paving_top']}))
