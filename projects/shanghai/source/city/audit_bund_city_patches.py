"""Read-only base audit and metadata-only merge preview for the Bund patch."""
from pathlib import Path
import argparse,gzip,hashlib,json,shutil,sys
from shapely.geometry import shape


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('base-models','raw','patch','base-exclusions','city-source-dir','output'):
        p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();patch=json.loads((a.patch/'patch-manifest.json').read_text())
    assert patch['complete'] and not patch['errors']
    assert sha(a.base_models/'manifest.json')==patch['base_manifest_sha256'],'Base manifest changed since patch planning'
    base=json.loads(a.base_exclusions.read_text());new=json.loads((a.patch/'bund-landmark-exclusions.json').read_text())
    oldrows={r['landmark_id']:r for r in base['landmark_sources']};newrows={r['landmark_id']:r for r in new['landmark_sources']}
    unchanged=[key for key in oldrows if key!='customs-house']
    for key in unchanged:assert oldrows[key]==newrows[key],f'Unrelated landmark changed: {key}'
    expected=set(oldrows)|{'bund02','bund03','bund12','bund15','bund17','bund18','bund19','bund20','bund23'}
    assert set(newrows)==expected
    for row in newrows.values():
        assert shape(row['confirmed_boundary']).is_valid and not shape(row['confirmed_boundary']).is_empty
        assert row['source_geometry'] and row['building_ids']
    for layer in ('building','building_part'):
        union=set().union(*(set(r[layer+'_ids']) for r in newrows.values()))
        assert union==set(new[layer+'_ids']),f'Runtime/global ID sets differ for {layer}'
    assert len(newrows['customs-house']['building_ids'])==6
    assert not newrows['customs-house'].get('retained_uncertain')
    assert len(newrows['bund23']['building_ids'])==2 and len(newrows['bund23']['building_part_ids'])==1
    assert new['counts']['source_renderable_replaced']==98
    assert new['counts']['source_nonrenderable_replaced']==5
    changed_ids=set();source_ids_checked=0
    sys.path.insert(0,str(a.city_source_dir.resolve()));import build_fullcity_models as builder
    for cell in patch['affected_owner_cells']:
        identity='-'.join(map(str,cell['tile']));changed_ids.add(identity)
        state=json.loads((a.patch/'state'/(identity+'.json')).read_text())
        with gzip.open(cell['source_file'],'rt') as f:features=json.load(f)['features']
        expectedids={'building':set(),'building_part':set()};actual={'building':set(),'building_part':set()}
        allowed={'building':set(),'building_part':set()}
        for feat in features:
            pr=feat['properties'];layer=pr['source_layer'];expectedids[layer].add(pr['id']);allowed[layer].add(pr['id'])
            if pr.get('building_id'):allowed['building'].add(pr['building_id'])
        for model in state['models']:
            record=json.loads((a.patch/'records'/(model+'.json')).read_text())
            _,triangles=builder.validate_glb(a.patch/record['file'])
            assert triangles==record['triangles']
            assert sha(a.patch/record['file'])==record['sha256']
            assert sha(a.patch/record['feature_ids_file'])==record['feature_ids_sha256']
            ids=json.loads((a.patch/record['feature_ids_file']).read_text())
            for layer in actual:actual[layer].update(ids[layer])
        for layer in actual:
            assert expectedids[layer]<=actual[layer]<=allowed[layer]
            source_ids_checked+=len(expectedids[layer])
        # Original owner-cell assets remain byte-identical in the source base.
        for old_id in cell['superseded_output_ids']:
            old=json.loads((a.base_models/'records'/(old_id+'.json')).read_text())
            assert sha(a.base_models/old['file'])==old['sha256']
    # This preview contains metadata only. GLBs remain in base or patch trees.
    # Do not serve it as a city; it verifies aggregate bookkeeping before merge.
    preview=a.output.parent/'merged-metadata-preview'
    for sub in ('records','state'):
        target=preview/sub;target.mkdir(parents=True,exist_ok=True)
        for old in target.glob('*.json'):old.unlink()
        for file in (a.base_models/sub).glob('*.json'):
            item=json.loads(file.read_text())
            owner='-'.join(map(str,item['tile']))
            if owner not in changed_ids:shutil.copy2(file,target/file.name)
        for file in (a.patch/sub).glob('*.json'):shutil.copy2(file,target/file.name)
    merged=builder.build_manifest(preview,a.raw,True,[])
    assert merged['complete'] and merged['coverage_balanced']
    assert merged['model_count']==1708
    assert merged['feature_count']==1796419
    assert merged['landmark_replacement_count']==98 and merged['residual_parent_features']==401
    report={'passed':True,'affected_owner_cells':sorted(changed_ids),'runtime_landmark_records':len(newrows),
            'unchanged_landmark_records':unchanged,'runtime_ids_match_global_ids':True,
            'source_ids_checked_in_changed_cells':source_ids_checked,'base_model_assets_unchanged':True,
            'expected_merged_model_count':merged['model_count'],'expected_merged_feature_count':merged['feature_count'],
            'expected_merged_renderable_replacements':merged['landmark_replacement_count'],
            'expected_merged_restored_parent_residuals':merged['residual_parent_features'],
            'metadata_only_preview_manifest':str(preview/'manifest.json'),
            'note':'Metadata preview is not a served city directory. Apply the actual patch assets and states to the intended base, then regenerate its final manifest.'}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
