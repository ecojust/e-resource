"""Web and distant LOD generation; preserve architectural and spatial provenance."""
import argparse, subprocess, json, struct
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--input',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--gltfpack',default='gltfpack');a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True)
b=a.input.read_bytes();length,_=struct.unpack_from('<II',b,12);source=json.loads(b[20:20+length]);copyright=source['asset']['copyright']
for name,extra in [('bund15-curtain-web.glb',[]),('bund15-curtain-lod.glb',['-si','0.35','-se','0.002','-sp'])]:
 path=a.output/name
 subprocess.run([a.gltfpack,'-i',str(a.input),'-o',str(path),'-cc','-noq','-km','-ke',*extra],check=True)
 # gltfpack 1.3 drops asset-level copyright/extras even with -ke. Restore both stages explicitly.
 data=path.read_bytes();n,_=struct.unpack_from('<II',data,12);doc=json.loads(data[20:20+n]);doc['asset'].update({k:v for k,v in source['asset'].items() if k not in ['version','generator']})
 encoded=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode();encoded+=b' '*((-len(encoded))%4)
 tail=data[20+n:]
 final=struct.pack('<III',0x46546c67,2,12+8+len(encoded)+len(tail))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+tail
 assert len(final)<100_000_000
 path.write_bytes(final)
 print(path.name,len(final))
