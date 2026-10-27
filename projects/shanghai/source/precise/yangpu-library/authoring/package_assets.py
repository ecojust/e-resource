#!/usr/bin/env python3
"""Lossless-position Meshopt package; --root points to this model development directory.
Preserves authored geometry; native generation is a separate Blender step.
"""
from pathlib import Path
import argparse,json,struct,hashlib,subprocess
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):
 b=Path(p).read_bytes();size,kind=struct.unpack_from('<II',b,12);assert kind==0x4e4f534a
 return json.loads(b[20:20+size]),b[20+size:]
def save(p,doc,tail):
 data=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode();data+=b' '*((-len(data))%4)
 Path(p).write_bytes(struct.pack('<4sII',b'glTF',2,20+len(data)+len(tail))+struct.pack('<II',len(data),0x4e4f534a)+data+tail)
def record(p,triangles=None):return {'path':str(p.resolve()),'bytes':p.stat().st_size,'sha256':sha(p),**({'triangles':triangles} if triangles is not None else {})}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--gltfpack',type=Path,required=True);a=ap.parse_args();out=a.root/'package-v6'
 if out.exists():raise ValueError('Use fresh package directory')
 out.mkdir();assets={};notes=[]
 for label,folder in [('raw','full-v6'),('lod_source','lod-v6')]:
  source=a.root/folder/'yangpu-library.glb';doc,tail=load(source)
  # Correct a legacy field name only; the geometry/BIN bytes remain unchanged.
  doc['extras']={('lod_authored_simplification' if k=='lod_authored_subtraction' else k):v for k,v in doc['extras'].items()}
  dest=out/('yangpu-library-raw.glb' if label=='raw' else 'yangpu-library-lod-source.glb');save(dest,doc,tail)
  assert load(dest)[1]==tail
  triangles=sum(doc['accessors'][p['indices']]['count']//3 for m in doc['meshes'] for p in m['primitives']);assets[label]=record(dest,triangles)
  notes.append({'source':str(source),'source_sha256':sha(source),'dest_sha256':sha(dest),'geometry_tail_byte_identical':True,'change':'Normalize legacy LOD field when present; current authored source already uses lod_authored_simplification'})
 for role,source_role in [('web','raw'),('lod','lod_source')]:
  source=Path(assets[source_role]['path']);dest=out/f'yangpu-library-{role}.glb';report=out/f'{role}-gltfpack.json'
  cmd=[str(a.gltfpack),'-i',str(source),'-o',str(dest),'-cc','-noq','-km','-ke','-r',str(report)]
  subprocess.run(cmd,check=True,capture_output=True,text=True)
  original,_=load(source);packed,tail=load(dest);packed['extras']=original['extras'];packed['asset']['copyright']=original['asset']['copyright'];save(dest,packed,tail)
  triangles=sum(packed['accessors'][p['indices']]['count']//3 for m in packed['meshes'] for p in m['primitives']);assert triangles==assets[source_role]['triangles']
  assets[role]=record(dest,triangles)
  assert dest.stat().st_size<100000000
 r={'assets':assets,'geometry_metadata_correction':notes,'gltfpack':str(a.gltfpack),'gltfpack_sha256':sha(a.gltfpack),'parameters':['-cc','-noq','-km','-ke'],'independent_decoded_verification_passed':False,'raw_lod_policy':'Remove stone joints/fluting, reduce tile repetitions/curve sampling; preserve main structure/true window and door openings. Authored simplification, not an exact triangle subset.'}
 (out/'packaging.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(assets))
if __name__=='__main__':main()
