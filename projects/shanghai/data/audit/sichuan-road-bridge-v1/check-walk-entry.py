"""Check the south approach point against map features and all delivered meshes."""
import argparse,hashlib,json,math,runpy
from pathlib import Path
from shapely.geometry import LineString,Point,Polygon
parser=argparse.ArgumentParser()
parser.add_argument('--decoded',required=True,type=Path,help='Directory containing the material-preserving full.glb and lod.glb decompressions')
args=parser.parse_args()
root=Path(__file__).resolve().parents[3]
audit=root/'data/audit/sichuan-road-bridge-v1'
refs=root/'source/precise/huangpu-sichuan-road-bridge/map-evidence.json'
contract=audit/'final-placement-contract.json'
c=json.loads(contract.read_bytes());refs=json.loads(refs.read_bytes());m=root/'assets/models/candidates'/c['id']/'manifest.json';manifest=json.loads(m.read_bytes())
entry=c['navigation']['walkStart'];heading=math.radians(c['heading']);north=6371008.8*math.pi/180;east=north*math.cos(math.radians(c['lat']))
xy=lambda pt:((pt[0]-c['lng'])*east,(pt[1]-c['lat'])*north)
e,n=xy(entry);x=e*math.cos(heading)-n*math.sin(heading);y=e*math.sin(heading)+n*math.cos(heading);walk=c['bridge_walk'];station=x-walk['shear']*y;end=walk['stations_m'][0][0]
point=Point(e,n)
def local_ring(coords):return [xy(v)for v in coords]
current=Polygon(local_ring(refs['source_ways']['815631994']['coordinates']))
frozen=Polygon(local_ring(next(f for f in refs['signed_transportation']if f['id']==8156319942)['coordinates'][0]))
paths={k:point.distance(LineString(local_ring(refs['source_ways'][k]['coordinates'])))for k in ['1467932127','1467932132']}
def physical(st,off):return (st+walk['shear']*off,off)
lamp_dist=min(Point(x,y).distance(Polygon([physical(p['station_m']+a*p['half_length_m'],p['offset_m']+b*p['half_width_m'])for a,b in [(-1,-1),(1,-1),(1,1),(-1,1)]]))for p in walk['posts'])
rail=min(abs(y-p['offset_m'])-p['radius_m']for p in walk['rails'])
assert 1.5<station-end<1.8 and walk['half_road_m']<y<walk['half_deck_m'] and rail>.7 and lamp_dist>12
assert current.contains(point)and frozen.contains(point) and min(paths.values())<2.2
Scene=runpy.run_path(str(root/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
hits={}
for variant in ['raw','full','lod']:
 asset=manifest['assets'][variant];file=m.parent/asset['file'] if variant=='raw' else args.decoded/(variant+'.glb')
 hit=Scene(file).ray([x,y,12],[0,0,-1],16);assert hit['material']=='pavement',hit
 hits[variant]=dict(source_sha256=asset['sha256'],mesh_sha256=hashlib.sha256(file.read_bytes()).hexdigest(),material=hit['material'],surface_altitude_m=12-hit['distance_m']+c['altitude'])
report={'contract_sha256':hashlib.sha256(contract.read_bytes()).hexdigest(),'navigation':c['navigation'],'station_m':station,'from_south_end_m':station-end,'toward_west_m':y,'clearance_to_rail_outer_face_m':rail,'clearance_to_nearest_pedestal_m':lamp_dist,'inside_frozen_deck_mvt_8156319942':True,'inside_osm_deck_815631994':True,'distance_to_osm_footway_lines_m':paths,'three_actual_surface_hits':hits}
(audit/'walk-entry.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False)[:1100])
