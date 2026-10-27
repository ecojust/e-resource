"""Finalize the v2 manifest from actual artifacts and one canonical metadata file.
Run only after the author has viewed the final previews and written visual review.
"""
from pathlib import Path
import json,hashlib,datetime,shutil,struct
ROOT=Path(__file__).resolve().parent.parent

def load(name):return json.loads((ROOT/name).read_text())
def dump(name,obj):(ROOT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def desc(p):return {'file':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
meta=load('source/asset-metadata.json');copyright=meta['copyright']
build=load('build-report.json');native=load('review/native-render-report.json');native_check=load('review/native-metadata-check.json');visual=load('review/author-visual-review.json');revision=load('review/author-revision-check.json')
assert native['raw_input']['sha256']==build['raw']['sha256']
assert native['native']['sha256']==native_check['native_sha256']
assert native['copyright']==native_check['scene_copyright']==native_check['model_collection_copyright']==copyright
assert visual['actually_viewed_final_previews'] and visual['raw_sha256']==build['raw']['sha256']
for item in visual['images']:assert desc(ROOT/item['file'])['sha256']==item['sha256']
for item in [build['raw'],build['lod_raw']]:
 data=(ROOT/item['file']).read_bytes();size=struct.unpack_from('<I',data,12)[0];glb=json.loads(data[20:20+size]);assert glb['asset']['copyright']==glb['extras']['copyright']==copyright
assert revision['changed_part_count']==6
source_files=sorted([p for p in (ROOT/'source').rglob('*') if p.is_file() and '__pycache__' not in p.parts]+[ROOT/'LICENSE',ROOT/'README.md'])
expected=[ROOT/build['raw']['file'],ROOT/build['lod_raw']['file']]+sorted((ROOT/'textures').glob('*'))
portable={'schema':'bajin-portable-source-v2','author':meta['author'],'copyright':copyright,'frozen_source_files':[desc(p) for p in source_files],'environment':{'python':'3.12.14','numpy':'2.3.5','shapely':'2.2.0','Pillow':'12.3.0','Blender':'4.3.2'},'reviewed_commands_from_package_root':['python source/generate_material.py --output textures','python source/build_model.py','python source/author_buffer_check.py','blender --background --threads 2 --python source/render_native.py','blender --background review/native/bajin-main-house.blend --python source/check_native_metadata.py'],'network_required':False,'private_reference_reads_required':False,'optional_parent_comparison':'source/check_revision.py reads adjacent frozen bajin-detailed-v1; it is not required for isolated model reproduction.','expected_deterministic_outputs':[desc(p) for p in expected],'native_and_preview_hashes_not_cross_environment_deterministic':True,'LOD_part_selection_rule':'omit labels starting flat-tiles/, ending /door-handle, or containing /panel-bead-; keep all other full parts','isolated_independent_reproduction_status':'pending v2 review'}
dump('PORTABLE.json',portable)
files=sorted(p for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in ['FILES.json','HANDOFF.json'])
index={'schema':'bajin-detailed-files-v2','files':[desc(p) for p in files],'total_listed_bytes':sum(p.stat().st_size for p in files),'every_file_strictly_under_100000000':all(p.stat().st_size<100000000 for p in files)};dump('FILES.json',index)
design=load('source/design-input.json');free=shutil.disk_usage(ROOT).free
handoff={'schema':'bajin-detailed-handoff-v2','author':meta['author'],'copyright':copyright,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'Frozen v2 exterior correction draft; awaiting root and independent v2 QA. NOT installed, integrated or published.','immutable_after_handoff':True,'resume_entry':'Read README.md, author-revision-check, native-metadata-check and actual preview images; review v2 before any integration. Do not modify frozen v1 or v2 in place.','revision_scope':design['revision_scope'],'north_entry_revision':design['north_entry_revision'],'parent_binding':load('source/parent-binding.json'),'raw':build['raw'],'lod_raw':build['lod_raw'],'native':native['native'],'previews':native['images'],'triangles':build['triangles'],'lod_triangles':build['lod_triangles'],'height_m_estimated':build['height_m'],'source_geometry':build['source_geometry'],'coordinate_frame':'Anchor-local ENU baked in vertex positions; GLB East/Up/-North; heading zero','anchor':design['frame']['anchor'],'changed_part_count':revision['changed_part_count'],'unchanged_part_count':revision['unchanged_part_count'],'source_frame_roof_textures_and_UV_contract_unchanged':True,'main_house_scope_unchanged':True,'review_manifests':[desc(ROOT/p) for p in ['source/asset-metadata.json','source/design-input.json','roof-planar-contract.json','features.json','construction-parts.json.gz','uv-contract.json','PORTABLE.json','review/native-render-report.json','review/native-metadata-check.json','review/author-buffer-screen.json','review/author-revision-check.json','review/author-visual-review.json','FILES.json']],'canonical_copyright_exactly_matches_raw_native_and_handoff':True,'native_model_collection':native['model_collection'],'native_preview_collection_not_asset':native['preview_collection'],'completed_author_checks':['All six changed construction parts bound to actual raw/LOD triangle buffers; 3780 other parts unchanged.','North stair boundary manifold, every edge exactly two faces, positive expected volume, three actual risers and tapered widths.','Arch/coping stop heights and unblocked central gap; low-wall5mm seams closed while inner edges retained.','Raw geometry/UV screening and exact source/frame/roof/texture/UV-contract invariants.','Actual saved native copyright readback and three final previews viewed.'],'pending':['Root final v2 geometry/appearance review','Independent v2 asset/native/isolated reproduction QA','Owner generation and neighbor integration','Compressed web/LOD browser checks','Publication'],'current_processes_running':False,'MAIN_modified':False,'remote_modified':False,'accepted':False,'installed':False,'published':False,'not_counted_in_published_36_buildings':True,'remaining_disk_bytes_at_handoff':free}
assert free>=300000000
assert sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())+30000<20000000
assert index['every_file_strictly_under_100000000']
dump('HANDOFF.json',handoff)
assert load('HANDOFF.json')['copyright']==copyright
print(json.dumps({'handoff':desc(ROOT/'HANDOFF.json'),'all_directory_bytes':sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file()),'remaining_disk_bytes':shutil.disk_usage(ROOT).free,'raw':build['raw'],'native':native['native']},indent=2))
