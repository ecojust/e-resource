"""Fetch sixteen 1 km Shanghai building samples from official Overture PMTiles.
Requires: pip install pmtiles mapbox-vector-tile shapely
Real footprints are preserved; this file does not invent heights or geometry.
"""
from urllib.request import Request, urlopen
from pathlib import Path
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, as_completed
import gzip, json, math, time, argparse
from pmtiles.reader import Reader
import mapbox_vector_tile
from shapely.geometry import shape, mapping, box
from shapely.ops import unary_union
from shapely import make_valid

HERE=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description=__doc__)
default_districts=next((p for p in [HERE.parents[1]/'data'/'districts.json',HERE/'districts.json'] if p.exists()), HERE/'districts.json')
parser.add_argument('--districts',type=Path,default=default_districts,help='Districts JSON with WGS84 walkStart points')
parser.add_argument('--output',type=Path,default=HERE.parents[1]/'data'/'neighborhoods',help='Output directory for GeoJSON extracts')
parser.add_argument('--release',default=None,help='Overture release; omitted means latest STAC release')
parser.add_argument('--radius',type=float,default=500,help='Half-width of each neighborhood in metres')
args=parser.parse_args()
if not 100 <= args.radius <= 2000:parser.error('--radius must be between 100 and 2000 metres')
DISTRICTS=json.loads(args.districts.read_text())['districts']
if args.release:
 RELEASE=args.release
else:
 catalog=json.load(urlopen(Request('https://stac.overturemaps.org/catalog.json',headers={'User-Agent':'Mozilla/5.0'}),timeout=30))
 RELEASE=catalog['latest']
URL=f'https://tiles.overturemaps.org/{RELEASE}/buildings.pmtiles'
OUT=args.output;OUT.mkdir(parents=True,exist_ok=True)
R=6378137
@lru_cache(maxsize=1024)
def get_bytes(offset,length):
 for attempt in range(4):
  try:
   req=Request(URL,headers={'User-Agent':'Mozilla/5.0','Range':f'bytes={offset}-{offset+length-1}'})
   with urlopen(req,timeout=30) as r:b=r.read()
   if len(b)!=length:raise ValueError(f'Range length mismatch {len(b)} != {length}')
   return b
  except Exception:
   if attempt==3:raise
   time.sleep(.5*(attempt+1))
READER=Reader(get_bytes)
@lru_cache(maxsize=128)
def tile(z,x,y):
 b=READER.get(z,x,y)
 if not b:return {}
 if b[:2]==b'\x1f\x8b':b=gzip.decompress(b)
 return mapbox_vector_tile.decode(b,default_options={'y_coord_down':True})
def tilexy(lon,lat,z=14):
 n=2**z
 return int((lon+180)/360*n),int((1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*n)
def to_wgs(coords,x,y,extent,z=14):
 if isinstance(coords[0],(int,float)):
  return [round((x+coords[0]/extent)/2**z*360-180,8),round(math.degrees(math.atan(math.sinh(math.pi*(1-2*(y+coords[1]/extent)/2**z)))),8)]
 return [to_wgs(c,x,y,extent,z) for c in coords]
def extract(d):
 lon,lat=d['walkStart'];dx=args.radius/(R*math.cos(math.radians(lat)))*180/math.pi;dy=args.radius/R*180/math.pi
 bbox=[lon-dx,lat-dy,lon+dx,lat+dy]
 # A 150 m apron avoids slicing a footprint at the requested 500 m sample edge.
 x0,y1=tilexy(lon-dx*1.3,lat-dy*1.3);x1,y0=tilexy(lon+dx*1.3,lat+dy*1.3)
 by_id={};tiles=[]
 for x in range(x0,x1+1):
  for y in range(y0,y1+1):
   tiles.append([14,x,y])
   for layer,data in tile(14,x,y).items():
    if layer not in ('building','building_part'):continue
    for f in data['features']:
     props=f.get('properties',{})
     if props.get('is_underground'):continue
     geom=f['geometry']
     if geom['type'] not in ('Polygon','MultiPolygon'):continue
     g={'type':geom['type'],'coordinates':to_wgs(geom['coordinates'],x,y,data['extent'])}
     poly=shape(g)
     if not poly.is_valid:poly=make_valid(poly)
     if poly.is_empty:continue
     identifier=str(props.get('id',f.get('id')))
     entry=by_id.setdefault((layer,identifier),{'props':props,'polygons':[]})
     entry['polygons'].append(poly)
 features=[];sources={};height_count=0;parts=0
 for (layer,identifier),entry in by_id.items():
  poly=unary_union(entry['polygons'])
  if poly.geom_type=='GeometryCollection':poly=unary_union([g for g in poly.geoms if g.geom_type in ('Polygon','MultiPolygon')])
  if poly.is_empty or poly.geom_type not in ('Polygon','MultiPolygon'):continue
  c=poly.centroid
  if not(bbox[0]<=c.x<=bbox[2] and bbox[1]<=c.y<=bbox[3]):continue
  props={k:v for k,v in entry['props'].items() if k in ['id','height','min_height','num_floors','min_floor','has_parts','building_id','class','subtype','names','@name','@geometry_source','@height_source','sources']}
  props['id']=identifier;props['source_layer']=layer
  if isinstance(props.get('sources'),str):
   try:props['sources']=json.loads(props['sources'])
   except ValueError:pass
  source=props.get('@geometry_source','unknown');sources[source]=sources.get(source,0)+1
  if props.get('height') is not None or props.get('num_floors') is not None:height_count+=1
  if layer=='building_part':parts+=1
  features.append({'type':'Feature','id':identifier,'properties':props,'geometry':mapping(poly)})
 collection={'type':'FeatureCollection','name':d['name']+f' · {args.radius*2:g} m building sample','bbox':bbox,
  'metadata':{'district_id':d['id'],'district_name':d['name'],'origin':d['walkStart'],'sample_width_m':args.radius*2,
   'selection':f'Footprint centroid inside ±{args.radius:g} m square; polygons are not clipped to square. Adjacent tile pieces merged by Overture ID.',
   'source':'Overture Maps Foundation','release':RELEASE,'pmtiles':URL,'tiles':tiles,'crs':'WGS84 / EPSG:4326',
   'license':'ODbL-1.0 (Overture buildings theme)','attribution':'© OpenStreetMap contributors; © Overture Maps Foundation; geometry sources retained per feature',
   'feature_count':len(features),'building_parts':parts,'features_with_height_or_floors':height_count,'geometry_sources':sources},'features':features}
 target=OUT/(d['id']+'.geojson');target.write_text(json.dumps(collection,ensure_ascii=False,separators=(',',':')))
 result={'district_id':d['id'],'district_name':d['name'],'origin':d['walkStart'],'bbox':bbox,'tiles':tiles,'features':len(features),'parts':parts,'with_height_or_floors':height_count,'geometry_sources':sources,'bytes':target.stat().st_size,'file':target.name}
 print(json.dumps(result,ensure_ascii=False),flush=True)
 return result
if __name__=='__main__':
 results=[]
 with ThreadPoolExecutor(max_workers=5) as ex:
  futures={ex.submit(extract,d):d for d in DISTRICTS}
  for f in as_completed(futures):
   try:results.append(f.result())
   except Exception as e:print('FAILED',futures[f]['name'],repr(e),flush=True);raise
 results.sort(key=lambda r:r['district_id'])
 manifest={'source':URL,'release':RELEASE,'license':'ODbL-1.0','attribution':'© OpenStreetMap contributors; © Overture Maps Foundation','samples':results,'total_features':sum(x['features'] for x in results)}
 (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
 print('COMPLETE',manifest['total_features'],'features',flush=True)
