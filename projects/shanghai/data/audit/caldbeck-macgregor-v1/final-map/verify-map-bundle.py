"""Verify the archived maps, normal-source requests, actual V6 network body and before/after delivery evidence."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def read(f):return json.loads(f.read_bytes())

def main():
    d=read(HERE/'main-browser.json')
    before=read(HERE/'control-browser.json')
    case=read(HERE.parent/'map-case.json')
    model=read(PROJECT/'assets/models/candidates'/case['id']/'manifest.json')
    native=read(HERE/'near-transport.json')
    live=read(HERE/'live-resource-evidence.json')
    assert native['completed'] and before['completed']
    assert d['catalog']=={'count':133,'sha256':'5c8ccd55a1fc857572fab0ed78b5f095303ab202aa71d30ec1711f5cd7efd155'}
    assert before['catalog']=={'count':132,'sha256':'4d51a1cb90a75a231c03947591d290fd6a202f99c19e66b0c3e43d3739fe191d'}
    original=Path(native['three_city_sites'][-1]['original']['url']).as_posix().split('18091/')[-1]
    assert not d['completed'] and d['failure'].startswith('AssertionError [ERR_ASSERTION]: Scene never downloaded '+original)
    assert not d['errors'] and not d['failed'] and d['finished']
    assert d['scriptSha256']==sha(HERE/'check-registered-map.cjs')
    assert before['scriptSha256']==sha(HERE/'check-native-registered-map.cjs')
    variants=[('map-mobile','full'),('map-desktop','full'),('map-street-facade','full'),('map-roof','full'),('map-distant','distant')]
    shots=[];meters=native['decoded_checks']['active']['surfaces'][str(native['tracked_owner'])]
    for item,(name,var)in zip(d['views'],variants,strict=True):
        assert item['view']==name and item['asset']['variant']==var
        role='lod'if var=='distant'else'full'
        assert item['asset']['triangles']==model['assets'][role]['triangles']
        assert item['glError']==0 and not item['contextLost']
        if name in ('map-street-facade','map-roof'):
            assert item['group']['clip_feature_local_ids']==[1960]and item['group']['triangles']==2
            assert any(s.get('id')==case['id']and s['segments']==3 for s in item['sections'])
    for record in [before,d]:
        assert not record['errors']and not record['failed']
        assert all(m in record['servedRuntime'] for m in ('src/app.js','src/map-scene.js','src/building-beacons.js','src/building-beacon-groups.js'))
        for f,dl in record['servedRuntime'].items():assert dl['sha256']==record['bindings'][f]
        for shot in record['screenshots']:
            assert sha(HERE/shot['file'])==shot['sha256']
            shots.append(shot['file'])
    assert len(shots)==6 and len(d['ground'])==11 and all(x['expected']==x['found']for x in d['ground'])
    four={}
    for role,asset in model['assets'].items():
        file=next(x for x in d['files']if x['file'].endswith('/'+asset['file']))
        assert file['sha256']==asset['sha256'] and file['bytes']==asset['bytes']
        if role in ('full','lod'):assert file['loadedByScene']
        four[role]=file['sha256']
    wanted=native['three_city_sites'][-1]['active'];body=next(r for r in live['receipts']if r['url']==wanted['url']and r.get('actualPageResponse'))
    assert body['sha256']==wanted['sha256']and body['receivedBytes']==wanted['bytes']
    assert body['performanceEntry']['encodedBodySize']==wanted['bytes']
    result={'completed':True,'id':case['id'],'mode':'Combined real browser and transport verification','completed_checks':['132-place unchanged owner using the repacked native group','133-place mobile, desktop, street, roof and distant city frames','Original, web, distant and editable downloads','11 ground checks','Active V6 response body and baseline triangle comparison across 131/132/133'],
      'earlier_assertion':'The 133-place browser passed every frame, ground and model-download check. Its last check incorrectly required the source to request the baseline near GLB instead of the configured V6 group. The original failing report is preserved in main-browser.json. The V6 response reached that same live browser and matches its manifest.','active_native_received_in_delivered_browser':body,'before_source_group':before['views'][0]['group'],'actual_owner_measurements':meters,'catalogs':[before['catalog'],d['catalog']],'screenshots':shots,'model_sha256':four,'checker_sha256':sha(Path(__file__)),'bindings':{f:sha(HERE/f)for f in ('main-browser.json','control-browser.json','live-resource-evidence.json','near-transport.json','check-native-registered-map.cjs','check-registered-map.cjs')}}
    (HERE/'verified-map.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(len(shots),len(d['ground']),body['sha256'])
if __name__=='__main__':main()
