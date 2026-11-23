"""Check the earlier city snapshot, the subsequent Wukang revision and the staged or published result."""
from pathlib import Path
import json,hashlib,gzip,subprocess
def verify(get,folder,expected,canonical):
    read=lambda n:json.loads(get(n))
    sha=lambda b:hashlib.sha256(b).hexdigest()
    folder=folder.rstrip('/')+'/'
    note=read(folder+'public-snapshot-replay.json')
    assert note['order']==283
    parent='370d35bbe3c8368576c9e0f2b647b8da210947e7'
    revision='0a9fb9674235a0d8cd9efa63d3e9e1deb570a641'
    assert note['baseline']==parent and note['amendment']==revision
    hist=gzip.decompress(get(folder+'snapshot-before-ordinary-revision.json.gz'))
    assert sha(hist)==note['previous_snapshot_sha256']=='1829bf70abc1b2f5c661fb9d361246e72bb217052ca6d6bb2be07a43cef85397'
    snapshot=json.loads(hist);signed=read(folder+'projection.json')
    assert signed['latest_confirmed_parent']==parent and signed['amendment']==revision
    frame=read(folder+'31-283-production.json');assert sha(get(folder+'31-283-production.json'))==note['highest_replayed_sha256']
    checks=read(folder+'verified-http.json');assert all(checks[k]==308 for k in ('full_responses','head_responses','partial_responses'))
    assert len(signed['levels'])==14 and len(signed['levels']['31']['delta'])==22
    assert len(note['changed_paths'])==5 and len(note['additional_paths'])==17
    for key,row in signed['levels']['31']['delta'].items():
        new=row['updated_283'];assert sha(get(key))==new==frame['files'][key],key
        if key in note['changed_paths']:
            assert snapshot['files'][key]==row['original_283']==note['changed_paths'][key]['before']
            assert new==note['changed_paths'][key]['after']
        else:assert key not in snapshot['files'] and row['original_283'] is None and new==note['additional_paths'][key]
        snapshot['files'][key]=new
    final_path=str(Path(folder).parent/'production-snapshot.json')
    compact=read(folder+'generator-padding-replay.json')
    assert compact['revision']=='68af4bd2df0190868f272cb0ee9b1fa63aebee2e' and compact['parent']=='94ff2e03ef31ada47101de8739a9030c23e97c43'
    key=compact['key'];assert key=='tools/build_model_todo.py'
    assert sha(canonical(snapshot))==note['merged_snapshot_sha256']==compact['snapshot_before']
    assert snapshot['files'][key]==compact['before']=='1a1d4bff8d8e8244f9e7631b446d5fbf605f9b27476941ec3977235e122a782a'
    snapshot['files'][key]=sha(get(key))
    assert snapshot['files'][key]==compact['after']=='4e32c7ff5a8c569bd8c38ad43ad6c20a17057559dd8250d6ab02fbcc5f071840'
    assert sha(canonical(snapshot))==compact['snapshot_after']==sha(get(final_path))
    assert expected['index.html']==note['changed_paths']['index.html']['before']
    reviewed=dict(expected);reviewed['index.html']=note['changed_paths']['index.html']['after']
    return reviewed
