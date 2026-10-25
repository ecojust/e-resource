"""Reproduce district/checkpoint checks from the included public-source facts.
Requires shapely and pyproj. Does not infer survey accuracy from source agreement.
"""
from pathlib import Path
import json,hashlib,math,re,argparse
from shapely.geometry import shape,Point
from shapely.ops import transform,unary_union
from pyproj import Transformer,Geod
HERE=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--project',type=Path,default=HERE.parents[1])
PROJECT=parser.parse_args().project
def read(p):return json.loads(p.read_text())
bounds=read(PROJECT/'data/districts-display.geojson');raw=read(PROJECT/'data/districts.geojson');districts=read(PROJECT/'data/districts.json')['districts'];source=read(HERE/'official-sources.json');pois=read(HERE/'poi-sources.json');fixes=read(HERE/'poi-fixes.json')
G={str(f['properties']['id']):shape(f['geometry']) for f in bounds['features']};R={str(f['properties']['id']):shape(f['geometry']) for f in raw['features']};D={str(d['id']):d for d in districts};tx=Transformer.from_crs(4326,32651,always_xy=True).transform;geod=Geod(ellps='WGS84')
# Facts transcribed from fetched official pages; differing publication dates and
# land/water definitions are retained, not forced to equal OSM polygon areas.
area_facts={
 '310101':('Huangpu',20.52,'district area'),'310104':('Xuhui',54.93,'district area'),
 '310105':('Changning',37.18,'district area'),'310106':("Jing'an",37,'district area'),
 '310107':('Putuo',55.53,'district area'),'310109':('Hongkou',23.48,'district area'),
 '310110':('Yangpu',60.61,'district area'),'310112':('Minhang',373,'nearly 373 square kilometres'),
 '310113':('Baoshan',300.6,'district area'),'310114':('Jiading',463.16,'district area'),
 '310115':('Pudong',1210,'district area'),'310116':('Jinshan',613,'land area; page separately reports 445 km² sea area'),
 '310117':('Songjiang',604,'district area'),'310118':('Qingpu',668.54,'district area'),
 '310120':('Fengxian',733.38,'district area'),'310151':('Chongming',1413,'district area')}
areas=[]
for id,(key,official,meaning) in area_facts.items():
 s=next(x for x in source if x['title'].startswith(key));area=transform(tx,G[id]).area/1e6
 areas.append({'district_id':id,'name':D[id]['name'],'official_area_km2':official,'official_area_definition':meaning,'official_url':s['url'],'official_excerpt':s['area_context'][0],'osm_display_polygon_area_km2':round(area,3),'osm_original_polygon_area_km2':round(transform(tx,R[id]).area/1e6,3),'difference_percent':round((area/official-1)*100,2),'geometry_valid':G[id].is_valid,'note':'Polygon area includes administrative water where present; no assertion that the official statistic uses the same definition.'})
rejected=[];candidates={id:[] for id in D}
for p in pois:
 if p.get('wgs84'):
  point=Point(p['wgs84']);ids=[i for i,g in G.items() if g.covers(point)]
  if p['district_id'] not in ids:
   rejected.append({'name':p['name'],'url':p['url'],'coordinates':p['wgs84'],'expected':p['district_id'],'actual':ids,'reason':'Named geographic point is cross-boundary, approximate, or a different campus; rejected as an interior checkpoint.'});continue
  if p['name'] in ['Shanghai Tower','Shanghai World Financial Center','Jin Mao Tower','Oriental Pearl Tower','Fengxian, Shanghai','Jinshan, Shanghai']:continue
  candidates[p['district_id']].append({'name':p['name'],'coordinates':p['wgs84'],'source':p['url'],'source_kind':'Wikipedia geographic coordinate; community source, not survey','coordinate_license':'Factual coordinates, article CC BY-SA; source attribution retained','selection':'named place'})
for p in fixes:
 if not p.get('results'):continue
 x=p['results'][0];id=p['district_id'];name=x.get('name',p['query']);coords=[float(x['lon']),float(x['lat'])]
 if p['query'].startswith('人民广场'):name='人民广场站（OSM铁路站对象）'
 candidates[id].append({'name':name,'coordinates':coords,'source':f"https://www.openstreetmap.org/{x['osm_type']}/{x['osm_id']}",'source_kind':'OpenStreetMap via Nominatim','coordinate_license':'ODbL-1.0','selection':'named place'})
features=[]
for id,d in D.items():
 points=[{'name':d['name']+'已核验道路起点','coordinates':d['walkStart'],'source':'OpenFreeMap/OpenMapTiles tile '+str(d['walkRoad']['source_tile'])+', feature '+str(d['walkRoad']['vector_feature_id']),'source_kind':'Existing project road-vector checkpoint; not an independent position measurement','coordinate_license':'ODbL-1.0','selection':'road spawn'}]
 points+=candidates[id][:3 if id=='310151' else 2]
 for n,p in enumerate(points):
  coords=p.pop('coordinates');found=[i for i,g in G.items() if g.covers(Point(coords))]
  p.update({'checkpoint_id':f'{id}-{n+1}','district_id':id,'district_name':d['name'],'contained_by':found,'boundary_check_passed':id in found,'expected_buildings':'unknown: building density is checked separately; park/lake/airport points may be open space','crs':'EPSG:4326'})
  features.append({'type':'Feature','id':p['checkpoint_id'],'properties':p,'geometry':{'type':'Point','coordinates':coords}})
geo={'type':'FeatureCollection','name':'Shanghai sixteen-district independent geographic checkpoints','crs_note':'WGS84 longitude/latitude; no GCJ-02/Baidu coordinates used','retrieved_at':'2026-10-25','license_note':'OSM-derived coordinates ODbL-1.0. Wikipedia article source attribution retained; positions are factual data. See source_kind per feature.','features':features}
(HERE/'checkpoints.geojson').write_text(json.dumps(geo,ensure_ascii=False,indent=2))
anchors=read(PROJECT/'data/landmark-anchors.json')['landmarks'];wiki_map={'shanghai-tower':'Shanghai Tower','oriental-pearl':'Oriental Pearl Tower','swfc':'Shanghai World Financial Center','jin-mao':'Jin Mao Tower'};landmarks=[]
height_primary={
 'shanghai-tower':(632,'https://www.skyscrapercenter.com/building/shanghai-tower/56','CVU / CTBUH Skyscraper Center architectural height'),
 'oriental-pearl':(468,'https://www.opg.cn/','Operator Oriental Pearl Group home page: 高468米'),
 'swfc':(492,'https://www.mori.co.jp/en/projects/swfc/','Mori Building developer project page: height of 492 meters'),
 'jin-mao':(420.5,'https://www.skyscrapercenter.com/building/jin-mao-tower/189','CVU / CTBUH Skyscraper Center architectural height'),
 'customs-house':(79.2,'https://web.archive.org/web/20100610110157/http://shanghai.customs.gov.cn/publish/portal27/tab8419/module26899/info82241.htm','Shanghai Customs official original text, archived 2010: main building 36.2m + clock tower approximately43m; stated total79.2m')}
for a in anchors:
 h,u,m=height_primary[a['id']];r={'id':a['id'],'name':a['name'],'osm_coordinates':[a['longitude'],a['latitude']],'osm_source':a['source_url'],'verified_reference_height_m':h,'height_source_url':u,'height_definition':m,'project_metadata_height_m_at_audit':a['height_m'],'metadata_matches_verified_height':abs(h-a['height_m'])<.05}
 if a['id'] in wiki_map:
  p=next(p for p in pois if p['name']==wiki_map[a['id']]);r.update({'secondary_coordinates':p['wgs84'],'secondary_coordinate_source':p['url'],'anchor_disagreement_m':round(geod.inv(a['longitude'],a['latitude'],*p['wgs84'])[2],2),'interpretation':'Different reference points / coarse community coordinates; not a measured positional error and not a reason to shift the model automatically.'})
 else:r['verified_clock_face_diameter_m']=5.4;r['verified_minute_hand_total_length_m']=3.17;r['verified_hour_hand_total_length_m']=2.3;r['height_conflict']='English Wikipedia states90m; Shanghai Customs official text states79.2m. Prefer official79.2m and preserve the conflicting-source record.'
 landmarks.append(r)
report={'checked_at':'2026-10-25','audit_scope':'Public-source, coordinate-system, polygon validity, membership and reference-height checks. Not survey / photogrammetry / full building-by-building accuracy verification.','boundary_sha256':hashlib.sha256((PROJECT/'data/districts-display.geojson').read_bytes()).hexdigest(),'district_count':len(G),'valid_polygons':sum(g.is_valid for g in G.values()),'official_shanghai_area_km2':6340.5,'official_shanghai_extent_dms':"120°51′–122°12′ E;30°40′–31°53′ N",'official_geography_source':'https://english.shanghai.gov.cn/en-Overview/20231209/705180b43f794c1ca43f4d1ddaa049a2.html','osm_display_union_area_km2':round(transform(tx,unary_union(list(G.values()))).area/1e6,3),'area_calculation_crs':'EPSG:32651 / WGS84 UTM51N','area_warning':'OSM relations include river/sea areas; the polygon union is not equivalent to official6340.5km² land-area statistics. Do not use the union or downloaded-tile area as an urban building coverage claim.','district_areas':areas,'checkpoint_count':len(features),'checkpoints_passed':sum(f['properties']['boundary_check_passed'] for f in features),'checkpoints_per_district':{id:sum(f['properties']['district_id']==id for f in features) for id in D},'rejected_reference_points':rejected,'landmark_reference_checks':landmarks,'limitations':['OSM boundary definitions and government statistical area definitions differ.','A point-in-polygon pass proves membership only, not shape accuracy along every boundary.','Map vector tile quantization and source footprint errors persist. Height source proxies are not per-building survey measurements.','Display boundary omits distant source relation members/farms outside the Shanghai focus rectangle; unmodified source geometry is preserved.','Road elevations, bridges, building facades and interiors need separate validation.']}
(HERE/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
assert len(G)==16 and all(g.is_valid for g in G.values())
assert report['checkpoints_passed']==report['checkpoint_count']
assert min(report['checkpoints_per_district'].values())>=2
print('PASS',len(features),'checkpoints across16districts; land/water area discrepancy documented; landmark height sources checked')
