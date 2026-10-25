"""Create a small deterministic, static traffic illustration on verified Bund roads.
Source paths/lane counts are OSM; vehicle presence, colors and shapes are fictional.
"""
from pathlib import Path
import sys,json,math,hashlib
import numpy as np
from shapely.geometry import shape,Point,LineString,Polygon,MultiLineString
from shapely.ops import transform,unary_union,linemerge
ROOT=Path(__file__).resolve().parent
PROJECT=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT.parents[2]
ORIGIN=(121.4862,31.2385);R=6378137.;SCALE=math.cos(math.radians(ORIGIN[1]));Y0=math.asinh(math.tan(math.radians(ORIGIN[1])))
def to_local(x,y,z=None):return R*math.radians(x-ORIGIN[0])*SCALE,-R*(math.asinh(math.tan(math.radians(y)))-Y0)*SCALE
def geographic(x,z):return ORIGIN[0]+math.degrees(x/(R*SCALE)),math.degrees(math.atan(math.sinh(Y0-z/(R*SCALE))))
def metric(g):return transform(to_local,g)
features=json.loads((ROOT/'bund-streets-road-check.geojson').read_text())['features']
road=metric(shape(next(f['geometry'] for f in features if f['properties']['role']=='asphalt_surface')))
crossings=metric(shape(next(f['geometry'] for f in features if f['properties']['role']=='mapped_crossings')))
main=[f for f in features if f['properties'].get('role')=='OSM_centerline' and f['properties'].get('tags',{}).get('name')=='中山东一路']
by_id={f['properties']['osm_way']:f for f in main}
east_ids=[40301368,1298040465]
west_ids=[1298040482,1068447135,448931481,1298040469,448931482,1201643770]
assert all(f['properties']['tags'].get('oneway')=='yes' and f['properties']['tags'].get('lanes')=='3' for f in main)
# Guard all actual street-crossing axes, including the pavement on either side.
osm=json.loads((ROOT/'osm-street.json').read_text())['elements'];cross_axes=[]
for e in osm:
 if e.get('tags',{}).get('footway')=='crossing' and 'geometry' in e:cross_axes.append(metric(LineString([(p['lon'],p['lat']) for p in e['geometry']])))
no_stop=crossings.buffer(10).union(unary_union(cross_axes).buffer(9))
for f in features:
 if f['properties'].get('role')=='OSM_centerline' and f['properties'].get('tags',{}).get('name')!='中山东一路':
  line=metric(shape(f['geometry']))
  no_stop=no_stop.union(line.buffer(9))
water=metric(shape(next(f['geometry'] for f in json.loads((ROOT/'bund-streets-shoreline-check.geojson').read_text())['features'] if f['properties']['role']=='merged_water')))
cs=json.loads((ROOT.parent/'bund-candidates.json').read_text())['candidates'];buildings=unary_union([metric(shape(c['geometry'])) for c in cs])
vehicles=[];envelopes=[];routes=[]
templates=[('sedan','#aeb9bf',4.62,1.82,1.52),('taxi','#53b5af',4.65,1.84,1.70),('sedan','#233746',4.70,1.86,1.54),('bus','#d2d2b8',10.5,2.45,3.35),('sedan','#7f3e37',4.56,1.81,1.52),('sedan','#d5d2c9',4.66,1.84,1.52),('taxi','#6cbbb2',4.65,1.84,1.70),('sedan','#51656b',4.55,1.82,1.52),('sedan','#c2c7cb',4.70,1.86,1.54),('sedan','#424955',4.62,1.82,1.52)]
for direction,ids in [('northbound',east_ids),('southbound',west_ids)]:
 route=linemerge(MultiLineString([metric(shape(by_id[i]['geometry'])) for i in ids]));assert route.geom_type=='LineString'
 coords=list(route.coords)
 if (direction=='northbound' and coords[0][1]<coords[-1][1]) or (direction=='southbound' and coords[0][1]>coords[-1][1]):coords.reverse()
 route=LineString(coords);routes.append({'id':direction,'osm_way_ids':ids,'lanes':3,'oneway':True,'line':{'type':'LineString','coordinates':[list(geographic(x,z)) for x,z in coords]},'estimated_carriageway_width_m':9.0,'inferred_lane_width_m':3.0})
 for ordinal,fraction in enumerate([.13,.31,.49,.68,.87]):
  idx=len(vehicles);kind,color,length,width,height=templates[idx]
  preferred_lane=1 if ordinal in (1,3) else 2
  found=None
  for lane in [preferred_lane,2,1]:
   offset=(2-lane)*3.0
   for adjustment in [0]+[v for i in range(1,16) for v in (i*3.,-i*3.)]:
    d=route.length*fraction+adjustment
    if not 14<d<route.length-14:continue
    p=np.array(route.interpolate(d).coords[0]);a=np.array(route.interpolate(d-.3).coords[0]);b=np.array(route.interpolate(d+.3).coords[0]);t=b-a;t/=np.linalg.norm(t);right=np.array([-t[1],t[0]]);p+=right*offset
    # Includes wheels, mirrors/handles/lights plus a 0.12m safety margin.
    envelope=Polygon([p+t*aa*(length/2+.12)+right*bb*(width/2+.12) for aa,bb in [(-1,-1),(1,-1),(1,1),(-1,1)]])
    if not road.contains(envelope) or envelope.intersects(no_stop) or any(envelope.distance(e)<22 for e in envelopes):continue
    if envelope.intersects(water) or envelope.intersects(buildings):continue
    heading=math.degrees(math.atan2(t[0],-t[1]))%360;lng,lat=geographic(*p)
    found={'id':'bund-traffic-'+str(idx+1).zfill(2),'kind':kind,'color':color,'lng':lng,'lat':lat,'heading_degrees':heading,'length_m':length,'width_m':width,'height_m':height,'ground_altitude_m':.020,'route':direction,'lane_from_right':lane,'lane_offset_right_m':offset,'distance_along_route_m':round(d,3),'source_osm_way':min(ids,key=lambda i:metric(shape(by_id[i]['geometry'])).distance(Point(p))),'footprint_clearance_to_road_edge_m':round(envelope.distance(road.boundary),4)}
    break
   if found:break
  if found:vehicles.append(found);envelopes.append(envelope)
assert 8<=len(vehicles)<=12,len(vehicles)
validation={'passed':True,'vehicle_count':len(vehicles),'all_vehicle_envelopes_within_generated_road':all(road.contains(e) for e in envelopes),'water_overlap_m2':sum(e.intersection(water).area for e in envelopes),'candidate_footprint_overlap_m2':sum(e.intersection(buildings).area for e in envelopes),'crossing_and_junction_overlap_m2':sum(e.intersection(no_stop).area for e in envelopes),'minimum_envelope_gap_m':round(min(a.distance(b) for i,a in enumerate(envelopes) for b in envelopes[i+1:]),3),'minimum_road_edge_clearance_m':round(min(e.distance(road.boundary) for e in envelopes),4),'envelope_extra_margin_m':.12,'building_check_scope':'Only the ten candidates[*].geometry footprints in source/bund/bund-candidates.json; not a citywide building check.','road_geometry_sha256':hashlib.sha256((ROOT/'bund-streets-road-check.geojson').read_bytes()).hexdigest()}
data={'version':4,'title':'外滩静态交通示意','mode':'static','is_live_traffic':False,'disclaimer_zh':'车辆为少量静态视觉示意，不代表实时交通、实际停放位置或公交线路。道路方向及车道数来自 OSM，车道宽度与车辆外观为建模推定。','coordinate_system':'WGS84 positions; vehicle dimensions in metres; heading clockwise from true north.','source':{'road_geometry':'source/bund/street/bund-streets-road-check.geojson','osm_roads':'source/bund/street/osm-roads.json','license':'OSM-derived positions ODbL-1.0; original procedural vehicle shapes MIT','attribution':'© OpenStreetMap contributors','road_surface_height_m':.020},'paths':routes,'vehicles':vehicles,'validation':validation}
output=PROJECT/'data/bund/traffic-v4.json';output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');print(json.dumps(validation))
