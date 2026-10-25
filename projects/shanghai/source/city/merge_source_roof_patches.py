"""Merge a validated roof patch into a new isolated city directory.

No repository, base asset, exclusion file or preview symlink is changed.
Existing detail_patch metadata is preserved. Immutable unchanged GLBs/ID
sidecars may be hard-linked; metadata is always copied before recomputation.
"""
from pathlib import Path
from collections import Counter
import argparse, json, os, shutil
from build_source_roof_patches import (VERSION, independent, load_builder,
    safe_asset, sha, validate_cell, write_json)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('base-models','patch','output','raw'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--city-source-dir',type=Path,default=Path(__file__).resolve().parent)
    parser.add_argument('--published-raw-path',help='Optional project-relative path; otherwise retain the current base manifest value')
    args = parser.parse_args()
    base=args.base_models.resolve(); patch_dir=args.patch.resolve(); out=args.output.resolve()
    independent(out,base,patch_dir,args.raw)
    if out.exists() and any(out.iterdir()): parser.error('Use a new empty merged output directory')
    patch=json.loads((patch_dir/'patch-manifest.json').read_text())
    old=json.loads((base/'manifest.json').read_text())
    if patch.get('version')!=VERSION or patch.get('complete') is not True:
        raise ValueError('Roof patch is incomplete or has an unsupported version')
    if sha(base/'manifest.json')!=patch['base_manifest_sha256']:
        raise ValueError('Base manifest changed after patch planning')
    if sha(patch_dir/'qualified-roofs.json')!=patch['qualification_sha256']:
        raise ValueError('Qualification document changed after patch generation')
    builder=load_builder(args.city_source_dir)
    records=[]
    for cell in patch['affected_owner_cells']:
        if sha(base/'state'/(cell['id']+'.json'))!=cell['base_state_sha256']:
            raise ValueError(f'Base owner state changed: {cell["id"]}')
        checked,_=validate_cell(patch_dir,base,cell,patch['configuration_sha256'],builder)
        records.extend(checked)
    by_id={record['id']:record for record in records}
    if len(by_id)!=len(records) or sorted(records,key=lambda r:r['id'])!=patch['records']:
        raise ValueError('Patch records differ from their current metadata files')
    if old['model_count']!=patch['base_model_count'] or old['feature_count']!=patch['base_feature_count']:
        raise ValueError('Base model/feature totals changed')
    out.mkdir(parents=True,exist_ok=True)
    linked=copied=0
    for item in base.iterdir():
        if item.name.startswith('.') or item.name in ('COMPLETE','manifest.json'): continue
        target=out/item.name
        if item.is_dir():
            target.mkdir(exist_ok=True)
            for source in item.rglob('*'):
                dest=target/source.relative_to(item)
                if source.is_dir(): dest.mkdir(exist_ok=True); continue
                dest.parent.mkdir(parents=True,exist_ok=True)
                if item.name in ('tiles','ids'):
                    try: os.link(source,dest); linked+=1
                    except OSError: shutil.copy2(source,dest); copied+=1
                else: shutil.copy2(source,dest); copied+=1
        else: shutil.copy2(item,target); copied+=1
    replaced=[]
    # Copy only explicitly validated active patch files; stale resumed exports
    # cannot leak into the merged city's records or ownership state.
    for record in records:
        for name in (record['file'],record['feature_ids_file'],'records/'+record['id']+'.json'):
            source=safe_asset(patch_dir,name); dest=safe_asset(out,name)
            dest.parent.mkdir(parents=True,exist_ok=True); dest.unlink(missing_ok=True)
            shutil.copy2(source,dest); replaced.append(name)
    for cell in patch['affected_owner_cells']:
        name='state/'+cell['id']+'.json'; dest=out/name
        dest.unlink(missing_ok=True); shutil.copy2(patch_dir/name,dest); replaced.append(name)
    for name in ('build-configuration.json','qualified-roofs.json','patch-plan.json','patch-manifest.json','roof-validation.json'):
        shutil.copy2(patch_dir/name,out/('source-roof-patch-'+name))
    # Preserve non-derived release metadata (including the existing detail_patch)
    # while recomputing every count and every changed record from actual files.
    manifest={**old,**builder.build_manifest(out,args.raw,True,[])}
    invariant_keys=('model_count','feature_count','building_footprints','building_parts','processed_source_tiles',
        'source_feature_count','source_renderable_count','landmark_replacement_count','landmark_geometry_override_count',
        'residual_parent_features','residual_parent_area_m2','residual_parent_height_quality','nonrenderable_parent_count',
        'height_quality','geometry_sources','excluded_underground_count','districts')
    if not manifest['complete'] or not manifest['coverage_balanced']:
        raise ValueError('Merged city failed complete coverage reconciliation')
    for key in invariant_keys:
        if manifest[key]!=old[key]: raise ValueError(f'Unexpected whole-city invariant change: {key}')
    manifest['source_raw_directory']=args.published_raw_path or old.get('source_raw_directory',str(args.raw))
    if args.published_raw_path: manifest['source_raw_directory_base']='project root'
    roof_stats=[roof for record in manifest['tiles'] for roof in record.get('source_roof_enhancement',{}).get('roof_stats',[])]
    keys=[roof['key'] for roof in roof_stats]
    if len(keys)!=len(set(keys)): raise ValueError('A source-qualified roof was emitted more than once')
    manifest['source_roof_enhancement']={'version':VERSION,'count':len(keys),'qualified_keys':sorted(keys),
        'roofs_by_shape':dict(Counter(roof['roof_shape'] for roof in roof_stats)),
        'roofs_by_district':dict(Counter(roof['district_id'] for roof in roof_stats)),
        'patch_qualification_sha256':patch['qualification_sha256'],'patch_configuration_sha256':patch['configuration_sha256'],
        'affected_owner_cells':[cell['tile'] for cell in patch['affected_owner_cells']],
        'original_footprint_topology_and_feature_ids_preserved':True,
        'existing_partition_ids_and_detail_patch_preserved':True,
        'source':'Source roof tags matched to exact OSM record versions and unchanged cached Overture footprints; see source-roof-patch-qualified-roofs.json.'}
    if old.get('detail_patch')!=manifest.get('detail_patch'):
        raise ValueError('Existing detailed-landmark patch metadata changed')
    old_by_id={record['id']:record for record in old['tiles']}
    for record in manifest['tiles']:
        identity=record['id']
        if identity not in by_id:
            if record!=old_by_id[identity] or sha(out/'records'/(identity+'.json'))!=sha(base/'records'/(identity+'.json')):
                raise ValueError(f'Unrelated tile metadata changed: {identity}')
        for file_key,hash_key in [('file','sha256'),('feature_ids_file','feature_ids_sha256')]:
            if sha(safe_asset(out,record[file_key]))!=record[hash_key]:
                raise ValueError(f'Merged asset hash mismatch: {identity}/{file_key}')
    affected={cell['id'] for cell in patch['affected_owner_cells']}
    for path in (base/'state').glob('*.json'):
        if path.stem not in affected and sha(path)!=sha(out/'state'/path.name):
            raise ValueError(f'Unrelated owner state changed: {path.name}')
    # Preserve existing per-district descriptive metadata, update only derived
    # fields and all asset references/checksums from the merged manifest.
    for district in manifest['districts']:
        did=district['id']; index_path=out/'districts'/(did+'.json')
        index=json.loads(index_path.read_text()) if index_path.exists() else {}
        old_tiles={tile['id']:tile for tile in index.get('tiles',[])}
        index.update({'district_id':did,'district_name':district['name'],'model_features':district['features'],
            'tiles':[{**old_tiles.get(tile['id'],{}),'id':tile['id'],'file':'../'+tile['file'],
                'feature_ids_file':'../'+tile['feature_ids_file'],'sha256':tile['sha256'],'bytes':tile['size_bytes'],
                'feature_ids_sha256':tile['feature_ids_sha256'],'feature_ids_bytes':tile['feature_ids_size_bytes'],
                'district_features':tile['district_counts'][did]['features']}
                for tile in manifest['tiles'] if did in tile['district_counts']]})
        write_json(index_path,index)
    write_json(out/'manifest.json',manifest)
    if sha(base/'manifest.json')!=patch['base_manifest_sha256']:
        raise ValueError('Original base manifest was modified')
    for cell in patch['affected_owner_cells']:
        if sha(base/'state'/(cell['id']+'.json'))!=cell['base_state_sha256']:
            raise ValueError('Original owner state was modified')
        for identity in cell['superseded_output_ids']:
            original=old_by_id[identity]
            if sha(safe_asset(base,original['file']))!=original['sha256']:
                raise ValueError('Original base model was modified')
    report={'version':VERSION,'complete':True,'base_manifest_sha256':patch['base_manifest_sha256'],
        'merged_manifest_sha256':sha(out/'manifest.json'),'model_count':manifest['model_count'],
        'feature_count':manifest['feature_count'],'roof_enhancement_count':len(keys),
        'linked_immutable_files':linked,'copied_metadata_files':copied,'replaced_files':replaced,
        'base_assets_unchanged':True,'unrelated_records_and_states_unchanged':True,
        'existing_detail_patch_preserved':True,'preview_symlink_modified':False,
        'district_indexes':[{'file':'districts/'+d['id']+'.json','sha256':sha(out/'districts'/(d['id']+'.json'))} for d in manifest['districts']]}
    write_json(out/'source-roof-patch-merge-report.json',report)
    (out/'COMPLETE').write_text('Complete isolated city with source-qualified roof patches.\n')
    print('ROOF_MERGE_COMPLETE',json.dumps(report,ensure_ascii=False),flush=True)


if __name__=='__main__': main()
