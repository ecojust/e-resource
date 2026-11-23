"""Verify the reviewed 283 camera changes, the intervening Wukang revision and the current 3304 registration."""
from pathlib import Path
import base64,gzip,hashlib,json
def verify(get,folder,expected,canonical):
    folder=folder.rstrip('/')+'/'
    root=str(Path(folder).parent)+'/'
    x=root+'xiangyang-ordinary-revision/'
    sha=lambda data: hashlib.sha256(data).hexdigest()
    proof=json.loads(get(x+'signed-route-replay.json'))
    assert proof['revision']=='ef259b7af5f3990ba7fa0ae34dc88883fc825c3e'
    assert proof['corrected_counts']=='842fa2327b90e2a303a44a0d1ea51aa02050b417'
    assert (proof['ordinary_models'],proof['candidate_models'],proof['resulting_navigation_entries'])==(41,278,319)
    before=gzip.decompress(get(x+'previous-production-snapshot.json.gz'))
    assert sha(before)==proof['prior_snapshot']=='ebc0520a14135818722b9fe43300062a74c43d40268fe853c67d46b9f5b639a8'
    older=base64.b64decode
    original_files=json.loads(gzip.decompress(get(x+'previous-replayed-files.json.gz')))
    def read_old(key):
        if key==root+'production-snapshot.json':return before
        return older(original_files[key]) if key in original_files else get(key)
    code=get(x+'prior-verifier.py')
    assert sha(code)=='9befba788c1f203c78d883499aa20c3a9bac4b8ee46bc507956b41e718cbcb64'
    namespace={}
    exec(compile(code,'prior-verifier.py','exec'),namespace)
    approved=namespace['verify'](read_old,folder,expected,canonical)
    snapshot=json.loads(before)
    highest=get(x+'31-measured-production.json'); assert sha(highest)==proof['highest_sha256']
    measured=json.loads(highest)
    assert measured['resulting_count']==319
    for key,change in proof['published_routes'].items():
        assert change['previous']==snapshot['files'].get(key)
        actual=sha(get(key))
        assert change['current']==actual==measured['files'][key],key
        if key in approved:approved[key]=actual
        snapshot['files'][key]=actual
    snapshot['resulting_count']=319
    assert sha(canonical(snapshot))==proof['final_snapshot']==sha(get(root+'production-snapshot.json'))
    assert {key:snapshot['files'][key] for key in set(snapshot['files'])-set(measured['files'])}==proof['additional_publication_test']
    assert {key:dict(gis=digest,publication=snapshot['files'].get(key)) for key,digest in measured['files'].items() if snapshot['files'].get(key)!=digest}==proof['underlying_differences']
    static=json.loads(get('data/landmarks.json'));town=json.loads(get('data/candidate-city-integrations.json'))
    assert len(static)==town['existing_city_count']==41 and len(town['models'])==278
    assert len({r['id'] for r in static+town['models']})==town['resulting_city_count']==319
    assert sum(bool(r.get('walkStart')) for r in static)==40
    current,=[r for r in static if r['id']=='xuhui-xiangyang-313-restored-courtyard-fronts']
    assert current.get('accepted') and current['owner']['feature_local_id']==3304 and current['navigation']['mode']=='overview'
    assert len(json.loads(get('data/model-todo/standalone-heritage-models.json'))['records'])==31
    return approved
