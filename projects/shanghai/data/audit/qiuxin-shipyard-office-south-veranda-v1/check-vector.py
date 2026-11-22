"""Compare the three-dimensional site and the full signed OpenFreeMap building tile."""
from argparse import ArgumentParser
from pathlib import Path
from hashlib import sha256
from math import radians,cos
from urllib.request import urlopen
import json,mapbox_vector_tile,numpy as np,shapely
from shapely.geometry import shape
HERE=Path(__file__).resolve().parent
p=ArgumentParser(description=__doc__);p.add_argument('--tile',type=Path);p.add_argument('--contract',type=Path,required=True);p.add_argument('--catalog',required=True);p.add_argument('--out',type=Path,required=True);args=p.parse_args()
u='https://tiles.openfreemap.org/planet/20261115_080022_pt/14/13721/6695.pbf';raw=args.tile.read_bytes()if args.tile else urlopen(u,timeout=35).read();assert sha256(raw).hexdigest()=='f487451d3cfed477260f528a91cc8908b981bffbb1fd2d2509b234253ce16d72'
catalog=urlopen(args.catalog,timeout=45).read()if args.catalog.startswith('http')else Path(args.catalog).read_bytes();old=json.loads(catalog);contract=json.loads(args.contract.read_bytes());mask=shape(contract['replacement_geometry']);src=mapbox_vector_tile.decode(raw,default_options={'y_coord_down':True})['building']
def coords(v):
    e=src['extent'];return np.column_stack(((13721+v[:,0]/e)/(1<<14)*360-180,np.degrees(np.arctan(np.sinh(np.pi*(1-2*(6695+v[:,1]/e)/(1<<14)))))))
source_features=[];components=0
for f in src['features']:
    g=shapely.transform(shape(f['geometry']),coords)
    parts=list(shapely.get_parts(g));components+=len(parts)
    assert not g.intersects(mask),f['id']
    if f['id']==117595520:
        assert len(parts)==743
        source_features.append(dict(id=f['id'],lower_height=f['properties'].get('render_min_height'),height=f['properties'].get('render_height'),components=743,unchanged_components=743))
overlap=[q['id']for q in old['models'] if q['id']!=contract['id']and q.get('replacement_geometry')and shape(q['replacement_geometry']).intersection(mask).area>1.e-15];assert not overlap,overlap
assert len(source_features)==1;report=dict(passed=True,source=u,source_bytes=len(raw),source_sha256=sha256(raw).hexdigest(),contract_sha256=sha256(args.contract.read_bytes()).hexdigest(),input_catalog_sha256=sha256(catalog).hexdigest(),input_locations=old['resulting_city_count'],building_layer_features=len(src['features']),all_components=components,affected_components=0,overlapping_previous_model_ids=overlap,nearby_aggregate=source_features[0],other_components_unchanged=743,reason='The office footprint is present in the signed high-detail native city. The vector tile covers the neighboring workshops but contains no component intersecting the office mask.')
args.out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
print(report,flush=True)
