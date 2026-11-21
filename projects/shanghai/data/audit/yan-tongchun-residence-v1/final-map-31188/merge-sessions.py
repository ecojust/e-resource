"""Combine four real process receipts for one immutable after-state."""
from pathlib import Path
from hashlib import sha256
import json,os

w=Path(__file__).parent
def read(f):
    return json.loads(f.read_bytes())
def digest(f):
    return sha256(f.read_bytes()).hexdigest()
def put(source,target):
    if target.exists():
        assert digest(target)==digest(source)
    else:
        os.link(source,target)

out=w/'after'
out.mkdir(exist_ok=True)
phases=('desktop','phone','architecture','distant')
expected_views={'desktop':['map-desktop'],'phone':['map-mobile'],'architecture':['map-front','map-carved-door-and-transom'],'distant':['map-distant']}
before=read(w/'before/before.json')
assert before['completed'] and before['browserClosed'] and (w/'before.exit').read_text().strip()=='0'
rows={}
for phase in phases:
    src=w/phase/'after.json'
    row=read(src)
    assert row['completed'] and row['browserClosed'] and row['mode']=='after' and row['segment']==phase
    assert row['beforeReceipt']['sha256']==digest(w/'before/before.json') and not row['pageErrors'] and not row['httpErrors']
    assert row['scriptSha256']==digest(w/('check-distant-and-downloads.cjs' if phase=='distant' else 'check-independent-city.cjs'))
    assert before['scriptSha256']==digest(w/'check-independent-city.cjs')
    assert row['caseSha256']==before['caseSha256'] and row['contractSha256']==before['contractSha256']
    assert (w/f'{phase}.exit').read_text().strip()=='0'
    for key in ('catalog','snapshotSha256','nativeInputs','modelInputs','site','id','beforeReceipt','groundSha256','files'):
        if rows:assert row[key]==rows['desktop'][key],key
    assert [Path(v['file']).stem for v in row['views']]==expected_views[phase]
    for view in row['views']:
        image=w/phase/view['file']
        assert not view['lost'] and view['glError']==0 and digest(image)==view['sha256']
        put(image,out/image.name)
    assert (len(row['actions'])==1)==(phase in ('phone','desktop'))
    assert (len(row['ground'])==12)==(phase=='architecture')
    assert bool(row['sources'])==(phase=='architecture')
    assert (len(row.get('downloads',[]))==4)==(phase=='distant')
    rows[phase]=row
result=rows['desktop'].copy()
for key in ('actions','views','ground','sources','pageErrors','failedRequests','httpErrors','downloads'):
    result[key]=[entry for row in rows.values() for entry in row.get(key,[])]
result['pageResponses']={}
for row in rows.values():
    for name,entry in row['pageResponses'].items():
        previous=result['pageResponses'].get(name)
        if previous:assert previous['sha256']==entry['sha256'] and previous['bytes']==entry['bytes'],name
        result['pageResponses'][name]=entry
assert len(result['actions'])==2 and {v['input'] for v in result['actions']}=={'mouse','touch'}
assert result['views'][0]['viewport']==[790,510] and result['views'][1]['viewport']==[390,844]
assert all(r['actual']==r['expected'] for r in result['ground'])
assert {r['role'] for r in result['downloads']}=={'raw','full','lod','native'}
result['segment']='four-closed-sessions'
result['finished']=rows['distant']['finished']
result['sessions']={phase:{'file':phase+'-browser.json','sha256':digest(w/phase/'after.json'),'started':row['started'],'finished':row['finished'],'browserClosed':row['browserClosed'],'exit':0} for phase,row in rows.items()}
(out/'after.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
(w/'after.exit').write_text('0\n')
