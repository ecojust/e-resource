#!/usr/bin/env python3
"""Check precise scope/UV retention and accepted front glass gaps.

Optional baseline arguments point to the separately preserved historical stage;
no baseline file is edited. This is numeric proof, not a visual acceptance.
"""
from pathlib import Path
from collections import defaultdict
import argparse,hashlib,importlib.util,json,struct,tempfile
import numpy as np
from build_model import build,HERE
PREVIOUS='77a72f8737f7e3b9afbffb9adf6e4e199d10cfe7af2d10cf0ab57afeb623ac31'

def glb(path):
 b=path.read_bytes();n=struct.unpack_from('<I',b,12)[0];j=json.loads(b[20:20+n]);start=28+n;return b,j,b[start:]
def accessor(j,b,i):
 a=j['accessors'][i];v=j['bufferViews'][a['bufferView']];width={'SCALAR':1,'VEC2':2,'VEC3':3}[a['type']]*{5125:4,5126:4}[a['componentType']];start=v.get('byteOffset',0)+a.get('byteOffset',0);assert not v.get('byteStride');return b[start:start+a['count']*width]
def photo_primitive(j):
 ps=[p for mesh in j['meshes'] for p in mesh['primitives'] if j['materials'][p['material']]['name']=='PhotoFacade_Bund07_RegisteredGlass'];assert len(ps)==1;return ps[0]
def part_key(p):
 return hashlib.sha256(json.dumps({k:p[k] for k in ['material','vertices','triangles']},sort_keys=True,separators=(',',':')).encode()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--baseline-source',type=Path);p.add_argument('--baseline-glb',type=Path);a=p.parse_args()
 B,r=build(HERE/'output');geo=json.loads((HERE/'geometry-input.json').read_text());poly=np.array(geo['polygon_local_east_north']);origin=(poly[3]+poly[4])/2;t=(poly[4]-poly[3]);t/=np.linalg.norm(t);n=np.array([t[1],-t[0]])
 checked=[]
 for part in B.parts:
  label=part['label'];mat=part['material']
  if label.startswith('edge-3/') and ('glass' in mat.lower() or mat.startswith('PhotoFacade_')):
   d=(np.array(part['vertices'])[:,:2]-origin)@n;expected=[.155,.175] if 'oculus-glass' in label else [-.20,-.18]
   assert np.allclose([d.min(),d.max()],expected,atol=1e-8),(label,d.min(),d.max())
   checked.append({'label':label,'actual_depth_m':[float(d.min()),float(d.max())]})
 report={'schema':'bund07-visual-refinement-scope-check-v1','passed':True,'new_raw_sha256':r['sha256'],'new_raw_bytes':r['bytes'],'new_triangles':r['triangles'],'front_glass_solids_checked':len(checked),'front_glass_depths':checked,'previous_raw_sha256':PREVIOUS,'baseline_comparison_performed':False,'numerical_audit_is_not_visual_acceptance':True}
 if a.baseline_glb:
  old,oj,ob=glb(a.baseline_glb);new,nj,nb=glb(HERE/'output/bund07.glb');assert hashlib.sha256(old).hexdigest()==PREVIOUS
  op=photo_primitive(oj);np0=photo_primitive(nj);keys=['POSITION','NORMAL','TEXCOORD_0'];same={k:accessor(oj,ob,op['attributes'][k])==accessor(nj,nb,np0['attributes'][k]) for k in keys};same['indices']=accessor(oj,ob,op['indices'])==accessor(nj,nb,np0['indices']);assert all(same.values());report['photo_18_pane_accessor_bytes_unchanged']=same
 if a.baseline_source:
  spec=importlib.util.spec_from_file_location('bund07_frozen_baseline',a.baseline_source);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
  with tempfile.TemporaryDirectory(prefix='bund07-baseline-audit-') as tmp:old,_=mod.build(Path(tmp))
  oldmap=defaultdict(list);newmap=defaultdict(list)
  for part in old.parts:oldmap[part['label']].append(part_key(part))
  for part in B.parts:newmap[part['label']].append(part_key(part))
  allow=('edge-3/front-ground-center-','edge-3/front-ground-end-','edge-3/approximate-observed-winged-crest','edge-3/crest-gold-relief','edge-3/bank-crest-','edge-3/bank-Thai-sign/','corner-roof-drum-','corner-drum-top-slab','closed-rounded-rectangular-metal-cap','roof-cap-standing-seam','setback-roof-front/','setback-','estimated-setback-roof-top')
  diff=[k for k in sorted(set(oldmap)|set(newmap)) if oldmap[k]!=newmap[k]];unexpected=[k for k in diff if not k.startswith(allow)];assert not unexpected,unexpected
  report.update({'baseline_comparison_performed':True,'unchanged_part_label_groups':sum(oldmap[k]==newmap[k] for k in set(oldmap)&set(newmap)),'unchanged_old_part_count':sum(len(oldmap[k]) for k in oldmap if oldmap[k]==newmap[k]),'changed_label_groups':diff,'allowed_change_prefixes':allow,'unexpected_changed_labels':unexpected})
 (HERE/'output/visual-refinement-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['front_glass_depths','changed_label_groups','allowed_change_prefixes']},indent=2))
if __name__=='__main__':main()
