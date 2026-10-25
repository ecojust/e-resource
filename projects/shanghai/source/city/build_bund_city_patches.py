"""Rebuild only owner cells covered by completed, explicitly confirmed models.

This tool never edits the base city directory. Its output is a separate patch
set containing tiles/ids/records/state plus a patch manifest. The caller must
publish the detailed models before merging this patch set into the city.
"""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import argparse, datetime, gzip, hashlib, importlib, json, os, shutil, struct, sys
from shapely.geometry import shape,mapping
from shapely.ops import unary_union


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def write_json(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name('.'+path.name+'.tmp')
    temp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    os.replace(temp,path)


def checked_glb(path):
    path=Path(path)
    if not path.exists():raise ValueError(f'Confirmed model does not exist: {path}')
    if path.stat().st_size>=100_000_000:raise ValueError(f'Model exceeds GitHub per-file limit: {path}')
    with path.open('rb') as f:magic,version,length=struct.unpack('<4sII',f.read(12))
    if magic!=b'glTF' or version!=2 or length!=path.stat().st_size:raise ValueError(f'Invalid GLB2: {path}')
    return {'file':str(path),'size_bytes':length,'sha256':sha(path)}


def make_plan(args):
    candidates={c['id']:c for c in json.loads(args.candidates.read_text())['candidates']}
    base=json.loads(args.base_exclusions.read_text())
    confirmations=json.loads(args.confirmations.read_text())
    base_ids={k:set(base.get(k+'_ids',[])) for k in ('building','building_part')}
    requested={k:set() for k in base_ids};models=[]
    for confirm in confirmations.get('models',[]):
        if confirm.get('coverage_confirmed') is not True:continue
        key=confirm['candidate_id']
        if key not in candidates:raise ValueError(f'Unknown candidate: {key}')
        candidate=candidates[key]
        file=Path(confirm['glb'])
        if not file.is_absolute():file=args.confirmations.parent/file
        info=checked_glb(file)
        if confirm.get('scope')!='entire_candidate_footprint':
            raise ValueError(f'{key}: partial models require an explicit geometric difference workflow; never delete an entire source by radius')
        selected={k:set(candidate['replacement'].get(k+'_ids',[])) for k in requested}
        boundaries=[shape(candidate['geometry'])]
        optional={g['id']:g for g in candidate['replacement'].get('optional_groups',[])}
        for group in confirm.get('included_optional_groups',[]):
            if group not in optional:raise ValueError(f'{key}: unknown optional group {group}')
            for layer in selected:selected[layer].update(optional[group].get(layer+'_ids',[]))
            if optional[group].get('confirmed_boundary_geometry'):
                boundaries.append(shape(optional[group]['confirmed_boundary_geometry']))
            elif group=='bank-west-wing':
                boundaries.append(shape(candidate['related_geometries']['western_wing']['geometry']))
            elif group=='customs-roof-components':
                components=json.loads((args.candidates.parent/'customs-components.json').read_text())['components']
                boundaries.extend(shape(c['geometry']) for c in components)
            else:raise ValueError(f'{key}: optional group has no exact confirmed geometry: {group}')
        for layer in requested:requested[layer].update(selected[layer])
        boundary=mapping(unary_union(boundaries))
        models.append({'candidate_id':key,'landmark_id':confirm.get('landmark_id') or ('customs-house' if key=='bund13' else key),
                       'name':candidate['name_zh'],**info,
                       'scope':confirm['scope'],'coverage_statement':confirm.get('coverage_statement'),
                       'included_optional_groups':confirm.get('included_optional_groups',[]),
                       'anchor':[candidate['origin_longitude'],candidate['origin_latitude']],
                       'osm_url':candidate['osm']['url'],'source_geometry':boundary,'confirmed_boundary':boundary,
                       'building_ids':sorted(selected['building']),'building_part_ids':sorted(selected['building_part'])})
    if not models:raise ValueError('No completed models with coverage_confirmed:true; no exclusions or tiles will be written')
    combined={k:base_ids[k]|requested[k] for k in requested}
    new_buildings=requested['building']-base_ids['building']
    found={k:set() for k in requested};owners={};affected={};counts={'renderable':0,'nonrenderable':0};matches={}
    # One read-only global scan ensures that linked parts in adjacent owner
    # cells are included. Only affected cells are ever rebuilt.
    paths=sorted((args.raw/'tiles').rglob('*.geojson.gz'))
    for path in paths:
        with gzip.open(path,'rt',encoding='utf8') as f:collection=json.load(f)
        tile=collection['metadata']['tile'];cell='-'.join(map(str,tile))
        for feat in collection['features']:
            p=feat['properties'];layer=p.get('source_layer','building');identity=str(p['id'])
            linked=layer=='building_part' and p.get('building_id') in new_buildings
            if linked:
                requested['building_part'].add(identity);combined['building_part'].add(identity)
                for model in models:
                    if p.get('building_id') in model['building_ids'] and identity not in model['building_part_ids']:
                        model['building_part_ids'].append(identity)
            if identity in combined[layer]:
                counts['nonrenderable' if p.get('renderable') is False else 'renderable']+=1
            if identity in requested[layer]:
                found[layer].add(identity);owners[layer+':'+identity]=tile
                matches[layer+':'+identity]={'id':identity,'source_layer':layer,'building_id':p.get('building_id'),
                                            'source_record_ids':[s.get('record_id') for s in p.get('sources',[]) if s.get('record_id')],
                                            'source_renderable':p.get('renderable') is not False,'source_geometry':feat['geometry'],
                                            'reason':'completed detailed model covers confirmed mapped footprint/component',
                                            'owner_tile':tile}
            if identity in requested[layer]-base_ids[layer]:
                entry=affected.setdefault(cell,{'tile':tile,'source_file':str(path),'source_sha256':sha(path),'changed_ids':{'building':[],'building_part':[]}})
                entry['changed_ids'][layer].append(identity)
    for layer in requested:
        missing=requested[layer]-found[layer]
        if missing:raise ValueError(f'Confirmed replacement source IDs missing from raw archive: {layer}: {sorted(missing)}')
    base_manifest=json.loads((args.base_models/'manifest.json').read_text())
    for cell,entry in affected.items():
        state=args.base_models/'state'/(cell+'.json')
        if state.exists():entry['superseded_output_ids']=json.loads(state.read_text())['models']
        else:entry['superseded_output_ids']=[r['id'] for r in base_manifest['tiles'] if r['tile']==entry['tile']]
    landmark_sources={record['landmark_id']:record for record in base.get('landmark_sources',[])}
    for model in models:
        record=dict(landmark_sources.get(model['landmark_id'],{}))
        for k in ('landmark_id','name','anchor','osm_url','source_geometry','confirmed_boundary'):
            record[k]=model[k]
        for layer in requested:
            record[layer+'_ids']=sorted(set(record.get(layer+'_ids',[]))|set(model[layer+'_ids']))
        record['matches']=[matches[layer+':'+identity] for layer in requested for identity in record[layer+'_ids'] if layer+':'+identity in matches]
        record['replacement_scope']='Entire mapped candidate footprint plus explicitly confirmed optional components; no radius deletion.'
        record['model_file']=model['file'];record['model_sha256']=model['sha256']
        covered=set(record['building_ids'])|set(record['building_part_ids'])
        if 'retained_uncertain' in record:record['retained_uncertain']=[r for r in record['retained_uncertain'] if r['id'] not in covered]
        landmark_sources[model['landmark_id']]=record
    caveats=list(base.get('caveats',[]))
    if any(m['landmark_id']=='customs-house' and 'customs-roof-components' in m['included_optional_groups'] for m in models):
        caveats=[c for c in caveats if not c.startswith('Five small overlapping Customs House')]
        caveats.append('Customs clock body and four roof pavilions are now confirmed using exact shared OSM nodes, photographs and complete detailed-model coverage; the western rear wing remains separate.')
    exclusions={**base,'schema_version':'bund-detail-confirmed-v3',
                'generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'building_ids':sorted(combined['building']),'building_part_ids':sorted(combined['building_part']),
                'excluded_keys':[layer+':'+identity for layer in combined for identity in sorted(combined[layer])],
                'base_exclusions_sha256':sha(args.base_exclusions),'confirmed_detailed_models':models,
                'landmark_sources':list(landmark_sources.values()),'caveats':caveats,
                'counts':{'building_ids':len(combined['building']),'building_part_ids':len(combined['building_part']),
                          'source_renderable_replaced':counts['renderable'],'source_nonrenderable_replaced':counts['nonrenderable']},
                'validation':{'complete_raw_archive_scan':True,'linked_parts_closed':True,'only_completed_models_confirmed':True,'radius_deletion':False},
                'consumer_contract':'Preserve exact IDs in sidecars. Rebuild only listed owner cells. Existing unrelated cell state/configuration hashes stay unchanged.'}
    plan={'version':1,'status':'confirmed-models-ready','base_manifest_sha256':sha(args.base_models/'manifest.json'),
          'base_exclusions_sha256':sha(args.base_exclusions),'confirmed_models':models,'affected_owner_cells':list(affected.values()),
          'new_replacement_ids':{k:sorted(requested[k]-base_ids[k]) for k in requested},
          'source_owners':owners,'unmodified_base_directory':str(args.base_models),
          'scope':'Only these source owner cells will be regenerated. No global state/configuration migration.'}
    return exclusions,plan


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('raw','base-models','base-exclusions','candidates','confirmations','output','height-raster','cnbh-raster','cmab-shards','height-lock','parent-residuals'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--city-source-dir',type=Path,default=Path(__file__).resolve().parent)
    p.add_argument('--gltfpack',default=os.environ.get('GLTFPACK') or shutil.which('gltfpack'))
    p.add_argument('--workers',type=int,default=2)
    p.add_argument('--export',action='store_true',help='Export the confirmed patch set; without this flag writes a reviewable plan only')
    a=p.parse_args()
    if a.output.resolve().is_relative_to(a.raw.resolve()) or a.output.resolve().is_relative_to(a.base_models.resolve()):
        p.error('Patch output must be outside the source and base model directory trees')
    a.output.mkdir(parents=True,exist_ok=True)
    # Invalidate an earlier success marker before any new plan/configuration
    # can replace it. Any exception thereafter leaves a non-publishable patch.
    write_json(a.output/'patch-manifest.json',{'complete':False,'status':'planning-or-building','scope':'patch only; do not merge until final validation succeeds'})
    exclusions,plan=make_plan(a)
    exclusions_path=a.output/'bund-landmark-exclusions.json'
    write_json(exclusions_path,exclusions);write_json(a.output/'patch-plan.json',plan)
    print(json.dumps({'planned_cells':len(plan['affected_owner_cells']),'confirmed_models':len(plan['confirmed_models']),'export':a.export}),flush=True)
    if not a.export:return
    if not a.gltfpack:p.error('gltfpack is required for compressed patch assets')
    sys.path.insert(0,str(a.city_source_dir.resolve()))
    builder=importlib.import_module('build_fullcity_models')
    lock=json.loads(a.height_lock.read_text())
    configuration={'build_version':builder.VERSION,'sampler_version':lock['sampler_version'],'compress':True,'target_bytes':9_000_000,
                   'height_lock_sha256':sha(a.height_lock),'landmark_exclusions_sha256':sha(exclusions_path),
                   'height_raster_sha256':sha(a.height_raster),'cnbh_raster_sha256':sha(a.cnbh_raster),
                   'cmab_manifest_sha256':sha(a.cmab_shards/'manifest.json'),
                   'sampler_source_sha256':sha(a.city_source_dir/'building_height_sampler.py'),
                   'raster_sampler_source_sha256':sha(a.city_source_dir/'raster_height_sampler.py')}
    options={**configuration,'output':str(a.output),'gltfpack':a.gltfpack,
             'height_raster':str(a.height_raster),'cnbh_raster':str(a.cnbh_raster),'cmab_shards':str(a.cmab_shards),
             'landmark_exclusions':exclusions,'parent_residuals':str(a.parent_residuals),
             'configuration_sha256':hashlib.sha256(json.dumps(configuration,sort_keys=True).encode()).hexdigest()}
    write_json(a.output/'build-configuration.json',configuration)
    results=[];errors=[]
    with ProcessPoolExecutor(max_workers=max(1,a.workers)) as pool:
        jobs={pool.submit(builder.export_source,cell['source_file'],options):cell for cell in plan['affected_owner_cells']}
        for future in as_completed(jobs):
            try:results.append(future.result());print(json.dumps(results[-1]),flush=True)
            except Exception as exc:errors.append({'cell':jobs[future]['tile'],'error':str(exc)})
    if errors:
        write_json(a.output/'patch-manifest.json',{'complete':False,'scope':'failed patch; do not merge','errors':errors})
        raise SystemExit(json.dumps(errors))
    records=[];referenced=set();active_states=set()
    for cell in plan['affected_owner_cells']:
        state_id='-'.join(map(str,cell['tile']));active_states.add(state_id)
        state=json.loads((a.output/'state'/(state_id+'.json')).read_text())
        if state['source_sha256']!=cell['source_sha256'] or state['configuration_sha256']!=options['configuration_sha256']:
            raise ValueError(f'Stale source state in patch output: {state_id}')
        for identity in state['models']:
            if identity in referenced:raise ValueError(f'Duplicate patch output ownership: {identity}')
            record=json.loads((a.output/'records'/(identity+'.json')).read_text())
            if record['tile']!=cell['tile']:raise ValueError(f'Output assigned to wrong owner: {identity}')
            referenced.add(identity);records.append(record)
    # A repeated run may change subdivisions or confirmed cell membership.
    # Prune only obsolete generated assets in this independent patch directory;
    # never let old unrelated records leak into the new patch manifest/merge.
    pruned=[]
    for path in (a.output/'records').glob('*.json'):
        if path.stem in referenced:continue
        old=json.loads(path.read_text())
        for field,folder in [('file','tiles'),('feature_ids_file','ids')]:
            asset=(a.output/old[field]).resolve()
            if not asset.is_relative_to((a.output/folder).resolve()):raise ValueError(f'Unexpected stale asset path: {asset}')
            asset.unlink(missing_ok=True)
        pruned.append(path.stem);path.unlink()
    for path in (a.output/'state').glob('*.json'):
        if path.stem not in active_states:path.unlink()
    for record in records:
        doc,triangles=builder.validate_glb(a.output/record['file'])
        assert triangles==record['triangles'] and sha(a.output/record['file'])==record['sha256']
        assert sha(a.output/record['feature_ids_file'])==record['feature_ids_sha256']
    manifest={'version':1,'complete':not errors and len(results)==len(plan['affected_owner_cells']),
              'scope':'Patch only; never substitute this for the whole-city manifest',
              'base_manifest_sha256':plan['base_manifest_sha256'],'exclusions_sha256':sha(exclusions_path),
              'affected_owner_cells':plan['affected_owner_cells'],'model_count':len(records),
              'pruned_stale_patch_output_ids':pruned,
              'total_model_bytes':sum(r['size_bytes'] for r in records),'records':records,'errors':errors,
              'merge_instructions':['Publish confirmed detailed models first.','Replace only listed old owner-cell tiles/ids/records/state; remove superseded output IDs absent from this patch.','Keep every unrelated state/config hash unchanged.','Merge detailed exclusions and call build_fullcity_models.build_manifest on the combined base directory with the original raw source; rerun full-city audit.']}
    write_json(a.output/'patch-manifest.json',manifest)
    if errors:raise SystemExit(json.dumps(errors))
    print('PATCH_COMPLETE',len(records),'models',manifest['total_model_bytes'],'bytes',flush=True)


if __name__=='__main__':main()
