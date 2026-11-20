from argparse import ArgumentParser
from urllib.request import urlopen
from pathlib import Path
import mapbox_vector_tile,shapely,json,numpy as np,hashlib
from shapely.geometry import shape,mapping
parser=ArgumentParser(description='Read the real OpenMapTiles building which aggregates the Union Building and two separate neighboring banks at Sichuan Middle Road.')
parser.add_argument('--tile',type=Path,help='Local copy of the immutable tile')
parser.add_argument('--out',type=Path,required=True)
args=parser.parse_args()
url='https://tiles.openfreemap.org/planet/20261115_080022_pt/14/13720/6694.pbf'
data=args.tile.read_bytes() if args.tile else urlopen(url,timeout=45).read()
m=hashlib.sha256(data).hexdigest()
assert m=='2cc557168a2d1e041735028eab34d233a0ed2c3bf04497e91cfa92dbf27cb48c'
audit=Path(__file__).resolve().parent

x,y,z=13720,6694,14
q=mapbox_vector_tile.decode(data,default_options={'y_coord_down':True})['building']
def wgs(p):return np.column_stack(((p[:,0]/q['extent']+x)/2**z*360-180,np.degrees(np.arctan(np.sinh(np.pi*(1-2*(p[:,1]/q['extent']+y)/2**z))))))
src=json.loads((audit.parents[2]/'source/precise/huangpu-four-banks-savings-building/footprint-review.json').read_bytes())
regions=[shape(src['source_outline'])]+[shape(n['geometry']) for n in src['retained_neighbors']]
r=[]
for f in q['features']:
 g=shapely.transform(shape(f['geometry']),wgs)
 if any(g.intersection(region).area>1e-13 for region in regions):
  r.append(dict(f,geometry=mapping(g)))
assert sorted(f['id'] for f in r)==[23809960,194200050,513173390]
args.out.write_text(json.dumps(dict(url=url,bytes=len(data),tile_sha256=m,type='FeatureCollection',features=r))+'\n')
