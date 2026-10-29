"""Package source GLBs and a saved native file; never asserts acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess

ID='chongming-west-guanting'
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
        'id': ID, 'name': '崇明学宫西官厅（文字尺寸参照候选）',
        'status': 'standalone-candidate-not-geographically-registered',
        'reference_period': 'Museum historical text and 2021 article context; repair records have different scopes; not verified 2026 condition',
        'assets': assets,
        'source_dimensions_m': {'east_west_width': 7.4, 'north_south_length': 10.2, 'height': 6.5, 'interpreted_local_base': [10.2, 7.4]},
        'dimension_status': 'Source measurement endpoints unspecified. Local X adopts north-south length and Y adopts east-west width; long-side front is an interpretation, not a verified courtyard facade. Roof overhang increases bounds.',
        'identity': {'documentary_location': 'west of Pan Pool / Dengyun Bridge', 'shared_assumption_candidate': 'chongming-east-guanting', 'same_real_details_verified': False, 'documented_bays': None, 'actual_front_direction_verified': False},
        'estimated': 'Shared East Guanting appearance assumptions with distinct dimensions: three equal front divisions, central double door and two windows, planar gable roof, tile counts, colours, base, rear and sides; matching real details unverified',
        'repair_records': [{'year': 1998, 'scope': 'old museum Guanting repair record'}, {'year': 1991, 'scope': 'article lists East/West Guanting among buildings repaired'}, {'from': '1998-12', 'to': '1999-10', 'scope': 'second phase covering several site buildings including both Guanting'}],
        'different_east_guanting_dimensions': True,
        'map_replacement': False, 'walk_integration': False, 'photos_embedded': False,
        'photo_reference_available': False, 'photo_reconstruction_accepted': False,
        'aerial_context_reference': True,
    }
    (a.out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(manifest,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
