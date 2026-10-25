"""Independent publication audit for a completed full-city model directory."""
from pathlib import Path
from collections import Counter
import argparse, gzip, hashlib, json, struct


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def audit(raw,models):
    manifest=json.loads((models/'manifest.json').read_text())
    source=json.loads((raw/'manifest.json').read_text())
    assert manifest['complete'] and source['complete'],'Both manifests must be complete'
    records={p.stem:json.loads(p.read_text()) for p in (models/'records').glob('*.json')}
    assert len(records)==manifest['model_count']==len(manifest['tiles'])
    assert {r['id'] for r in manifest['tiles']}==set(records)
    triangles=0;size=0;quality=Counter();districts=Counter();largest=0
    for key,r in records.items():
        path=models/r['file'];ids_path=models/r['feature_ids_file']
        assert path.stat().st_size==r['size_bytes']<100_000_000,key
        assert ids_path.stat().st_size==r['feature_ids_size_bytes']<100_000_000,key
        assert digest(path)==r['sha256'] and digest(ids_path)==r['feature_ids_sha256'],key
        with path.open('rb') as f:
            magic,version,total,jsonsize,kind=struct.unpack('<4sIIII',f.read(20))
            assert magic==b'glTF' and version==2 and total==r['size_bytes'] and kind==0x4e4f534a,key
            document=json.loads(f.read(jsonsize))
            binsize,binkind=struct.unpack('<II',f.read(8))
            assert binkind==0x004e4942 and 28+jsonsize+binsize==total,key
        count=sum(document['accessors'][p['indices']]['count']//3 for m in document['meshes'] for p in m['primitives'])
        assert count==r['triangles'],key
        assert any('walls' in m.get('name','').lower() for m in document['materials']),key
        if r['compression']['type']!='none':
            assert 'EXT_meshopt_compression' in document.get('extensionsRequired',[]),key
        triangles+=count;size+=r['size_bytes'];largest=max(largest,r['size_bytes'])
        quality.update(r['height_quality'])
        for code,d in r['district_counts'].items():districts[code]+=d['features']
    modeled=sum(districts.values());replaced=0;residuals=0;source_renderable=0;source_features=0
    used=set();states=list((models/'state').glob('*.json'));ids_checked=0
    for state_path in states:
        state=json.loads(state_path.read_text());z,x,y=state['tile']
        raw_path=raw/'tiles'/str(z)/str(x)/(str(y)+'.geojson.gz')
        assert digest(raw_path)==state['source_sha256'],state_path
        with gzip.open(raw_path,'rt') as f:features=json.load(f)['features']
        original={'building':set(),'building_part':set()};allowed={'building':set(),'building_part':set()}
        for feat in features:
            props=feat['properties'];layer=props.get('source_layer','building');identity=str(props['id'])
            original[layer].add(identity);allowed[layer].add(identity)
            if layer=='building_part' and props.get('building_id'):allowed['building'].add(str(props['building_id']))
        actual={'building':set(),'building_part':set()}
        for key in state['models']:
            assert key in records and key not in used,key
            used.add(key);r=records[key]
            assert r['source_sha256']==state['source_sha256'],key
            ids=json.loads((models/r['feature_ids_file']).read_text())
            for layer in actual:actual[layer].update(ids[layer])
        # An empty cell may contain only a suppressed parent or custom landmark.
        # It needs no generic mesh and therefore no overlap suppression sidecar.
        if state['models']:
            for layer in actual:
                assert original[layer]<=actual[layer],(state_path,'missing source IDs',len(original[layer]-actual[layer]))
                assert actual[layer]<=allowed[layer],(state_path,'unknown feature IDs')
                ids_checked+=len(original[layer])
        assert len(features)==state['source_feature_count'],state_path
        source_features+=len(features);source_renderable+=state['source_renderable_count']
        replaced+=sum(state['landmark_replacement_counts'].values())
        residuals+=sum(state.get('residual_parent_counts',{}).values())
    assert used==set(records),'Orphan or multiply assigned output record'
    assert triangles==manifest['triangle_count'] and size==manifest['total_model_bytes']
    assert dict(quality)==manifest['height_quality']
    assert source_features==source['unique_feature_count']
    assert modeled+replaced==source_renderable+residuals
    assert source_renderable==source['renderable_feature_count']
    for d in source['districts']:
        matching=next(x for x in manifest['districts'] if x['id']==d['id'])
        assert districts[d['id']]+matching['landmark_replacement_count']==d['renderable_count']+matching.get('residual_parent_features',0),d['id']
    return {'passed':True,'source_tiles':len(states),'model_count':len(records),
            'source_features':source_features,'modeled_features':modeled,'landmark_replaced_features':replaced,
            'restored_parent_residual_features':residuals,
            'sidecar_source_ids_checked':ids_checked,'triangles':triangles,'total_glb_bytes':size,
            'maximum_glb_bytes':largest,'height_quality':dict(quality),
            'checks':['SHA256 for every GLB and ID sidecar','GLB2 headers and exact JSON/BIN lengths',
                      'index triangle count and meshopt requirement','all raw hashes and ID sidecar membership',
                      'one output ownership per tile record','all 16 district source/model/replacement counts']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--raw',type=Path,required=True);p.add_argument('--models',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=audit(a.raw,a.models)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
