#!/usr/bin/env python3
"""Compare actual serialized parts with the frozen3325262c visual candidate.

All non-target POSITION/NORMAL/UV triangle arrays must remain byte-identical.
"""
from pathlib import Path
import argparse,hashlib,json,struct
import numpy as np
HERE=Path(__file__).resolve().parent
EXPECTED='3325262c62958cbfeb5a1ad07e19c42b1644b0b0e1a654558204e7d68562c832'
TARGETS={'edge-3/front-ground-end--10.50-frame-grid','edge-3/front-ground-end-+10.50-frame-grid'}

def read(path):
 raw=path.read_bytes();assert len(raw)<100_000_000;magic,version,total=struct.unpack_from('<4sII',raw);assert (magic,version,total)==(b'glTF',2,len(raw));jl,jt=struct.unpack_from('<II',raw,12);assert jt==0x4e4f534a;doc=json.loads(raw[20:20+jl]);bl,bt=struct.unpack_from('<II',raw,20+jl);assert bt==0x004e4942;return raw,doc,raw[28+jl:28+jl+bl]
def acc(doc,binary,i):
 a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']];assert not v.get('byteStride');width={'SCALAR':1,'VEC2':2,'VEC3':3}[a['type']];return np.frombuffer(binary,dtype={5125:'<u4',5126:'<f4'}[a['componentType']],count=a['count']*width,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,width)
def parts(doc,binary,summary):
 out={}
 for prim in doc['meshes'][0]['primitives']:
  material=doc['materials'][prim['material']]['name'];ix=acc(doc,binary,prim['indices']).ravel();data={k:acc(doc,binary,v)[ix] for k,v in prim['attributes'].items()};offset=0
  for idx,p in enumerate(summary):
   if p['material']!=material:continue
   count=p['triangles']*3;out[idx]={'label':p['label'],'material':material,'data':{k:v[offset:offset+count].tobytes() for k,v in data.items()}};offset+=count
  assert offset==len(ix)
 return out

def main():
 p=argparse.ArgumentParser();p.add_argument('--baseline-dir',type=Path,required=True);a=p.parse_args();old=a.baseline_dir/'output';new=HERE/'output';oraw,od,ob=read(old/'bund07.glb');nraw,nd,nb=read(new/'bund07.glb');assert hashlib.sha256(oraw).hexdigest()==EXPECTED
 assert od['materials']==nd['materials'];assert od['nodes']==nd['nodes'];assert od['scenes']==nd['scenes'];assert od['asset']['copyright']==nd['asset']['copyright']
 for key in ['geometry_input_sha256','calibration_sha256','anchor','front_width_m','raised_sign_lettering','photographic_glazing','glass_frame_fit']:assert od['extras'][key]==nd['extras'][key],key
 os=json.loads((old/'bund07.geometry.json').read_text())['part_summary'];ns=json.loads((new/'bund07.geometry.json').read_text())['part_summary'];assert len(os)==len(ns)
 op=parts(od,ob,os);np0=parts(nd,nb,ns);changed=[];unchanged=0;photo=0
 for idx in range(len(os)):
  x,y=op[idx],np0[idx];assert x['label']==y['label'] and x['material']==y['material']
  if x['data']!=y['data']:changed.append(x['label']);assert x['label'] in TARGETS
  else:unchanged+=1
  if 'TEXCOORD_0' in x['data']:assert x['data']==y['data'];photo+=1
 assert set(changed)==TARGETS and len(changed)==2
 images=[]
 for d,b in [(od,ob),(nd,nb)]:
  assert len(d['images'])==1 and 'uri' not in d['images'][0];v=d['bufferViews'][d['images'][0]['bufferView']];images.append(b[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']])
 assert images[0]==images[1]
 report={'schema':'bund07-v3-two-arch-grid-serialized-invariance-v1','passed':True,'previous_raw_sha256':EXPECTED,'new_raw_sha256':hashlib.sha256(nraw).hexdigest(),'new_raw_bytes':len(nraw),'parts_total':len(os),'unchanged_non_target_parts':unchanged,'changed_parts':changed,'proof':'Each actual glTF primitive was expanded by indices then split using exact material-ordered part triangle counts. All non-target expanded POSITION/NORMAL/TEXCOORD0 bytes are identical. No source-position-only substitute.','photo_panes_unchanged':photo,'original_embedded_jpeg_sha256':hashlib.sha256(images[1]).hexdigest(),'materials_nodes_scene_copyright_unchanged':True,'geometry_input_calibration_anchor_unchanged':True,'bounds_unchanged':json.loads((old/'bund07.geometry.json').read_text())['bounds_glb']==json.loads((new/'bund07.geometry.json').read_text())['bounds_glb'],'visual_limit':'4x4 source frame count corrected; blind slats remain unmodeled and no post-v3 render acceptance is claimed here.'}
 assert report['bounds_unchanged'];(new/'arch-grid-revision-check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
