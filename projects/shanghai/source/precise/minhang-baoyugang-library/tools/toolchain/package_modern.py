#!/usr/bin/env python3
"""Create a new independent modern-building package; never register/install.
Adapted explicitly from upstream/package_precise_building.py. Modern LOD only compresses
raw unchanged or an explicit authored subtraction; no whole-model QEM simplification.
Uses the frozen Bund packager's geometry/compression functions, not its path policy.
All paths and provenance are explicit. LOD retains every source image and attribution.
"""
from pathlib import Path, PurePosixPath
import argparse, copy, hashlib, importlib.util, json, os, re, shutil, subprocess, sys, tempfile
from datetime import datetime, timezone

ROLES = ('raw', 'web', 'native', 'lod')
LIMIT = 100_000_000
HERE = Path(__file__).resolve().parent
DEFAULT_CORE = HERE / 'upstream/package_building.py'
from modern_contract import target as checked_target, bound as checked_bound, upstream as checked_upstream, external_gltfpack as checked_gltfpack

def fail(condition, message):
    if not condition: raise ValueError(message)

def digest(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def load_core(path):
    path=Path(path).resolve();expected=digest(path)
    spec=importlib.util.spec_from_file_location('_frozen_architecture_packager',path)
    fail(spec is not None and spec.loader is not None,'Cannot load frozen packaging helper')
    module=importlib.util.module_from_spec(spec); prior=sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode=True;spec.loader.exec_module(module)
    finally:sys.dont_write_bytecode=prior
    fail(digest(path)==expected,'Frozen packaging helper changed while importing')
    module._loaded_source_sha256=expected
    for name in ('load_helper','measure_asset','image_records','blender_header','run_pack','check_compressed','rewrite_glb_json','BASE_PARAMETERS'):
        fail(hasattr(module,name),'Frozen packaging helper lacks '+name)
    return module,path

def relative_asset(value, role):
    fail(isinstance(value,str) and bool(value),'Asset path must be a nonempty string')
    fail(re.fullmatch(r'[A-Za-z0-9_./-]+',value) is not None,'Unsafe asset path characters')
    p=PurePosixPath(value)
    fail(not p.is_absolute() and '..' not in p.parts and str(p)==value,'Asset path must be canonical project-relative')
    fail(all(not part.startswith('.') for part in p.parts),'Hidden/path traversal component rejected')
    prefix=('assets','native','precise') if role=='native' else ('assets','models','precise')
    fail(p.parts[:3]==prefix and len(p.parts)>=5,'Use the explicit precise asset namespace, not city/Bund assets')
    fail(p.suffix==('.blend' if role=='native' else '.glb'),'Asset suffix does not match role')
    return str(p)

def no_symlink_components(path):
    p=Path(path).absolute()
    fail(not any(q.is_symlink() for q in (p,*p.parents)),'Symlink path component rejected: '+str(path))

def text(value, field):
    fail(isinstance(value,str) and bool(value.strip()),'Missing '+field)
    return value

def normalized(value):return ''.join(c.lower() for c in value if c.isalnum())

def validate_spec(spec, base):
    fail(spec.get('schema')=='precise-building-package-input-v1','Unsupported input schema')
    ident=text(spec.get('id'),'id');fail(re.fullmatch('[a-z0-9][a-z0-9-]{0,95}',ident) is not None,'Invalid stable id')
    paths=spec.get('paths');fail(isinstance(paths,dict) and set(paths)==set(ROLES),'Exactly raw/web/native/lod paths are required')
    paths={r:relative_asset(paths[r],r) for r in ROLES}
    fail(len({v.casefold() for v in paths.values()})==4,'Asset paths must be distinct even on case-insensitive filesystems')
    p=copy.deepcopy(spec.get('provenance'));fail(isinstance(p,dict),'Explicit provenance is required')
    fail(p.get('id')==ident,'Provenance id does not match package id')
    for f in ('name','source_provider','source_url'):text(p.get(f),f)
    fail(p['source_url'].startswith(('https://','http://')),'source_url must be a public HTTP(S) URL')
    district=p.get('district');fail(isinstance(district,dict),'Explicit district object required')
    for f in ('id','name'):text(district.get(f),'district.'+f)
    for field in ('source_license','asset_license'):
        fail(isinstance(p.get(field),list) and bool(p[field]),'Explicit '+field+' entries required')
        for item in p[field]:
            fail(isinstance(item,dict),'Invalid license record')
            for key in ('id','url','attribution','role'):text(item.get(key),field+'.'+key)
    fail(isinstance(p.get('source_photos'),list),'source_photos must explicitly list photos, or [] for an untextured model')
    sources=[]
    for photo in p['source_photos']:
        for field in ('author','license','license_url','source_url','date'):text(photo.get(field),'photo.'+field)
        fail(isinstance(photo.get('embedded_as_texture'),bool),'Photo embedding declaration must be boolean')
        if not photo['embedded_as_texture']:continue
        image=photo.get('image');fail(isinstance(image,dict),'Embedded photo image metadata required')
        fail(type(image.get('bytes')) is int and 0<image['bytes']<LIMIT,'Invalid original photo size')
        fail(re.fullmatch('[a-f0-9]{64}',str(image.get('sha256',''))) is not None,'Invalid original photo SHA256')
        source=Path(text(image.get('source'),'embedded photo image.source'))
        if not source.is_absolute():source=base/source
        source=source.resolve();fail(source.is_file(),'Original photo is missing: '+str(source))
        fail(source.stat().st_size==image['bytes'] and digest(source)==image['sha256'],'Original photo bytes/SHA mismatch')
        sources.append((source,image['sha256'],image['bytes']))
    # Share-alike texture adaptations cannot be silently declared MIT/CC0 only.
    asset_ids={normalized(x['id']) for x in p['asset_license']}
    for photo in p['source_photos']:
        if photo['embedded_as_texture'] and normalized(photo['license']).startswith('ccbysa'):
            fail(normalized(photo['license']) in asset_ids,'Embedded BY-SA photograph license must remain in asset_license')
    tokens=spec.get('required_copyright_tokens',[])
    fail(isinstance(tokens,list) and all(isinstance(t,str) and bool(t.strip()) for t in tokens),'required_copyright_tokens must be a list of nonempty strings')
    return ident,paths,p,sources

def self_contained(core,helper,path):
    doc,_=core.image_records(helper,path)
    fail(all('uri' not in b for b in doc.get('buffers',[])),'GLB contains an external buffer URI')
    fail(all('uri' not in im for im in doc.get('images',[])),'GLB contains an image URI')
    return doc

def package(target_path,project,gltfpack,output):
    t=checked_target(target_path);checked_upstream(project)
    core_path=DEFAULT_CORE;spec_path=checked_bound(t['actual']['package_spec']);raw=checked_bound(t['actual']['raw']);native=checked_bound(t['actual']['native'])
    lod_input=raw if t['lod_policy']['mode']=='compression-only' else checked_bound(t['actual']['authored_lod'])
    spec_path=Path(spec_path).resolve();spec_bytes=spec_path.read_bytes();spec=json.loads(spec_bytes);ident,paths,provenance,photos=validate_spec(spec,spec_path.parent)
    raw,native,project=Path(raw).resolve(),Path(native).resolve(),Path(project).resolve()
    no_symlink_components(output); output=Path(output).absolute()
    fail(not output.exists(),'Output must not exist; no previous package is overwritten')
    fail(output!=project and project not in output.parents and output not in project.parents,'Output must be independent from project')
    fail(all(output!=p and output not in p.parents for p in (raw,native,spec_path,*[x[0] for x in photos])),'Output may not contain an input')
    # Read-only conflict check, independent of any Bund/global registry.
    for rel in paths.values():
        target=project/rel;no_symlink_components(target)
        fail(not target.exists(),'Existing project asset is protected: '+rel)
    core,core_path=load_core(core_path)
    for p in (raw,native,spec_path):fail(p.is_file(),'Missing input: '+str(p));core.sized(p)
    exe=shutil.which(str(gltfpack));fail(exe is not None,'gltfpack executable not found');exe=str(Path(exe).resolve());external_tool=checked_gltfpack(exe)
    helper_expected=digest(project/'tools/build_bund_lods.py')
    helper,helper_path=core.load_helper(project)
    fail(digest(helper_path)==helper_expected,'Measurement helper changed while importing')
    snapshots={p:digest(p) for p in (raw,native,lod_input,Path(target_path).resolve())}
    for key,value in t['actual'].items():
        if isinstance(value,dict) and 'source' in value:snapshots[checked_bound(value)]=value['sha256']
    snapshots[core_path]=core._loaded_source_sha256
    snapshots[HERE/'external-tool-lock.json']=digest(HERE/'external-tool-lock.json')
    for row in external_tool['files']:snapshots[Path(row['source'])]=row['sha256']
    snapshots[helper_path]=helper_expected
    snapshots[spec_path]=hashlib.sha256(spec_bytes).hexdigest()
    for photo_path,expected,_ in photos:snapshots[photo_path]=expected
    for p,expected in snapshots.items():fail(digest(p)==expected,'Input changed since initial validation: '+str(p))
    native_info=core.blender_header(native); source_doc=self_contained(core,helper,raw)
    copyright=text(source_doc.get('asset',{}).get('copyright'),'raw asset.copyright')
    # Preserve licenses and explicit optional attribution tokens; never inject OSM defaults.
    tokens=[x['id'] for key in ('source_license','asset_license') for x in provenance[key]]
    tokens+=spec.get('required_copyright_tokens',[])
    fail(all(isinstance(t,str) and normalized(t) and normalized(t) in normalized(copyright) for t in tokens),'Raw copyright does not contain required license/attribution tokens')
    version_run=subprocess.run([exe,'-v'],capture_output=True,text=True,check=True);version=(version_run.stdout+version_run.stderr).strip()
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.'+ident+'-package-',dir=output.parent) as tmp:
        work=Path(tmp);payload=work/'payload';payload.mkdir();targets={r:payload/rel for r,rel in paths.items()}
        for p in targets.values():p.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(raw,targets['raw']);shutil.copyfile(native,targets['native'])
        fail(digest(targets['raw'])==snapshots[raw] and digest(targets['native'])==snapshots[native],'Input changed while copying')
        raw_asset,raw_bounds=core.measure_asset(helper,targets['raw'],paths['raw'],source=True)
        declared={(x[1],x[2]) for x in photos};embedded={(r['sha256'],r['bytes']) for r in raw_asset['embedded_images']}
        fail(embedded==declared,'Every embedded image must match a declared original photo; no missing/extra images')
        native_asset={'file':paths['native'],'sha256':snapshots[native],'bytes':core.sized(targets['native']),'triangles':None,'bounds_glb':None,'geometry_evaluated':False,**native_info}
        def compressed(role,params):
            _,report=core.run_pack(exe,lod_input if role=='lod' else targets['raw'],targets[role],params,work/(role+'-gltfpack.json'))
            # gltfpack can remove root metadata. Restore supplied provenance only, preserving compressed BIN.
            def metadata(doc):
                if 'extras' in source_doc:doc['extras']=copy.deepcopy(source_doc['extras'])
                if 'extras' in source_doc.get('asset',{}):doc.setdefault('asset',{})['extras']=copy.deepcopy(source_doc['asset']['extras'])
            core.rewrite_glb_json(targets[role],metadata)
            a,_=core.check_compressed(helper,targets[role],paths[role],raw_asset,raw_bounds,copyright,report)
            after=self_contained(core,helper,targets[role]);fail(after.get('extras')==source_doc.get('extras'),'Root provenance changed')
            return a
        web=compressed('web',core.BASE_PARAMETERS)
        fail(web['triangles']==raw_asset['triangles'],'Web triangle count changed')
        fail(web['maximum_bounds_change_m']<=core.WEB_BOUNDS_TOLERANCE_M,'Web bounds exceed 0.0001 m')
        # Modern thin shells and apertures are never globally simplified.
        # Either compress raw unchanged, or compress the author's explicit subtractive LOD.
        lod=compressed('lod',core.BASE_PARAMETERS)
        fail(lod['maximum_bounds_change_m']<helper.MAX_BOUNDS_CHANGE,'Authored LOD bounds exceed strict0.35m limit')
        accepted={'parameters':list(core.BASE_PARAMETERS),'target_triangle_ratio':None,'relative_error_limit':None,'permissive':False,'accepted':True,'maximum_bounds_change_m':lod['maximum_bounds_change_m'],'bytes':lod['bytes'],'triangles':lod['triangles'],'mode':t['lod_policy']['mode']}
        history=[accepted]
        assets={'raw':raw_asset,'web':web,'native':native_asset,'lod':lod}
        for p,expected in snapshots.items():fail(digest(p)==expected,'Input/helper changed during packaging: '+str(p))
        for rel in paths.values():
            no_symlink_components(project/rel);fail(not (project/rel).exists(),'Project target appeared during packaging; refusing stale copy-new plan')
        record={'schema':'precise-building-packaging-v1','packaging_passed':True,'registered':False,'building_id':ident,'created_utc':datetime.now(timezone.utc).isoformat(),'generator_sha256':digest(Path(__file__)),'gltfpack_version':version,'frozen_helper':{'file':str(core_path),'sha256':snapshots[core_path]},'measurement_helper':{'file':'tools/build_bund_lods.py','sha256':snapshots[helper_path]},'inputs':{'raw':{'file':str(raw),'sha256':snapshots[raw]},'native':{'file':str(native),'sha256':snapshots[native]},'spec':{'file':str(spec_path),'sha256':snapshots[spec_path]}},'provenance':provenance,'source_asset_metadata':source_doc['asset'],'source_extras':source_doc.get('extras'),'assets':assets,'asset_files':[a['file'] for a in assets.values()],'registration_assets':{r:{'source':str(output/a['file']),'file':a['file'],'bytes':a['bytes'],'sha256':a['sha256']} for r,a in assets.items()},'lod_policy':{'maximum_bounds_change_m':helper.MAX_BOUNDS_CHANGE,'comparison':'strictly less','attempts':history,'accepted':accepted,'image_policy':'retain_all_original_images','no_material_approximation':True},'commands_relative_to_output':{'web':['gltfpack','-i',paths['raw'],'-o',paths['web'],*core.BASE_PARAMETERS],'lod':['gltfpack','-i',paths['raw'],'-o',paths['lod'],*accepted['parameters']],'postprocess':'Restore source asset.copyright, source root extras and asset extras without modifying compressed BIN.'},'verification':{'raw_native_byte_identical':True,'all_original_image_bytes_preserved':True,'original_image_source_files_checked':True,'original_image_source_scope':'embedded_as_texture=true only; non-embedded reference provenance is preserved but its files are not verified here','copyright_preserved':True,'source_provider_provenance_preserved':True,'all_files_strictly_under_bytes':LIMIT,'web_triangle_count_preserved':True,'web_bounds_limit_m':core.WEB_BOUNDS_TOLERANCE_M,'project_destinations_absent':True,'inputs_and_helpers_unchanged':True},'limitations':['Not a registration, installation or building acceptance; navigation/district/provider are caller-supplied and not inferred.','Native checks cover recognizable plain/gzip/zstandard Blender headers and exact copied bytes; Blender geometry/packed resources were not inspected.','No browser, rendering, Blender or photographic metric review; no decoded triangle/normal/UV equivalence check in this tool.','LOD bounds are not a Hausdorff or silhouette proof; all LOD images remain, without an invented tinted-glass replacement.','Asset copy-new plan requires fresh source SHA and target absence checks when a separate installer runs.']}
        record['external_gltfpack_tool_lock']={'source':str(HERE/'external-tool-lock.json'),'bytes':(HERE/'external-tool-lock.json').stat().st_size,'sha256':digest(HERE/'external-tool-lock.json')}
        record['modern_target']={'source':str(Path(target_path).resolve()),'sha256':digest(target_path)}
        record['authored_lod_input']={'source':str(lod_input),'bytes':lod_input.stat().st_size,'sha256':digest(lod_input)}
        record['lod_policy'].update(mode=t['lod_policy']['mode'],automatic_simplification=False,geometric_reduction_claimed=lod['triangles']<raw_asset['triangles'],actual_triangle_ratio=lod['triangles']/raw_asset['triangles'],allowed_omission_label_patterns=t['lod_policy']['allowed_omission_label_patterns'],protected_geometry_verification='pending actual GLTFLoader decode and independent probes')
        record['verification']['decoded_geometry_passed']=False
        record['limitations'].append('Modern LOD is compression-only or explicit authored subtraction; package bounds do not prove retained apertures, parts or normals. Actual decoder must independently verify all retained triangles.')
        record['commands_relative_to_output']['lod'][2]=str(lod_input)
        checked_upstream(project);checked_target(target_path)
        record_path=payload/'packaging-record.json';record_path.write_text(json.dumps(record,ensure_ascii=False,indent=2,allow_nan=False)+'\n');core.sized(record_path)
        fail(not output.exists(),'Output appeared while packaging; refusing replacement')
        # Reserve the final directory exclusively, then move verified files into it.
        # A marker is retained until the record is installed last; consumers require the record.
        output.mkdir();marker=output/'.package-incomplete';marker.write_text('not ready\n')
        for p in payload.iterdir():
            if p.name!='packaging-record.json':os.rename(p,output/p.name)
        os.rename(record_path,output/'packaging-record.json');marker.unlink()
    return record

def main():
    p=argparse.ArgumentParser(description='Stage-only modern package. Requires an actual ready target; pending templates are rejected.')
    for f in ('target','project','output'):p.add_argument('--'+f,type=Path,required=True)
    p.add_argument('--gltfpack',required=True);a=p.parse_args()
    try:r=package(a.target,a.project,a.gltfpack,a.output)
    except (ValueError,OSError,KeyError,IndexError,subprocess.CalledProcessError) as e:p.exit(1,'Packaging failed: '+str(e)+'\n')
    print(json.dumps({'packaging_passed':True,'registered':False,'decoded_geometry_passed':False,'building_id':r['building_id'],'record':str(a.output/'packaging-record.json')},ensure_ascii=False))
if __name__=='__main__':main()
