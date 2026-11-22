from pathlib import Path as P
import hashlib,json,time
w=P(__file__).parent
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
c=w/'final-map-31234/mouse/process.json'
r=json.loads(c.read_bytes());assert r['node_closed'] and r['exit_code']==0 and r['remaining_chromium']==r['remaining_children']==[] and r['report_sha256']==h(c.with_name('main-browser.json'))
ticket=w/'mouse-closing-returned.json'
if not ticket.exists():
    sources=list(map(P,('/tmp/jixian299/234-mouse-layer21-returned.json','/dev/shm/root-tram520/work/234-confirmed-surface-returned.json','/tmp/julu314-553/234-mouse-revised-returned.json','/tmp/ruijin129-557/234-mouse-revised-returned.json','/tmp/jiangsu796-449/second-234-development/234-development-returned.json')))
    for source in sources:
        note=json.loads(source.read_bytes())
        assert note['exit_code']==0 and not note.get('remaining_children') and not note.get('remaining')
    tmp=ticket.with_suffix('.pending')
    tmp.write_text(json.dumps(dict(host_sha256=h(c),host_report_sha256=r['report_sha256'],returned={str(x):h(x)for x in sources}),indent=2)+'\n')
    tmp.replace(ticket)
s=json.loads(ticket.read_bytes());assert s['host_sha256']==h(c) and s['host_report_sha256']==r['report_sha256']
for k,v in s['returned'].items():assert h(P(k))==v
