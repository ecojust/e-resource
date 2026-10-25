"""Refresh final detailed-model hashes without changing generic mesh provenance.

Architectural embellishments can change after coverage is frozen. If only model
file hashes/sizes change, preserve the exact exclusion configuration that built
the generic patch, and prove that the final runtime IDs and boundaries match it.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,shutil
from build_bund_city_patches import checked_glb,write_json,sha


def geometry_contract(data):
    return {'building_ids':data['building_ids'],'building_part_ids':data['building_part_ids'],
            'geometry_overrides':data.get('geometry_overrides',{}),
            'landmarks':[{k:r.get(k) for k in ['landmark_id','building_ids','building_part_ids','anchor','confirmed_boundary','source_geometry']}
                         for r in data['landmark_sources']]}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--patch',type=Path,required=True)
    p.add_argument('--confirmations',type=Path);a=p.parse_args()
    manifest_path=a.patch/'patch-manifest.json';manifest=json.loads(manifest_path.read_text())
    assert manifest['complete'],'Only finalize an otherwise completed and validated patch'
    manifest['complete']=False;manifest['status']='finalizing-detailed-model-metadata';write_json(manifest_path,manifest)
    current_path=a.patch/'bund-landmark-exclusions.json';config_path=a.patch/'build-configuration.json'
    config=json.loads(config_path.read_text());snapshot=a.patch/'bund-landmark-exclusions.generation-snapshot.json'
    if not snapshot.exists():shutil.copy2(current_path,snapshot)
    assert sha(snapshot)==config['landmark_exclusions_sha256'],'Generation configuration snapshot hash must match real mesh build inputs'
    generation=json.loads(snapshot.read_text());final=json.loads(current_path.read_text());changes=[]
    for model in final['confirmed_detailed_models']:
        actual=checked_glb(model['file'])
        if model['sha256']!=actual['sha256']:
            changes.append({'landmark_id':model['landmark_id'],'old_sha256':model['sha256'],'final_sha256':actual['sha256'],
                            'old_bytes':model['size_bytes'],'final_bytes':actual['size_bytes']})
        model.update(actual)
        row=next(r for r in final['landmark_sources'] if r['landmark_id']==model['landmark_id'])
        row['model_file']=actual['file'];row['model_sha256']=actual['sha256']
    original_contract=geometry_contract(generation);final_contract=geometry_contract(final)
    assert original_contract==final_contract,'IDs or footprint boundaries changed: this requires real tile rebuilding'
    contract_hash=hashlib.sha256(json.dumps(final_contract,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    final['model_metadata_finalized_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    final['generic_mesh_generation_snapshot']={'file':snapshot.name,'sha256':sha(snapshot),'ids_and_boundaries_unchanged':True,'geometry_contract_sha256':contract_hash}
    write_json(current_path,final)
    config['runtime_exclusions_sha256']=sha(current_path)
    config['generation_exclusions_snapshot']=snapshot.name
    config['runtime_metadata_only_refresh']=True
    write_json(config_path,config)
    report={'passed':True,'metadata_only':True,'generic_meshes_rebuilt':False,'generic_state_hashes_changed':False,
            'generation_exclusions_sha256':sha(snapshot),'final_runtime_exclusions_sha256':sha(current_path),
            'geometry_contract_sha256':contract_hash,'all_ids_and_boundaries_unchanged':True,'model_file_updates':changes,
            'note':'Mesh nodes and state configuration hashes retain the original generation snapshot. Final runtime records reference the frozen detailed models; no dependency hash is falsely migrated.'}
    write_json(a.patch/'model-metadata-finalization.json',report)
    if a.confirmations:
        table=json.loads(a.confirmations.read_text());table['status']='final models frozen and metadata verified'
        for item in table['models']:
            match=next(m for m in final['confirmed_detailed_models'] if m['candidate_id']==item['candidate_id'])
            item['final_source_glb_sha256']=match['sha256'];item['final_source_glb_bytes']=match['size_bytes']
        write_json(a.confirmations,table)
    manifest.update({'complete':True,'status':'complete','generation_exclusions_sha256':sha(snapshot),
                     'exclusions_sha256':sha(current_path),'model_metadata_finalization_file':'model-metadata-finalization.json'})
    write_json(manifest_path,manifest);print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
