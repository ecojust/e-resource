"""Package source GLBs and a saved native file; never asserts acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess

ID='chongming-ruxue-gate'
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
        dest=a.out/(ID+suffix);subprocess.run([a.gltfpack,'-i',str(source),'-o',str(dest),'-cc','-noq','-vnf','-km','-ke'],check=True)
        preserve_candidate_metadata(dest,source)
        assets[role]=record(dest);assert assets[role]['triangles']==record(source)['triangles']
    manifest = {
        'id':ID,'name':'崇明学宫儒学大门（文字尺寸参照候选）','status':'standalone-text-dimension-candidate-not-geographically-registered',
        'assets':assets,
        'source_dimensions_m':{'length':10.7,'width':8.8,'height':8.0,'interpreted_local_base':[10.7,8.8]},
        'area_m2':{'museum_reported':94,'calculated_length_times_width':94.16,'limit':'Approximately consistent after rounding; does not resolve source measurement endpoints'},
        'dimension_status':'Length/width compass direction and base/wall/column/eave endpoints unspecified. Local X/Y base assignment is an interpretation; eave overhang increases total model bounds.',
        'identity':{'documentary_location':'east of Lingxing Gate, due south of Yimen','documented_bays':None,'central_door_documented':False,'actual_front_direction_verified':False},
        'estimated':'Single-storey three equal front divisions, central closed double door, two lattice windows, planar two-slope roof, tile counts, colours, base and unobserved rear/sides',
        'repair_record':{'year':2004,'source':'old museum page3_3'},
        'historical_only':[{'year':1760,'event':'repair'},{'year':1915,'event':'county middle-school gate use'}],
        'code_reuse':{'candidate':'chongming-west-guanting','source_commit':'ffc4510616e628d505b710b8e834f4bb3571eb8a','scope':'Generic facade/roof workflow with independent Ruxue dimensions and estimated openings; no proof of matching physical appearance'},
        'reference_period':'Historical museum text; not verified2026condition',
        'photo_reference_available':False,'photo_reconstruction_accepted':False,'yimen_photo_used_as_substitute':False,
        'photos_embedded':False,'map_replacement':False,'walk_integration':False,
        'viewer_walk_scope':'Outside the full model envelope; closed doors and no interior passage',
    }
    (a.out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(manifest,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
