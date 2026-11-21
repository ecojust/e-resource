"""Verify unmodified city tiles intersecting a 160 m circle around the factory archive marker."""
from pathlib import Path
from urllib.request import urlopen
from urllib.error import HTTPError
from math import radians, cos, hypot
import json, hashlib, subprocess

work = Path(__file__).parent
repo = Path('/workspace/e-resource')
read = lambda p: json.loads(p.read_bytes())
key = 'projects/shanghai/'
old = read(work.parent/'frozen-park-owners.json')
site = read(work/'bound-inputs.json')
lon, lat = site['point']
signed = {row['macro']:row for row in old['source']}
requests = []
radius = 160

def object_id(path):
    return subprocess.check_output(['git','-C',repo,'rev-parse',old['revision']+':'+key+path],text=True).strip()

def get(port,path,source_sha=None):
    oid=object_id(path)
    url=f'http://127.0.0.1:{port}/'+path
    try:
        with urlopen(url,timeout=50) as response:
            assert response.status==200
            body=response.read()
    except HTTPError as error:
        requests.append(dict(path=path,port=port,url=url,status=error.code,git_blob=oid,expected_sha256=source_sha))
        return None
    sha=hashlib.sha256(body).hexdigest()
    assert hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()==oid
    assert source_sha is None or source_sha==sha
    requests.append(dict(path=path,port=port,url=url,status=200,git_blob=oid,sha256=sha,bytes=len(body)))
    return body

for port in (31219,31220):
    get(port,'data/districts-display.geojson')
    for macro,ref in signed.items():
        pref='assets/city-detail/macros/'+macro+'/'
        ready=get(port,pref+'READY.json')
        if ready is None:continue
        manifest=json.loads(ready)
        get(port,pref+'far.glb')
        get(port,pref+'feature-table.json.gz',ref['sha256'])
        for tile in manifest['tiles']:
            west,south,east,north=tile['geographic_bbox']
            dx=max(west-lon,0,lon-east)*111195*cos(radians(lat));dy=max(south-lat,0,lat-north)*111195
            if hypot(dx,dy)<=radius:get(port,pref+tile['file'],tile['sha256'])
out=work/'complex-source-http.json'
evidence=dict(passed=all(y['status']==200 for y in requests),complex_marker=[lon,lat],coarse_location=True,
              radius_m=radius,baseline=old['revision'],requests=requests)
temp=out.with_suffix('.part');temp.write_text(json.dumps(evidence,indent=2)+'\n');temp.replace(out)
print(len(requests),sum(r.get('bytes',0) for r in requests),[(r['port'],r['path']) for r in requests if r['status']!=200]);assert evidence['passed']
