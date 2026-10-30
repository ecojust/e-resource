"""Package source GLBs and a saved native file; never asserts acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess

ID='hongkou-russian-consulate'
def document(path):
    data=path.read_bytes();length=struct.unpack_from('<I',data,12)[0]
    return json.loads(data[20:20+length])
def preserve_candidate_metadata(path,source):
    # gltfpack omits top-level extras even with -ke. Preserve the independently
    # named candidate and its limits without changing any packed mesh bytes.
    data=path.read_bytes();old_length=struct.unpack_from('<I',data,12)[0]
    doc=json.loads(data[20:20+old_length]);doc['extras']=document(source)['extras']
    payload=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode('utf-8')
    payload+=b' '*((-len(payload))%4)
    tail=data[20+old_length:]
    path.write_bytes(struct.pack('<4sII',b'glTF',2,20+len(payload)+len(tail))+struct.pack('<II',len(payload),0x4E4F534A)+payload+tail)
def record(path):
    data=path.read_bytes();assert 0<len(data)<100_000_000
    result={'file':path.name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
    if path.suffix=='.glb':
        doc=document(path)
        def count_node(i):
            node=doc['nodes'][i];own=sum(doc['accessors'][q['indices']]['count']//3 for q in doc['meshes'][node['mesh']]['primitives']) if 'mesh' in node else 0
            return own+sum(count_node(c) for c in node.get('children',[]))
        result['triangles']=sum(count_node(i) for i in doc['scenes'][doc.get('scene',0)]['nodes'])
    return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--raw',type=Path,required=True);parser.add_argument('--lod',type=Path,required=True);parser.add_argument('--native',type=Path,required=True);parser.add_argument('--out',type=Path,required=True);parser.add_argument('--gltfpack',required=True);a=parser.parse_args()
    a.out.mkdir(parents=True,exist_ok=True);assets={}
    for role,source,suffix in [('raw',a.raw,'-raw.glb'),('native',a.native,'.blend')]:
        dest=a.out/(ID+suffix)
        if source.resolve()!=dest.resolve():shutil.copyfile(source,dest)
        assets[role]=record(dest)
    for role,source,suffix in [('full',a.raw,'-web.glb'),('lod',a.lod,'-lod.glb')]:
        dest=a.out/(ID+suffix);subprocess.run([a.gltfpack,'-i',str(source),'-o',str(dest),'-cc','-noq','-vnf','-km','-kn','-ke'],check=True)
        preserve_candidate_metadata(dest,source)
        assets[role]=record(dest);assert assets[role]['triangles']==record(source)['triangles']
    manifest = {'id':ID,'name':'俄罗斯领事馆历史主楼外观候选','status':'standalone-exterior-candidate-not-geographically-registered','dimensions_all_estimated':True,'estimated_body_width_depth_m':[44,24],'estimated_total_height_m':30.8,'four_storeys_text_reference':True,'storey_mapping_verified':False,'photograph_period':'2010-05','chronology_unresolved':[1916,1917],'garden_pavilion_modeled':False,'map_replacement':False,'walk_integration':False,'photos_embedded':False,'complete_photo_reconstruction_accepted':False,'estimated':'Overall scale, windows, rear/side facades, balconies, roof pitch, gable silhouette, tower position and eightfold lantern geometry. Main visible composition guided by2010 photograph.'}
    manifest['assets']=assets
    (a.out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(manifest,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
