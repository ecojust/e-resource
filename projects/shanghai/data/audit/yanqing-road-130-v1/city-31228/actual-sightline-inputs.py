"""Bind the two historic front views to actual city triangles at both detail levels."""
import collections,gzip,hashlib,json,math,sys
from pathlib import Path
from urllib.request import urlopen
import numpy as np
import shapely
from shapely.geometry import shape, Point, LineString

root=Path(__file__).resolve().parent
ordinal=int(root.name[-3:])
auditname='yanqing-road-130-v1'
audit=Path('/workspace/e-resource/projects/shanghai/data/audit')/auditname
contract_path=audit/'final-placement-contract.json'
read=lambda f:json.loads(f.read_bytes())
digest=lambda b:hashlib.sha256(b).hexdigest()
contract=read(contract_path)
review=read(root/f'stage{ordinal}'/'source/precise'/contract['id']/'footprint-review.json')
cpu=read(root/'special-camera-sightlines.json')
macro=review['frozen_macro']
originals={v['repository_path'].split('/')[-1]:v for v in review['frozen_bindings']}
base=f'http://127.0.0.1:{31000+ordinal}/'
def fetch_checked(name):
    row=originals[name];route=row['repository_path'].removeprefix('projects/shanghai/')
    with urlopen(base+route,timeout=90) as response:
        assert response.status==200;body=response.read()
    assert len(body)==row['bytes'] and digest(body)==row['sha256']
    return body
ready=json.loads(fetch_checked('READY.json'))
features=json.loads(gzip.decompress(fetch_checked('feature-table.json.gz')))['features']
targets=collections.defaultdict(list)
for probe in read(audit/'surface-probes.json')['results']['raw']['probes']:
    if probe.get('first_hit'):targets[probe['label']].append(probe['first_hit']['point_enu_m'])
point=Point(contract['lng'],contract['lat'])
k=6371008.8*math.cos(math.radians(point.y));north=math.asinh(math.tan(math.radians(point.y)))
theta=math.radians(contract['heading']);c,s=math.cos(theta),math.sin(theta)
def local(x):
    east=np.radians(x[:,0]-point.x)*k;n=(np.arcsinh(np.tan(np.radians(x[:,1])))-north)*k
    return np.column_stack((east*c-n*s,east*s+n*c))
def save_geo(g):return shapely.to_geojson(g)
nearby={f['localId']:(f['geometry'],shapely.transform(shape(f['geometry']),local)) for f in features if shape(f['geometry']).distance(point)<.004}
views={};relevant=set()
for name,view in cpu.items():
    if not isinstance(view,dict) or 'witnesses' not in view:continue
    centre=view['center'];h=cpu['size'][1]
    distance=h/(2*math.tan(math.radians(36.87)/2))*2*math.pi*k/(512*2**view['zoom'])
    angle,pitch=map(math.radians,(view['bearing_offset'],view['pitch']))
    eye=[centre[0]-math.sin(angle)*distance*math.sin(pitch),centre[1]-math.cos(angle)*distance*math.sin(pitch),view['elevation']+distance*math.cos(pitch)]
    used=collections.Counter();lines=[]
    for probe in view['witnesses']:
        label=probe['feature'];i=used[label];used[label]+=1
        t=targets[label][i]
        lines.append({'feature':label+' #'+str(i+1),'target':t,'was_visible_in_signed_model':probe['clear']})
        line=LineString([eye[:2],t[:2]])
        relevant.update(n for n,(_,poly) in nearby.items() if line.distance(poly)<=1.2)
    views[name]={'eye':eye,'sightlines':lines}
groups=[dict(id=v['id'],file=v['file'],signed_sha256=v['sha256'],members=v['featureLocalIds']) for v in ready['tiles'] if relevant.intersection(v['featureLocalIds'])]
members=set().union(*(set(g['members']) for g in groups))
owners=[{'local_id':f['localId'],'geometry_wgs84':f['geometry']} for f in features if f['localId'] in members]
sources=dict(contract_sha256=digest(contract_path.read_bytes()),catalog_sha256=read(root/'signed-comparison.json')['stages'][1]['catalog_sha256'],contract=contract,ground_mask=json.loads(save_geo(shapely.transform(shape(contract['replacement_geometry']),local)))['coordinates'],groups=groups,all_ids=sorted(relevant),views=views,owners=owners,origin_longitude=ready['origin_longitude'],origin_latitude=ready['origin_latitude'],far_sha256=originals['far.glb']['sha256'],near_manifest_sha256=originals['READY.json']['sha256'],feature_table_sha256=originals['feature-table.json.gz']['sha256'],macro=macro)
(root/'actual-city-ray-inputs.json').write_text(json.dumps(sources,ensure_ascii=False,separators=(',',':'))+'\n')
print(ordinal,len(groups),len(relevant),sum(len(v['sightlines'])for v in views.values()))
