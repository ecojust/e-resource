"""Re-request actual map resources, independently binding each to the release or immutable Git baseline."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from hashlib import sha1,sha256
from http.client import HTTPConnection
from pathlib import Path
from urllib.parse import quote,urlsplit
import argparse,json,subprocess

ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--browser',type=Path,required=True);ap.add_argument('--project',type=Path,required=True)
ap.add_argument('--release',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
args=ap.parse_args()
read=lambda p:json.loads(p.read_bytes())
browser=read(args.browser);release=read(args.release)
assert browser['completed'] and browser['browser_closed'] and browser['city_count']==release['resulting_count']==166
url=urlsplit(browser['server']);assert url.hostname=='127.0.0.1'
baseline=release['asset_revision']; root=args.project.resolve()
declarations={v['file']:v['sha256'] for v in browser['http_assets']+browser['map_files_seen']}
requests=set(browser['http_response_paths'])|set(declarations)
assert requests and all(k and not k.startswith('/') and '..' not in k.split('/') for k in requests)
def verify(rel):
    c=HTTPConnection(url.hostname,url.port,timeout=90)
    try:
        c.request('GET','/'+quote(rel,safe='/'))
        response=c.getresponse();assert response.status==200,(rel,response.status)
        length=int(response.getheader('Content-Length'));z=sha256();blob=sha1(f'blob {length}\x00'.encode());lengthread=0
        while data:=response.read(131072):
            z.update(data);blob.update(data);lengthread+=len(data)
        assert lengthread==length
        h=z.hexdigest();git=blob.hexdigest();header=response.getheader('X-Audit-SHA256')
        if header is not None:assert h==header,rel
        if rel in release['files']:
            assert h==release['files'][rel],rel;witness='signed release'
        elif rel.startswith('assets/city-detail/macros/') or not (root/rel).is_file():
            cmd=['git','--no-lazy-fetch','ls-tree',baseline,'--','projects/shanghai/'+rel]
            row=subprocess.check_output(cmd,cwd='/workspace/e-resource',text=True).strip();assert row and row.split()[2]==git,(rel,row,git)
            witness='immutable city Git blob'
        else:
            assert sha256((root/rel).read_bytes()).hexdigest()==h,rel;witness='materialized release input'
        if rel in declarations:assert declarations[rel]==h,rel
        if rel in browser['bindings']:assert browser['bindings'][rel]==h,rel
        return rel,dict(bytes=length,sha256=h,git_blob=git,source=witness)
    finally:c.close()
with ThreadPoolExecutor(2) as pool:rows=dict(pool.map(verify,sorted(requests)))
extra={row:{'sha256':h,'bytes':(root/row).stat().st_size} for row,h in browser['bindings'].items() if row not in rows}
assert all(sha256((root/row).read_bytes()).hexdigest()==v['sha256'] for row,v in extra.items())
out=dict(utc=datetime.now(timezone.utc).isoformat(),model_id=browser['model_id'],count=browser['city_count'],base=browser['server'],baseline=baseline,
    release_sha256=sha256(args.release.read_bytes()).hexdigest(),browser_sha256=sha256(args.browser.read_bytes()).hexdigest(),
    method='All local HTTP paths recorded during the scene and the four model downloads were fetched again and compared to signed release bytes, the materialized input tree or the immutable city Git blob. The local generation inputs below were verified separately.',
    files=rows,extra_generation_inputs=extra,observed_resources=len(rows),observed_total_bytes=sum(v['bytes'] for v in rows.values()))
args.out.write_text(json.dumps(out,indent=2)+'\n')
print(out['observed_resources'],out['observed_total_bytes'],len(extra))
