"""Package source GLBs and a saved native file; never asserts acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess

ID='huangpu-sun-yatsen-residence'
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
    manifest={'id':ID,'name':'上海孙中山故居主楼','status':'source-anchored-exterior-candidate-not-installed','reference_period':'2015/2017 facade and 2020 aerial photographs; not a claim about 2026 condition','assets':assets,'estimated_dimensions_m':{'body':[17.6,16.4],'main_ridge':11.7,'maximum_chimney':12.975},'height_status':'Two storeys documented; all metric geometry, hidden faces and steps estimated. Baseline inferred 20.45m height not used.','source_owner':'building:9bbed57b-ae4b-4abc-be77-0b5444bf0a9a','source_local_id':3433,'map_replacement':False,'walk_integration':False,'photos_embedded':False,'textures':'Original procedural pebbledash basecolor, normal and ORM; MIT'}
    (a.out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(manifest,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
