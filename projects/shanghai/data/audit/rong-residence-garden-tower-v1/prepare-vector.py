from argparse import ArgumentParser
from urllib.request import urlopen,Request
from pathlib import Path
import mapbox_vector_tile,shapely,json,numpy as np,hashlib
from shapely.geometry import shape,mapping
parser=ArgumentParser(description='Decode the vector aggregates touching this parcel and its immediate neighbors.')
parser.add_argument('--tile',type=Path,help='Local copy of the immutable tile')
parser.add_argument('--out',type=Path,required=True)
args=parser.parse_args()
url='https://tiles.openfreemap.org/planet/20261115_080022_pt/14/13719/6694.pbf'
data=args.tile.read_bytes() if args.tile else urlopen(Request(url,headers={"User-Agent":"Mozilla/5.0","Referer":"https://openfreemap.org/"}),timeout=45).read()
m=hashlib.sha256(data).hexdigest()
assert m=='21ae0cc5b91bfb8c85d320d3d0295804e5af8d04fcca02fb316f3e5ef80449e2'
audit=Path(__file__).resolve().parent

x,y,z=13719,6694,14
q=mapbox_vector_tile.decode(data,default_options={'y_coord_down':True})['building']
def wgs(p):return np.column_stack(((p[:,0]/q['extent']+x)/2**z*360-180,np.degrees(np.arctan(np.sinh(np.pi*(1-2*(p[:,1]/q['extent']+y)/2**z))))))
src=json.loads((audit.parents[2]/'source/precise/jingan-rong-residence-garden-tower/footprint-review.json').read_bytes())
regions=[shape(n['geometry_wgs84']) for n in src['owners']]
r=[]
for f in q['features']:
 g=shapely.transform(shape(f['geometry']),wgs)
 if any(shapely.make_valid(part).intersection(region).area>1e-13 for part in shapely.get_parts(g) for region in regions if part.envelope.intersects(region.envelope)):
  r.append(dict(f,geometry=mapping(g)))
assert r and len(set(f['id'] for f in r))==len(r)
args.out.write_text(json.dumps(dict(url=url,bytes=len(data),sha256=m,type='FeatureCollection',features=r))+'\n')
