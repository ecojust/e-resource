"""Package source GLBs and a saved native file; never asserts acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess

ID='chongming-yimen'
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
        'id':ID,'name':'崇明学宫仪门（照片形态参照候选）','status':'standalone-photo-form-candidate-not-geographically-registered','assets':assets,
        'source_dimensions_m':{'front_width':10.6,'depth':9.7,'height':9.07,'measurement_endpoints_verified':False},
        'model_dimensions_m':{'interpreted_base':[10.6,9.7],'estimated_total_height':7.0,'height_is_pixel_measurement':False},
        'height_reconciled':False,'documented_height_satisfied':False,
        'height_limit':'The 7.0m model height is a form-design estimate. The documentary9.07m height is preserved separately; its endpoints and relationship to this photograph remain unresolved.',
        'area_m2':{'museum_reported':102.8,'calculated_width_times_depth':102.82},
        'identity':{'documentary_location':'east of Lingxing Gate, north of Ruxue Gate','documented_bays':None,'complete_column_network_verified':False},
        'observed':'Curved pale end walls, curved front roof, two inner uprights, six grille fields per side, two exposed fields per curtain flank, beige curtain and vertical plaque field',
        'estimated':'Profile coordinates, grille pane counts, curtain fold count, colours, two steps, symmetric rear roof and plain closed rear wall',
        'repair_record':{'year':2001,'source':'old museum page3_3'},
        'photo_reference_available':True,'photo_scale_accepted':False,'complete_photo_reconstruction_accepted':False,
        'photos_embedded':False,'map_replacement':False,'walk_integration':False,
        'viewer_walk_scope':'Outside the full model envelope; no interior or passage behind the curtain',
    }
    (a.out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(manifest,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
