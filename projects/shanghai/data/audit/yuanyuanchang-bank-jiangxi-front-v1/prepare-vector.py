from argparse import ArgumentParser
from urllib.request import urlopen
from pathlib import Path
import mapbox_vector_tile,shapely,json,numpy as np,hashlib
from shapely.geometry import shape,mapping
parser=ArgumentParser(description='Decode the seven source aggregates that intersect the bank and neighboring properties.')
parser.add_argument('--tile',type=Path,help='Local copy of the immutable tile')
parser.add_argument('--out',type=Path,required=True)
args=parser.parse_args()
url='https://tiles.openfreemap.org/planet/20261115_080022_pt/14/13720/6693.pbf'
data=args.tile.read_bytes() if args.tile else urlopen(url,timeout=45).read()
m=hashlib.sha256(data).hexdigest()
assert m=='e6a2578dd38fdc6ef28737b68ea1e59181efe7d2fbde1d812f76f0a555833495'
audit=Path(__file__).resolve().parent

x,y,z=13720,6693,14
q=mapbox_vector_tile.decode(data,default_options={'y_coord_down':True})['building']
def wgs(p):return np.column_stack(((p[:,0]/q['extent']+x)/2**z*360-180,np.degrees(np.arctan(np.sinh(np.pi*(1-2*(p[:,1]/q['extent']+y)/2**z))))))
src=json.loads((audit.parents[2]/'source/precise/huangpu-yuanyuanchang-bank-jiangxi-front/footprint-review.json').read_bytes())
regions=[shape(n['geometry_wgs84']) for n in src['owners']]
r=[]
for f in q['features']:
 g=shapely.transform(shape(f['geometry']),wgs)
 if any(g.intersection(region).area>1e-13 for region in regions):
  r.append(dict(f,geometry=mapping(g)))
assert sorted(f['id'] for f in r)==sorted([23711710,4147331500,116293700,116367960,116367860,116367720,2935044980])
args.out.write_text(json.dumps(dict(url=url,bytes=len(data),sha256=m,type='FeatureCollection',features=r))+'\n')
