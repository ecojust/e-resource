"""Read each ordinary release's approved runtime and bind the archive to the actual four downloads."""
from pathlib import Path
import json, sys
from urllib.request import urlopen

HERE=Path(__file__).resolve().parent
AUDIT=Path('/workspace/e-resource/projects/shanghai/data/audit/chen-bingqian-historic-residence-v1')
SOURCE=Path('/workspace/e-resource/projects/shanghai/source/precise/jingan-chen-bingqian-historic-residence/reference-review.json')
TOP=Path('/tmp/shanghai-yongjia-porch')
sys.path.insert(0,str(TOP))
from common import read, save, canon, sha, full

target='jingan-chen-bingqian-historic-residence'
prior='xuhui-huaihai-road-1634-residence'
catalog='data/candidate-city-integrations.json'
original=read(AUDIT/'viewer.json')
contract=read(AUDIT/'final-placement-contract.json')
proof=read(AUDIT/'final-marker-status.json')
assert proof['geometry'] is None and (proof['clip_count'],proof['collisions'],proof['visible_city_models'])==(0,0,0)
assert original['passed'] and len(original['views'])==len(original['downloads'])==4
origins={};rows=[];generic=['index.html','landmarks.html','src/app.js','src/map-scene.js',*proof['runtime_signature']]
for n,num in [(217,254),(218,255)]:
    cmp=read(TOP/'scenes'/f'{n}-comparison.json')
    snapshot=full(n);signature=sha(canon(snapshot))
    assert cmp['passed'] and signature==cmp['production_receipt_sha256'] and snapshot['resulting_count']==num
    complete=read(TOP/'scenes'/f'{n}-all-http.json')
    assert complete['passed'] and complete['production_receipt_sha256']==signature and len(complete['ranges'])==5
    urls={row['path']:row['actual_url'] for row in cmp['files']}
    base=f'http://127.0.0.1:{31000+n}/'
    seen={}
    def get(path):
        url=base+urls.get(path,path)
        with urlopen(url, timeout=90) as response:
            assert response.status==200
            blob=response.read()
        digest=sha(blob)
        assert snapshot['files'][path]==digest,path
        seen[path]={'sha256':digest,'bytes':len(blob),'url':url}
        return blob
    cat=json.loads(get(catalog));rows.append(cat['models'])
    assert cat['resulting_city_count']==num and any(r['id']==prior for r in cat['models'])
    for path in generic:get(path)
    if n==217:assert not any(r['id']==target for r in rows[0])
    else:
        marker=rows[-1][-1];assert marker['id']==target and rows[0]==rows[1][:-1]
        assert cmp['previous_catalog_sha256']==origins['217']['catalog_sha256']
        for key in ['lng','lat','historical_view','navigation','collision_geometry','replacement_geometry','source_feature_ids']:
            assert marker[key]==contract[key]
        for key,digest in proof['runtime_signature'].items():assert seen[key]['sha256']==digest
        page=get(marker['individual_page']).decode()
        assert '2014年重刊、拍摄年代待考的黑白旧照' in page and '两层券廊各设八跨' in page
        manifest=json.loads(get(marker['candidate_manifest']))
        for key,digest in original['files'].items():assert sha(get(key))==digest
        for role,entry in manifest['assets'].items():
            actual=get(str(Path(marker['candidate_manifest']).parent/entry['file']))
            assert sha(actual)==entry['sha256']==original['downloads'][role]['sha256']
        for view in original['views']:assert sha((AUDIT/view['filename']).read_bytes())==view['sha256']
    origins[str(n)]={'url':base,'count':num,'signed_files':len(snapshot['files']),'snapshot_sha256':signature,'catalog_sha256':seen[catalog]['sha256'],'files':seen,'all_http':{'sha256':sha((TOP/'scenes'/f'{n}-all-http.json').read_bytes()),'bytes':complete['total_bytes'],'count':complete['count'],'ranges':len(complete['ranges'])}}
save(HERE/'bound-inputs.json',canon({'origins':origins,'id':target,'previous':prior,'title':marker['name'],'archive_page':marker['individual_page'],'marker':[marker['lng'],marker['lat']],'archive':marker['historical_view'],'previous_candidate_rows_retained_in_order':len(rows[0]),'source_review_sha256':sha(SOURCE.read_bytes()),'old_viewer_sha256':sha((AUDIT/'viewer.json').read_bytes()),'old_viewer_screenshots':original['views']}))
print(num,origins['218']['signed_files'],len(rows[0]),marker['name'])
