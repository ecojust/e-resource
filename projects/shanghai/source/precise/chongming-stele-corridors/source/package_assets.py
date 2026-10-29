"""Package source GLBs and a saved native file; never asserts acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess

ID='chongming-stele-corridors'
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
    manifest = {'id': 'chongming-stele-corridors', 'name': '崇明学宫碑廊（两长边分段候选）', 'status': 'standalone-long-side-components-candidate-not-geographically-registered', 'source_dimensions_m': {'total_length': 76.7, 'width': 2.5, 'each_long_side_interpretation': 30.5, 'north_south_combined_budget': 15.7, 'measurement_endpoints_verified': False}, 'model_scope': {'component_count': 2, 'each_base': [30.5, 2.5], 'modeled_baseline_total_length': 61.0, 'north_south_geometry_created': False, 'estimated_total_height': 4.6, 'full_layout_accepted': False}, 'display_layout': {'local_y_centres': [-3.5, 3.5], 'separation': 7.0, 'placement_only': True, 'measured_courtyard_width': False, 'same_facing': True}, 'common_geometry_assumptions_shared': True, 'same_real_details_independently_verified': False, 'historical_collection_count': 53, 'blank_panels_per_component': 20, 'all_blank_panel_positions_and_sizes_estimated': True, 'inscriptions_reconstructed': False, 'area_m2': {'museum_reported_all_corridors': 191.75, 'calculated_documented_total_times_width': 191.75, 'modeled_long_side_base_total': 152.5}, 'identity': {'documentary_location': 'between Yimen and Minglun Hall, east/west long sides and unresolved north/south portions', 'photographed_side_verified': False}, 'estimated': 'Height4.6m,10 chosen divisions with3.0m column spacing/end margins, column size, roof external form/curvature,40 blank panels total and all locations, paving, wall thickness and hidden rear.', 'repair_record': {'year': 2001, 'source': 'old museum page3_3'}, 'photo_reference_available': True, 'photo_scale_accepted': False, 'complete_photo_reconstruction_accepted': False, 'photos_embedded': False, 'map_replacement': False, 'walk_integration': False, 'viewer_walk_scope': 'Only outside the entire display envelope; no through-gallery viewer navigation despite separately verified geometric open cores'}
    manifest['assets']=assets
    (a.out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(manifest,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
