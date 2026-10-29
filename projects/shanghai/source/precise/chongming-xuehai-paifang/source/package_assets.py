"""Package source GLBs and a saved native file; never asserts acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess

ID='chongming-xuehai-paifang'
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
        'id':ID,'name':'崇明学宫西牌坊（题名面待核）','status':'standalone-structure-candidate-not-geographically-registered',
        'assets':assets,
        'identity':{'physical_side':'west per official2021text','legacy_id_is_not_an_accepted_inscription':True,'individual_photo_face_binding_complete':False},
        'source_dimensions_m':{'pillar_ns_distance_ambiguous_endpoints':4.4,'pillar_ew_dimension_ambiguous_endpoints':1.6,'pair_spacing_ambiguous_endpoints':33},
        'interpretations_m':{'post_axis_spacing':4.4,'foot_support_depth_not_shaft_section':1.6,'total_height_including_highest_ornament_estimated':9.6},
        'height_status':'三丈 is not converted into surveyed10m;9.6m is an estimate guided by secondary over9m wording',
        'structure':{'stone_posts':2,'independent_canopies':3,'high_central_canopy':1,'low_side_canopies':2,'upswept_roof_corners':12,'passage_open_in_geometry':True,'plaque_faces':'blank'},
        'title_sources':{'official2021_west':['道冠古今','学海'],'old_museum1998_undefined_left':['学海','德配天地'],'old_museum1998_undefined_right':['朝宗','道冠古今'],'difference_resolved':False,'titles_engraved':False},
        'reference_period':'Historical museum text,2021official side grouping,2023collage and front panorama; capture dates/same-object face pairing unverified; not2026survey',
        'estimated':'Post sections,footing interpretation,roof spans and curves,hip ends,bracket joinery,original simplified carving/crest shapes,materials,rear and hidden supports',
        'photos_embedded':False,'photo_reference_available':True,'photo_reconstruction_accepted':False,
        'map_replacement':False,'walk_integration':False,'viewer_walk_scope':'outside whole model envelope only; does not permit passage traversal or climbing',
    }
    (a.out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(manifest,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
