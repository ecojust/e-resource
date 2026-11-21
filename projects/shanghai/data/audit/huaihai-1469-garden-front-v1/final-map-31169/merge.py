from pathlib import Path
from hashlib import sha256
import json,os
w=Path(__file__).parent
read=lambda f:json.loads(f.read_bytes())
h=lambda f:sha256(f.read_bytes()).hexdigest()
runs={key:read(w/('after-'+key)/'after.json') for key in ('desktop','mobile')}
out=w/'after';out.mkdir(exist_ok=True)
for key,r in runs.items():
    assert r['passed'] and r['browser_closed'] and len(r['captures'])==3 and r['states'][0]['device']==key
    assert (w/f'after-{key}.exit').read_text().strip()=='0'
    for im in r['captures']:
        f=w/('after-'+key)/im['file'];dest=out/f.name
        assert h(f)==im['sha256']
        if not dest.exists():os.link(f,dest)
        else:assert h(dest)==im['sha256']
q={**runs['desktop']}
for array in ('captures','states','page_errors','http_errors','request_failures','canceled_requests','unread_bodies'):
    if any(array in r for r in runs.values()):q[array]=sum((r.get(array,[])for r in runs.values()),[])
for key in ('catalog','count','base','id','script_sha256','signed_input_sha256'):
    assert runs['desktop'][key]==runs['mobile'][key]
q['signed_responses']={**runs['desktop']['signed_responses'],**runs['mobile']['signed_responses']}
q['closed_at']=runs['mobile']['closed_at']
q['device_reports']={key:{'sha256':h(w/('after-'+key)/'after.json'),'closed_at':r['closed_at'],'exit':0,'signed_responses':r['signed_responses']}for key,r in runs.items()}
(out/'after.json').write_text(json.dumps(q,indent=2)+'\n')
(w/'after.exit').write_text('0\n')
