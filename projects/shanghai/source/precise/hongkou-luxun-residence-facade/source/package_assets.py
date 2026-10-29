"""Package source GLBs and a saved native file; never asserts acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess

ID='hongkou-luxun-residence-facade'
def document(path):
    data=path.read_bytes();length=struct.unpack_from('<I',data,12)[0]
    return json.loads(data[20:20+length])
def record(path):
    data=path.read_bytes();assert 0<len(data)<100_000_000
    result={'file':path.name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
    if path.suffix=='.glb':
        doc=document(path);result['triangles']=sum(doc['accessors'][p['indices']]['count']//3 for m in doc['meshes'] for p in m['primitives'])
    return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--raw',type=Path,required=True);parser.add_argument('--lod',type=Path,required=True);parser.add_argument('--native',type=Path,required=True);parser.add_argument('--out',type=Path,required=True);parser.add_argument('--gltfpack',required=True);a=parser.parse_args()
    a.out.mkdir(parents=True,exist_ok=True);assets={}
    for role,source,suffix in [('raw',a.raw,'-raw.glb'),('native',a.native,'.blend')]:
        dest=a.out/(ID+suffix)
        if source.resolve()!=dest.resolve():shutil.copyfile(source,dest)
        assets[role]=record(dest)
    for role,source,suffix in [('full',a.raw,'-web.glb'),('lod',a.lod,'-lod.glb')]:
        dest=a.out/(ID+suffix);subprocess.run([a.gltfpack,'-i',str(source),'-o',str(dest),'-cc','-noq','-vtf','-vnf','-km','-ke'],check=True)
        assets[role]=record(dest);assert assets[role]['triangles']==record(source)['triangles']
    manifest={'id':ID,'name':'上海鲁迅故居正立面与院门','status':'unregistered-front-component-candidate-not-installed','reference_period':'2010/2011 front photographs; not a claim about2026 condition','assets':assets,'estimated_dimensions_m':{'facade_width':5.5,'eaves_height':10.1,'fence_offset':2.5},'height_status':'Three storeys documented; ALL metric geometry estimated. Roof and whole-house shell omitted.','source_owner':None,'source_local_id':None,'map_replacement':False,'walk_integration':False,'photos_embedded':False,'textures':'Original procedural aggregate stone basecolor, normal and ORM; MIT','scope':'Front facade and gate component only; no roof, side/rear facade, interior or plants'}
    (a.out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(manifest,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
