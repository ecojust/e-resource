#!/usr/bin/env python3
"""Reconstruct complete source lake outer/inner rings; no model/navigation verdict."""
import hashlib,json,math
from pathlib import Path
from shapely.geometry import Polygon,Point,shape,mapping
from shapely.ops import transform
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
source_path=HERE/'osm-jinhai-lake-full.json';source=json.loads(source_path.read_bytes());elements={(x['type'],x['id']):x for x in source['elements']};relation=elements[('relation',7617592)];assert relation['tags']['natural']=='water' and relation['tags']['type']=='multipolygon'
gp=ROOT/'freeze-v1/fengxian-museum/geometry-input.json';g=json.loads(gp.read_bytes());lon0,lat0=g['anchor'];cos0=math.cos(math.radians(lat0));my0=math.asinh(math.tan(math.radians(lat0)))
def local(lon,lat,z=None):return [6378137*math.radians(lon-lon0)*cos0,6378137*(math.asinh(math.tan(math.radians(lat)))-my0)*cos0]
parts={};members=[]
for member in relation['members']:
 assert member['type']=='way' and member['role'] in ('outer','inner');way=elements[('way',member['ref'])];ids=way['nodes'];assert all(('node',i) in elements for i in ids)
 parts.setdefault(member['role'],[]).append((member['ref'],ids));members.append({'way_id':member['ref'],'role':member['role'],'node_count':len(ids),'closed_in_source':ids[0]==ids[-1]})
outer_ids=list(parts['outer'][0][1]);outer_members=[parts['outer'][0][0]];remaining=parts['outer'][1:]
while remaining:
 choices=[(i,ids if ids[0]==outer_ids[-1] else list(reversed(ids))) for i,(_,ids) in enumerate(remaining) if outer_ids[-1] in (ids[0],ids[-1])];assert len(choices)==1
 index,ids=choices[0];outer_ids.extend(ids[1:]);outer_members.append(remaining[index][0]);remaining.pop(index)
assert outer_ids[0]==outer_ids[-1]
def coords(ids):return [[elements[('node',i)]['lon'],elements[('node',i)]['lat']] for i in ids]
outer=coords(outer_ids);inner=[]
for way,ids in parts['inner']:assert ids[0]==ids[-1];inner.append(coords(ids))
water=Polygon(outer,inner);assert water.is_valid and len(water.interiors)==5
local_water=transform(local,water);owner=shape(g['model_geometry_local_east_north_m']);islands=[transform(local,Polygon(ring)) for ring in inner];covering=[i for i,poly in enumerate(islands) if poly.covers(owner)];assert len(covering)==1
closest=local_water.distance(owner);assert closest>0 and not local_water.intersects(owner)
def desc(p):b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
context={'type':'FeatureCollection','features':[{'type':'Feature','id':'osm-relation-7617592','properties':{'name':'Jinhai Lake','source':'OpenStreetMap relation7617592','source_license':'ODbL-1.0','coordinates':'Frozen-owner local east/north metres'},'geometry':mapping(local_water)}]}
with (HERE/'water-local-enu.geojson').open('x') as f:json.dump(context,f,ensure_ascii=False,indent=2);f.write('\n')
report={'schema':'fengxian-v17-complete-source-lake-context','source_extraction_passed':True,'model_geometry_evaluated':False,'model_accepted':False,'navigation_accepted':False,'source':desc(source_path),'source_contract':desc(gp),'relation':{k:relation[k] for k in ('id','version','timestamp','tags')},'members':members,'stitched_outer_way_order':outer_members,'outer_ring_node_count':len(outer_ids),'inner_island_count':len(inner),'all_relation_way_nodes_present':True,'water_geometry_valid':True,'coordinate_contract':g['coordinate_contract'],'museum_island_inner_way_id':parts['inner'][covering[0]][0],'source_owner_water_intersection_area_m2':local_water.intersection(owner).area,'source_owner_minimum_water_distance_m':closest,'water_geometry':desc(HERE/'water-local-enu.geojson'),'limits':['Mapped lake geometry, including museum island, is reconstructed from the complete actual relation response; this is not a survey of current shore or all small pools.','Distance applies only to the original source owner polygon, not to corrected architectural geometry, stairs, roof openings, a walking spawn or any camera.','The rejected spatial-v2 roof/courtyard topology was not used or accepted by this source report.','Final external walkStart, finite keyboard sweep and default14m camera arm require the corrected final mesh plus actual source buildings/water/roads and browser verification.','No roof-route, stair climbing or interior collision/support guarantee; unchanged runtime uses mapped building polygons and explicit existing support proxies.'],'script':desc(Path(__file__))}
with (HERE/'water-source-review.json').open('x') as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'report':desc(HERE/'water-source-review.json'),'island_way':report['museum_island_inner_way_id'],'source_owner_water_distance_m':closest,'source_geometry_only':True},indent=2))
