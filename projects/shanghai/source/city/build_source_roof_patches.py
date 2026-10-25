"""Plan or build an isolated patch from individually source-qualified roofs.

The default is a plan only. --export rebuilds affected owner cells using the
existing exporter, height sources, exclusions and residuals. ROOF_CELL_READY
lines are emitted only after a whole owner cell passes validation. The base
city is never modified, and its existing partition IDs must remain unchanged.
"""
from pathlib import Path, PurePosixPath
from concurrent.futures import ProcessPoolExecutor, as_completed
from collections import Counter
import argparse, hashlib, importlib, json, math, os, shutil, sys

VERSION = 'source-qualified-roof-patch-v1'
LIMIT = 100_000_000


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write_json(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name('.' + path.name + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    os.replace(temp, path)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def safe_asset(root, relative):
    path = PurePosixPath(relative)
    if path.is_absolute() or '..' in path.parts or '\\' in str(relative):
        raise ValueError(f'Unsafe asset path: {relative}')
    return Path(root) / path


def independent(output, *sources):
    output = Path(output).resolve()
    for source in sources:
        source = Path(source).resolve()
        if output.is_relative_to(source) or source.is_relative_to(output):
            raise ValueError(f'Output must be independent of source tree: {source}')


def load_builder(directory):
    sys.path.insert(0, str(Path(directory).resolve()))
    return importlib.import_module('build_fullcity_models')


def make_plan(args, builder):
    base = json.loads((args.base_models/'manifest.json').read_text())
    qualified = json.loads(args.qualified_roofs.read_text())
    if not base.get('complete') or not base.get('coverage_balanced'):
        raise ValueError('Base city must be complete and coverage balanced')
    if qualified.get('complete') is not True or not qualified.get('schema_version'):
        raise ValueError('Qualification must have complete:true and a schema_version')
    roofs = qualified.get('roofs')
    if not isinstance(roofs, list) or not roofs:
        raise ValueError('No accepted source-qualified roofs')
    exclusions = json.loads(args.landmark_exclusions.read_text())
    excluded = {layer: set(exclusions.get(layer+'_ids', [])) for layer in ('building','building_part')}
    residual = json.loads(args.parent_residuals.read_text()).get('parent_geometry_overrides', {})
    configuration = json.loads((args.base_models/'build-configuration.json').read_text())
    accepted_exclusion_hashes = {configuration.get('landmark_exclusions_sha256')}
    accepted_exclusion_hashes.update(base.get('detail_patch', {}).get(k) for k in ('runtime_exclusions_sha256','generation_exclusions_sha256'))
    if sha(args.landmark_exclusions) not in accepted_exclusion_hashes:
        raise ValueError('Exclusions do not match the current base city/detail patch')
    if configuration.get('parent_residual_file_sha256') != sha(args.parent_residuals):
        raise ValueError('Parent residual input differs from the current base city')
    by_key = {}; cells = {}; source_cache = {}
    for roof in roofs:
        layer = roof['source_layer']; identity = str(roof['id']); key = layer+':'+identity
        if layer not in excluded or key in by_key or roof.get('key', key) != key:
            raise ValueError(f'Invalid/duplicate qualified identity: {key}')
        tile = list(map(int, roof.get('owner_tile') or roof['tile']))
        cell_id = '-'.join(map(str, tile))
        source = args.raw/'tiles'/str(tile[0])/str(tile[1])/(str(tile[2])+'.geojson.gz')
        if not source.is_file(): source = source.with_suffix('')
        if cell_id not in source_cache:
            collection = builder.read_raw(source)
            actual_tile, origin, bbox, meta = builder.raw_tile(source, collection)
            if list(actual_tile) != tile: raise ValueError(f'Raw owner tile differs: {cell_id}')
            features = {f['properties'].get('source_layer','building')+':'+str(f['properties']['id']): f for f in collection['features']}
            if len(features) != len(collection['features']): raise ValueError(f'Duplicate source IDs: {cell_id}')
            source_cache[cell_id] = (sha(source), features, origin)
            state_path = args.base_models/'state'/(cell_id+'.json')
            state = json.loads(state_path.read_text())
            ids = state['models']
            if state['source_sha256'] != source_cache[cell_id][0] or not ids:
                raise ValueError(f'Base owner state does not match raw input: {cell_id}')
            records = {r['id']: r for r in base['tiles'] if r['tile'] == tile}
            if set(ids) != set(records): raise ValueError(f'Base manifest/state ownership differs: {cell_id}')
            for output_id, record in records.items():
                current = json.loads((args.base_models/'records'/(output_id+'.json')).read_text())
                if current != record: raise ValueError(f'Base record differs from manifest: {output_id}')
                for path_key, hash_key in [('file','sha256'),('feature_ids_file','feature_ids_sha256')]:
                    if sha(safe_asset(args.base_models, record[path_key])) != record[hash_key]:
                        raise ValueError(f'Base asset changed: {output_id}/{path_key}')
            cells[cell_id] = {'id':cell_id,'tile':tile,'source_file':str(source.resolve()),
                'source_sha256':source_cache[cell_id][0],'superseded_output_ids':ids,
                'base_state_sha256':sha(state_path),'qualified_keys':[]}
        source_hash, features, origin = source_cache[cell_id]
        expected_hash = roof.get('source_sha256') or roof.get('source_tile_sha256')
        if source_hash != expected_hash: raise ValueError(f'Qualified raw source hash changed: {key}')
        feature = features.get(key)
        if not feature: raise ValueError(f'Qualified source record missing: {key}')
        props = feature['properties']
        if props.get('renderable') is False or identity in excluded[layer] or identity in residual or key in exclusions.get('geometry_overrides', {}):
            raise ValueError(f'Qualified roof overlaps excluded/residual/replaced geometry: {key}')
        if canonical(feature['geometry']) != canonical(roof['geometry']):
            raise ValueError(f'Qualified footprint differs from raw source: {key}')
        if roof.get('original_properties') is not None and canonical(props) != canonical(roof['original_properties']):
            raise ValueError(f'Qualified properties differ from raw source: {key}')
        if list(roof['origin']) != list(origin) or str(roof['district_id']) != str(props['district_id']):
            raise ValueError(f'Qualified origin/district differs: {key}')
        if feature['geometry']['type'] != 'Polygon' or len(feature['geometry']['coordinates']) != 1:
            raise ValueError(f'Unsupported accepted footprint topology: {key}')
        axes = roof.get('axes', {})
        normalized = {'roof_shape':roof['roof_shape'],'roof_height':float(roof['roof_height']),
            'height':float(roof['height']),'base':float(roof.get('base',roof.get('min_height')) or 0),
            'ridge_unit':roof.get('ridge_unit') or axes.get('ridge_axis_xz'),
            'down_slope_unit':roof.get('down_slope_unit') or axes.get('downslope_axis_xz')}
        if normalized['roof_shape'] not in ('gabled','skillion') or not all(math.isfinite(normalized[k]) for k in ('height','base','roof_height')):
            raise ValueError(f'Invalid accepted roof parameters: {key}')
        raw_base, raw_height, raw_quality = builder.building_height(props)
        height_tolerance=4*sum(math.ulp(normalized[name]) for name in ('height','base','roof_height'))
        if (normalized['roof_shape'] != props.get('roof_shape')
                or float(props.get('roof_height')) != normalized['roof_height']
                or raw_quality != 'source_height' or raw_base!=normalized['base']
                or raw_height!=normalized['height']
                or normalized['roof_height']<=0
                or normalized['roof_height']>normalized['height']-normalized['base']+height_tolerance):
            raise ValueError(f'Accepted roof parameters disagree with raw source height/shape: {key}')
        by_key[key] = normalized; cells[cell_id]['qualified_keys'].append(key)
    # A later incremental patch must never flatten a previously enhanced roof.
    for record in base['tiles']:
        if '-'.join(map(str,record['tile'])) in cells:
            old = set(record.get('source_roof_enhancement', {}).get('keys', []))
            if not old.issubset(by_key): raise ValueError('Qualification omits an existing roof in an affected cell')
    return {'version':VERSION,'base_manifest_sha256':sha(args.base_models/'manifest.json'),
        'base_model_count':base['model_count'],'base_feature_count':base['feature_count'],
        'qualification_sha256':sha(args.qualified_roofs),'qualification_schema_version':qualified['schema_version'],
        'qualified_count':len(by_key),'qualified_keys':sorted(by_key),'affected_owner_cells':list(cells.values()),
        'partition_policy':'Replay original median-split tree; retain every current output ID. Fail rather than silently split or omit accepted roofs.'}, by_key, qualified, configuration


def validate_cell(output, base, cell, configuration_hash, builder):
    state_path = output/'state'/(cell['id']+'.json')
    state = json.loads(state_path.read_text())
    if state['source_sha256'] != cell['source_sha256'] or state['configuration_sha256'] != configuration_hash:
        raise ValueError(f'Stale patch state: {cell["id"]}')
    if set(state['models']) != set(cell['superseded_output_ids']):
        raise ValueError(f'Owner partition IDs changed: {cell["id"]}')
    records = []; applied = []; files = []
    invariant_keys = ('building_count','building_footprints','building_parts','polygon_count','height_quality',
                      'district_counts','geometry_sources','geographic_bbox','geometry_bbox','invalid_polygon_count',
                      'residual_parent_features','residual_parent_area_m2','residual_parent_height_quality')
    for identity in state['models']:
        record_path = output/'records'/(identity+'.json')
        record = json.loads(record_path.read_text()); old = json.loads((base/'records'/(identity+'.json')).read_text())
        for key in invariant_keys:
            # Legacy V2 records omit zero-valued residual fields.
            expected = old.get(key, {} if key=='residual_parent_height_quality' else 0)
            actual = record.get(key, {} if key=='residual_parent_height_quality' else 0)
            if actual != expected: raise ValueError(f'Non-roof invariant changed: {identity}/{key}')
        if record['feature_ids_sha256'] != old['feature_ids_sha256']:
            raise ValueError(f'Feature ID sidecar changed: {identity}')
        doc, triangles = builder.validate_glb(safe_asset(output, record['file']))
        if triangles != record['triangles']: raise ValueError(f'Triangle metadata mismatch: {identity}')
        for file_key, hash_key, size_key in [('file','sha256','size_bytes'),('feature_ids_file','feature_ids_sha256','feature_ids_size_bytes')]:
            path = safe_asset(output, record[file_key])
            if path.stat().st_size != record[size_key] or path.stat().st_size >= LIMIT or sha(path) != record[hash_key]:
                raise ValueError(f'Patch file checksum/size differs: {path}')
            files.append({'file':record[file_key],'bytes':path.stat().st_size,'sha256':record[hash_key]})
        files.append({'file':str(record_path.relative_to(output)),'bytes':record_path.stat().st_size,'sha256':sha(record_path)})
        applied.extend(record.get('source_roof_enhancement', {}).get('keys', [])); records.append(record)
    if len(applied) != len(set(applied)) or set(applied) != set(cell['qualified_keys']):
        raise ValueError(f'Accepted roof application count differs: {cell["id"]}')
    files.append({'file':str(state_path.relative_to(output)),'bytes':state_path.stat().st_size,'sha256':sha(state_path)})
    return records, files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('raw','base-models','qualified-roofs','landmark-exclusions','output','height-raster','cnbh-raster','cmab-shards','height-lock','parent-residuals'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--city-source-dir',type=Path,default=Path(__file__).resolve().parent)
    parser.add_argument('--gltfpack',default=os.environ.get('GLTFPACK') or shutil.which('gltfpack'))
    parser.add_argument('--workers',type=int,default=2)
    parser.add_argument('--export',action='store_true')
    args = parser.parse_args()
    independent(args.output,args.raw,args.base_models)
    if args.output.exists() and any(args.output.iterdir()) and not (args.output/'patch-manifest.json').is_file():
        parser.error('Use an empty output directory or an existing source-roof patch directory')
    args.output.mkdir(parents=True,exist_ok=True)
    write_json(args.output/'patch-manifest.json',{'version':VERSION,'complete':False,'status':'planning-or-building'})
    builder = load_builder(args.city_source_dir)
    plan, overrides, qualified, base_config = make_plan(args,builder)
    write_json(args.output/'patch-plan.json',plan)
    print('ROOF_PATCH_PLAN',json.dumps({'cells':len(plan['affected_owner_cells']),'qualified_roofs':len(overrides),'export':args.export}),flush=True)
    if not args.export: return
    if not args.gltfpack: parser.error('--gltfpack is required for export')
    geometry = importlib.import_module('roof_geometry')
    lock = json.loads(args.height_lock.read_text())
    configuration = {'version':VERSION,'build_version':builder.VERSION,'sampler_version':lock['sampler_version'],
        'compress':True,'target_bytes':base_config['target_bytes'],
        'height_lock_sha256':sha(args.height_lock),'height_raster_sha256':sha(args.height_raster),
        'cnbh_raster_sha256':sha(args.cnbh_raster),'cmab_manifest_sha256':sha(args.cmab_shards/'manifest.json'),
        'sampler_source_sha256':sha(args.city_source_dir/'building_height_sampler.py'),
        'raster_sampler_source_sha256':sha(args.city_source_dir/'raster_height_sampler.py'),
        'parent_residual_file_sha256':sha(args.parent_residuals),'landmark_exclusions_sha256':sha(args.landmark_exclusions),
        'exporter_source_sha256':sha(args.city_source_dir/'build_fullcity_models.py'),
        'mesh_writer_source_sha256':sha(args.city_source_dir/'build_district_models.py'),
        'roof_geometry_source_sha256':sha(args.city_source_dir/'roof_geometry.py'),
        'roof_geometry_version':getattr(geometry,'VERSION','roof-geometry-v1'),
        'roof_qualification_sha256':plan['qualification_sha256'],'qualification_schema_version':qualified['schema_version'],
        'qualification_input':qualified.get('input',{}),'qualification_policy':qualified.get('policy',{}),
        'base_manifest_sha256':plan['base_manifest_sha256'],'partition_policy':plan['partition_policy']}
    for key in ('sampler_version','height_lock_sha256','height_raster_sha256','cnbh_raster_sha256','cmab_manifest_sha256',
                'sampler_source_sha256','raster_sampler_source_sha256','mesh_writer_source_sha256'):
        if configuration[key] != base_config.get(key): raise ValueError(f'Base height/geometry lock differs: {key}')
    config_hash = hashlib.sha256(canonical(configuration).encode()).hexdigest()
    options = {**configuration,'output':str(args.output),'gltfpack':args.gltfpack,
        'height_raster':str(args.height_raster),'cnbh_raster':str(args.cnbh_raster),'cmab_shards':str(args.cmab_shards),
        'parent_residuals':str(args.parent_residuals),'landmark_exclusions':json.loads(args.landmark_exclusions.read_text()),
        'configuration_sha256':config_hash,'roof_overrides':overrides,
        'fixed_output_ids':{cell['id']:cell['superseded_output_ids'] for cell in plan['affected_owner_cells']}}
    write_json(args.output/'build-configuration.json',configuration)
    shutil.copy2(args.qualified_roofs,args.output/'qualified-roofs.json')
    records = []; errors = []
    with ProcessPoolExecutor(max_workers=max(1,args.workers)) as pool:
        jobs = {pool.submit(builder.export_source,cell['source_file'],options):cell for cell in plan['affected_owner_cells']}
        for future in as_completed(jobs):
            cell = jobs[future]
            try:
                future.result()
                cell_records, files = validate_cell(args.output,args.base_models,cell,config_hash,builder)
                records.extend(cell_records)
                print('ROOF_CELL_READY',json.dumps({'tile':cell['tile'],'models':[r['id'] for r in cell_records],
                    'qualified_roofs':len(cell['qualified_keys']),'files':files},ensure_ascii=False),flush=True)
            except Exception as error:
                failure={'cell':cell['id'],'error':str(error)}; errors.append(failure)
                print('ROOF_CELL_ERROR',json.dumps(failure),flush=True)
    if errors:
        write_json(args.output/'patch-manifest.json',{'version':VERSION,'complete':False,'errors':errors})
        raise SystemExit(1)
    records.sort(key=lambda record:record['id'])
    stats=[roof for record in records for roof in record.get('source_roof_enhancement',{}).get('roof_stats',[])]
    if len(stats)!=len(overrides) or {roof['key'] for roof in stats}!=set(overrides):
        raise ValueError('Final accepted roof coverage differs')
    manifest={**plan,'complete':True,'configuration_sha256':config_hash,'model_count':len(records),'records':records,
        'total_model_bytes':sum(record['size_bytes'] for record in records),'errors':[],
        'roofs_by_shape':dict(Counter(roof['roof_shape'] for roof in stats)),
        'roofs_by_district':dict(Counter(roof['district_id'] for roof in stats)),
        'scope':'Independent affected-owner patch only; not a whole-city manifest.'}
    write_json(args.output/'roof-validation.json',{'version':VERSION,'complete':True,'qualified_roof_count':len(stats),
        'qualification_sha256':plan['qualification_sha256'],'configuration_sha256':config_hash,
        'all_accepted_roofs_applied_exactly_once':True,'existing_partition_ids_preserved':True,
        'feature_counts_id_sidecars_heights_footprints_preserved':True,
        'roofs_by_shape':manifest['roofs_by_shape'],'roofs_by_district':manifest['roofs_by_district'],'roofs':stats})
    write_json(args.output/'patch-manifest.json',manifest)
    print('ROOF_PATCH_COMPLETE',json.dumps({'models':len(records),'roofs':len(stats),'bytes':manifest['total_model_bytes']}),flush=True)


if __name__ == '__main__': main()
