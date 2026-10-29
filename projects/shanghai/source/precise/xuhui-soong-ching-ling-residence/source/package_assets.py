"""Package source GLBs and a saved native file; never asserts acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess

ID='xuhui-soong-ching-ling-residence'
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
    manifest={'id':ID,'name':'上海宋庆龄故居主楼','status':'unregistered-main-house-exterior-candidate-not-installed','reference_period':'2013/2016/2019 photographs; not a claim about2026 condition','assets':assets,'estimated_dimensions_m':{'body':[22,14],'eaves':7.7,'main_ridge':11.0,'maximum_pipe':13.28},'height_status':'Two storeys documented; ALL metric geometry, roof curvature, hidden surfaces and details estimated. Baseline heights not used.','source_owner':None,'source_local_id':None,'map_replacement':False,'walk_integration':False,'photos_embedded':False,'textures':'Original procedural pebbledash basecolor, normal and ORM; MIT','scope':'Main house only; hidden sides/rear simplified; no annex, garden, interior or exact historic insignia'}
    (a.out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(manifest,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
