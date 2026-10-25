#!/usr/bin/env python3
"""Resumable whole-boundary extraction of Shanghai Overture building footprints.

pip install pmtiles mapbox-vector-tile shapely
python source/city/fetch_fullcity.py --stage plan

Defaults are relative to this project's root, independent of the working
directory: data/districts-display.geojson, data/fullcity-raw, .cache/fullcity.
The cache contains large temporary SQLite and PMTiles downloads; do not publish it.

Data: Overture buildings ODbL 1.0, including OSM and CC BY 4.0 East Asian
Buildings. No heights are fabricated here. Source maxzoom 14 is retained.
"""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import sqlite3
import time
from urllib.request import Request, urlopen

import mapbox_vector_tile
from mapbox_vector_tile.decoder import TileData
from pmtiles.tile import deserialize_header, deserialize_directory, find_tile, zxy_to_tileid
from shapely import make_valid, from_wkb, to_wkb
from shapely.geometry import shape, mapping, box, Point
from shapely.ops import unary_union
from shapely.prepared import prep

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parent.parent
P=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.ArgumentDefaultsHelpFormatter)
P.add_argument('--boundary',type=Path,default=PROJECT/'data/districts-display.geojson',help='District boundary GeoJSON')
P.add_argument('--output',type=Path,default=PROJECT/'data/fullcity-raw',help='Extracted raw snapshot directory')
P.add_argument('--cache',type=Path,default=PROJECT/'.cache/fullcity',help='Resumable temporary download/SQLite cache')
P.add_argument('--release',default='2026-10-21.0')
P.add_argument('--workers',type=int,default=6)
P.add_argument('--stage',choices=['all','plan','download','decode','assemble','export'],default='all')
A=P.parse_args()
OUT=A.output;CACHE=A.cache
for p in [OUT,CACHE,CACHE/'ranges',CACHE/'mvt']:p.mkdir(parents=True,exist_ok=True)
URL=f'https://tiles.overturemaps.org/{A.release}/buildings.pmtiles'
BOUNDARY=json.loads(A.boundary.read_text())
BOUNDARY_HASH=hashlib.sha256(A.boundary.read_bytes()).hexdigest()
DISTRICTS=[]
for f in BOUNDARY['features']:
 g=shape(f['geometry'])
 if not g.is_valid:g=make_valid(g)
 DISTRICTS.append({'id':str(f['properties'].get('id') or f['properties']['adcode']),
  'name':f['properties']['name'],'geometry':g,'prepared':prep(g),'bbox':g.bounds})
CITY=unary_union([d['geometry'] for d in DISTRICTS]);PREPARED_CITY=prep(CITY)
ZOOM=14;N=2**ZOOM
identity_path=CACHE/'identity.json'
identity={'release':A.release,'boundary_sha256':BOUNDARY_HASH}
if identity_path.exists() and json.loads(identity_path.read_text())!=identity:
 raise RuntimeError('Cache release/boundary mismatch. Choose a separate --cache directory.')
identity_path.write_text(json.dumps(identity))

def say(*args):print(time.strftime('%H:%M:%S'),*args,flush=True)
def write_json(path,data):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 tmp=path.with_suffix(path.suffix+'.tmp')
 tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2))
 tmp.replace(path)
def tile_lon(x):return x/N*360-180
def tile_lat(y):return math.degrees(math.atan(math.sinh(math.pi*(1-2*y/N))))
def tile_box(x,y):return [tile_lon(x),tile_lat(y+1),tile_lon(x+1),tile_lat(y)]
def xy(lon,lat):return int((lon+180)/360*N),int((1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*N)
def key_for(x,y):return f'{ZOOM}/{x}/{y}'

@lru_cache(maxsize=256)
def get_range(offset,length):
 path=CACHE/'ranges'/f'{offset}-{length}.bin'
 if path.exists() and path.stat().st_size==length:return path.read_bytes()
 for attempt in range(6):
  try:
   req=Request(URL,headers={'User-Agent':'Mozilla/5.0','Range':f'bytes={offset}-{offset+length-1}'})
   with urlopen(req,timeout=40) as r:
    if r.status!=206:raise IOError(f'Expected Range206, got {r.status}')
    data=r.read()
   if len(data)!=length:raise IOError(f'Wrong range length {len(data)} expected{length}')
   tmp=path.with_suffix(f'.{os.getpid()}.{time.time_ns()}.tmp');tmp.write_bytes(data);tmp.replace(path)
   return data
  except Exception:
   if attempt==5:raise
   time.sleep(min(10,1.2*2**attempt))

HEADER=deserialize_header(get_range(0,127))
if HEADER['max_zoom']<ZOOM:raise RuntimeError('Requested source zoom is unavailable')
@lru_cache(maxsize=64)
def directory(offset,length):return deserialize_directory(get_range(offset,length))
def tile_info(x,y):
 tile_id=zxy_to_tileid(ZOOM,x,y)
 offset,length=HEADER['root_offset'],HEADER['root_length']
 for _ in range(4):
  entry=find_tile(directory(offset,length),tile_id)
  if entry is None:return None
  if entry.run_length:
   return {'offset':HEADER['tile_data_offset']+entry.offset,'length':entry.length}
  offset,length=HEADER['leaf_directory_offset']+entry.offset,entry.length
 raise RuntimeError('PMTiles directory depth exceeded')

def plan():
 old=OUT/'plan.json'
 if old.exists():
  data=json.loads(old.read_text())
  if data.get('boundary_sha256')==BOUNDARY_HASH and data.get('release')==A.release:return data
 x0,y1=xy(CITY.bounds[0],CITY.bounds[1]);x1,y0=xy(CITY.bounds[2],CITY.bounds[3])
 tiles=[]
 for x in range(x0,x1+1):
  for y in range(y0,y1+1):
   bounds=tile_box(x,y);polygon=box(*bounds)
   if not PREPARED_CITY.intersects(polygon):continue
   ids=[d['id'] for d in DISTRICTS if d['prepared'].intersects(polygon)]
   tiles.append({'tile':[ZOOM,x,y],'key':key_for(x,y),'bbox':bounds,
    'district_ids':ids,'inside_city':PREPARED_CITY.covers(polygon)})
 say('PLAN queryingdirectory',len(tiles),'intersecting tiles')
 for i,t in enumerate(tiles):
  info=tile_info(t['tile'][1],t['tile'][2]);t['source']=info
  if i%250==0:say('PLAN',i,'/',len(tiles))
 data={'release':A.release,'url':URL,'boundary_file':str(A.boundary),'boundary_sha256':BOUNDARY_HASH,
  'boundary_bbox':list(CITY.bounds),'zoom':ZOOM,'planned_tiles':len(tiles),
  'source_present_tiles':sum(t['source'] is not None for t in tiles),
  'source_absent_tiles':sum(t['source'] is None for t in tiles),
  'compressed_tile_bytes':sum(t['source']['length'] for t in tiles if t['source']),
  'tiles':tiles}
 write_json(old,data)
 say('PLAN_DONE',data['source_present_tiles'],'present',data['source_absent_tiles'],'absent',data['compressed_tile_bytes'],'compressedbytes')
 return data

PLAN=plan();TILES={t['key']:t for t in PLAN['tiles']}

def download_one(t):
 _,x,y=t['tile'];path=CACHE/'mvt'/f'{x}-{y}.pbf.gz';length=t['source']['length']
 if path.exists() and path.stat().st_size==length:return 'cached'
 offset=t['source']['offset']
 # Tilebytes have their own cache; do not duplicate them under ranges/.
 for attempt in range(6):
  try:
   req=Request(URL,headers={'User-Agent':'Mozilla/5.0','Range':f'bytes={offset}-{offset+length-1}'})
   with urlopen(req,timeout=40) as r:
    if r.status!=206:raise IOError(f'Unexpected HTTP{r.status}')
    b=r.read()
   if len(b)!=length:raise IOError('Incomplete range')
   # A CRC/decompression check prevents poisoning a resumable tile cache.
   if HEADER['tile_compression'].value==2:gzip.decompress(b)
   tmp=path.with_suffix('.tmp');tmp.write_bytes(b);tmp.replace(path)
   return 'downloaded'
  except Exception:
   if attempt==5:raise
   time.sleep(min(10,1.2*2**attempt))
def download():
 wanted=[t for t in PLAN['tiles'] if t['source']]
 stats=Counter();failed=[]
 with ThreadPoolExecutor(max_workers=A.workers) as ex:
  futures={ex.submit(download_one,t):t for t in wanted}
  for i,f in enumerate(as_completed(futures),1):
   try:stats[f.result()]+=1
   except Exception as e:failed.append({'tile':futures[f]['tile'],'error':repr(e)})
   if i%100==0 or i==len(wanted):
    say('DOWNLOAD',i,'/',len(wanted),dict(stats),'failed',len(failed))
    write_json(OUT/'download-progress.json',{'total':len(wanted),'completed':sum(stats.values()),'stats':dict(stats),'failed':failed})
 return failed

DB=CACHE/'footprints.sqlite'
CON=sqlite3.connect(DB)
CON.execute('PRAGMA journal_mode=WAL');CON.execute('PRAGMA synchronous=NORMAL');CON.execute('PRAGMA cache_size=-131072')
CON.executescript('''
CREATE TABLE IF NOT EXISTS pieces(ident TEXT NOT NULL,tilekey TEXT NOT NULL,geometry BLOB NOT NULL,properties TEXT NOT NULL,PRIMARY KEY(ident,tilekey)) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS decoded(tilekey TEXT PRIMARY KEY,feature_count INTEGER,success INTEGER,error TEXT);
CREATE TABLE IF NOT EXISTS parent_parts(parent_id TEXT PRIMARY KEY) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS assembled(ownertile TEXT NOT NULL,ident TEXT NOT NULL,district TEXT NOT NULL,feature TEXT NOT NULL,renderable INTEGER NOT NULL,has_height INTEGER NOT NULL,layer TEXT NOT NULL,source TEXT NOT NULL,PRIMARY KEY(ownertile,ident)) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS state(key TEXT PRIMARY KEY,value TEXT);
''')
state=CON.execute("SELECT value FROM state WHERE key='boundary_hash'").fetchone()
if state and state[0]!=BOUNDARY_HASH:raise RuntimeError('Cache boundary changed: use a new --cache directory')
CON.execute("INSERT OR REPLACE INTO state VALUES('boundary_hash',?)",(BOUNDARY_HASH,));CON.commit()

def convert_coords(coords,x,y,extent):
 if isinstance(coords[0],(int,float)):
  return [round((x+coords[0]/extent)/N*360-180,8),round(math.degrees(math.atan(math.sinh(math.pi*(1-2*(y+coords[1]/extent)/N)))),8)]
 return [convert_coords(c,x,y,extent) for c in coords]

def decode_one(t):
 _,x,y=t['tile'];path=CACHE/'mvt'/f'{x}-{y}.pbf.gz'
 if not path.exists():return None
 data=path.read_bytes()
 if data[:2]==b'\x1f\x8b':data=gzip.decompress(data)
 decoded=mapbox_vector_tile.decode(data,default_options={'y_coord_down':True})
 local={};parentids=set()
 for layer,content in decoded.items():
  if layer not in ('building','building_part'):continue
  for feature in content['features']:
   props=feature.get('properties',{})
   if props.get('is_underground'):continue
   geo=feature['geometry']
   if geo['type'] not in ('Polygon','MultiPolygon'):continue
   geometry=shape({'type':geo['type'],'coordinates':convert_coords(geo['coordinates'],x,y,content['extent'])})
   if not geometry.is_valid:geometry=make_valid(geometry)
   if geometry.is_empty:continue
   if not t['inside_city'] and not PREPARED_CITY.intersects(geometry):continue
   oid=str(props.get('id') or feature.get('id'))
   ident=layer+':'+oid
   props=dict(props);props['id']=oid;props['source_layer']=layer
   if isinstance(props.get('sources'),str):
    try:props['sources']=json.loads(props['sources'])
    except ValueError:pass
   if layer=='building_part' and props.get('building_id'):parentids.add(props['building_id'])
   if ident in local:local[ident][0]=unary_union([local[ident][0],geometry])
   else:local[ident]=[geometry,props]
 rows=[(ident,t['key'],sqlite3.Binary(to_wkb(g)),json.dumps(p,ensure_ascii=False,separators=(',',':'))) for ident,(g,p) in local.items()]
 return rows,parentids

def decode():
 completed={row[0] for row in CON.execute('SELECT tilekey FROM decoded WHERE success=1')}
 pending=[t for t in PLAN['tiles'] if t['source'] and t['key'] not in completed]
 say('DECODE start',len(pending),'pending',len(completed),'cached')
 for i,t in enumerate(pending,1):
  try:
   result=decode_one(t)
   if result is None:raise FileNotFoundError('Source tile cache missing')
   rows,parents=result
   CON.executemany('INSERT OR REPLACE INTO pieces VALUES(?,?,?,?)',rows)
   CON.executemany('INSERT OR IGNORE INTO parent_parts VALUES(?)',[(x,) for x in parents])
   CON.execute('INSERT OR REPLACE INTO decoded VALUES(?,?,1,NULL)',(t['key'],len(rows)))
  except Exception as e:
   CON.execute('INSERT OR REPLACE INTO decoded VALUES(?,0,0,?)',(t['key'],repr(e)));say('DECODE_FAILED',t['key'],repr(e))
  if i%10==0 or i==len(pending):CON.commit()
  if i%50==0 or i==len(pending):
   n=CON.execute('SELECT SUM(feature_count) FROM decoded WHERE success=1').fetchone()[0] or 0
   say('DECODE',i,'/',len(pending),'fragments',n)
   write_json(OUT/'decode-progress.json',{'cached_tiles':len(completed),'processed_pending':i,'pending_total':len(pending),'fragments':n})
 CON.commit()

def polygonal(g):
 if g.is_empty:return None
 if not g.is_valid:g=make_valid(g)
 if g.geom_type in ('Polygon','MultiPolygon'):return g
 if g.geom_type=='GeometryCollection':
  parts=[p for p in g.geoms if p.geom_type in ('Polygon','MultiPolygon')]
  return unary_union(parts) if parts else None
 return None

def district_for(point,g):
 for d in DISTRICTS:
  x0,y0,x1,y1=d['bbox']
  if x0<=point.x<=x1 and y0<=point.y<=y1 and d['prepared'].covers(point):return d
 # Numerical boundaries: use maximum positive overlap rather than guessing.
 candidates=[(g.intersection(d['geometry']).area,d) for d in DISTRICTS if d['prepared'].intersects(g)]
 return max(candidates,key=lambda pair:pair[0])[1] if candidates else None

def assemble():
 parts={r[0] for r in CON.execute('SELECT parent_id FROM parent_parts')}
 state=CON.execute("SELECT value FROM state WHERE key='last_assembled_ident'").fetchone();last=state[0] if state else ''
 reader=sqlite3.connect(DB)
 cursor=reader.execute('SELECT ident,geometry,properties FROM pieces WHERE ident>? ORDER BY ident',(last,))
 batch=[];processed=0;discarded=0
 def finish(ident,geometries,props):
  nonlocal discarded
  if not geometries:return
  g=geometries[0] if len(geometries)==1 else unary_union(geometries)
  g=polygonal(g)
  if g is None or not PREPARED_CITY.intersects(g):discarded+=1;return
  if not PREPARED_CITY.covers(g):g=polygonal(g.intersection(CITY))
  if g is None or g.is_empty or g.area<=1e-15:discarded+=1;return
  point=g.centroid
  if not g.covers(point):point=g.representative_point()
  district=district_for(point,g)
  if district is None:discarded+=1;return
  x,y=xy(point.x,point.y);owner=key_for(x,y)
  props['district_id']=district['id'];props['district_name']=district['name']
  props['renderable']=not(props['source_layer']=='building' and props.get('has_parts') and props['id'] in parts)
  props['fragment_count']=len(geometries)
  feature={'type':'Feature','id':props['id'],'properties':props,'geometry':mapping(g)}
  tagged=any(isinstance(props.get(k),(int,float)) and props[k]>0 for k in ('height','num_floors'))
  batch.append((owner,ident,district['id'],json.dumps(feature,ensure_ascii=False,separators=(',',':')),
    int(props['renderable']),int(tagged),props['source_layer'],props.get('@geometry_source','unknown')))
 current=None;geoms=[];props=None
 for ident,blob,rawprops in cursor:
  if current is not None and ident!=current:
   finish(current,geoms,props);processed+=1
   if processed%2000==0:
    CON.executemany('INSERT OR REPLACE INTO assembled VALUES(?,?,?,?,?,?,?,?)',batch);batch.clear()
    CON.execute("INSERT OR REPLACE INTO state VALUES('last_assembled_ident',?)",(current,));CON.commit()
   if processed%20000==0:
    say('ASSEMBLE',processed,'IDs thisrun','discarded',discarded)
    write_json(OUT/'assemble-progress.json',{'processed_ids_this_run':processed,'discarded_this_run':discarded,'last_id':current})
   geoms=[]
  current=ident;geoms.append(from_wkb(blob));props=json.loads(rawprops)
 if current is not None:
  finish(current,geoms,props);processed+=1
  CON.executemany('INSERT OR REPLACE INTO assembled VALUES(?,?,?,?,?,?,?,?)',batch)
  CON.execute("INSERT OR REPLACE INTO state VALUES('last_assembled_ident',?)",(current,));CON.commit()
 reader.close();CON.execute('PRAGMA wal_checkpoint(TRUNCATE)');say('ASSEMBLE_DONE',processed,'IDs thisrun')

def audit_underground():
 cached=OUT/'underground-summary.json'
 if cached.exists() and (OUT/'excluded-underground.geojson.gz').exists():
  previous=json.loads(cached.read_text())
  if previous.get('release')==A.release and previous.get('boundary_sha256')==BOUNDARY_HASH:return previous
 items={};source_fragments=0;tiles_with_underground=0
 for index,t in enumerate(PLAN['tiles']):
  if not t['source']:continue
  z,x,y=t['tile'];n=2**z
  path=CACHE/'mvt'/f'{x}-{y}.pbf.gz'
  data=path.read_bytes()
  if data[:2]==b'\x1f\x8b':data=gzip.decompress(data)
  td=TileData(data);found_tile=False
  for layer in td.tile.layers:
   if layer.name not in ('building','building_part') or 'is_underground' not in layer.keys:continue
   underground_index=list(layer.keys).index('is_underground')
   true_indices={i for i,v in enumerate(layer.values) if v.HasField('bool_value') and v.bool_value}
   if not true_indices:continue
   for f in layer.features:
    if not any(k==underground_index and v in true_indices for k,v in zip(f.tags[::2],f.tags[1::2])):continue
    props={layer.keys[k]:td.parse_value(layer.values[v]) for k,v in zip(f.tags[::2],f.tags[1::2])}
    def transform(px,py):return (round((x+px/layer.extent)/n*360-180,8),round(math.degrees(math.atan(math.sinh(math.pi*(1-2*(y+py/layer.extent)/n)))),8))
    geo=td.parse_geometry(f.geometry,f.type,layer.extent,True,transform)
    g=shape(geo)
    if not g.is_valid:g=make_valid(g)
    if g.is_empty or not PREPARED_CITY.intersects(g):continue
    source_fragments+=1;found_tile=True
    oid=str(props.get('id',f.id));key=layer.name+':'+oid
    props['id']=oid;props['source_layer']=layer.name;props['renderable']=False
    props['render_exclusion']='source_is_underground'
    if isinstance(props.get('sources'),str):
     try:props['sources']=json.loads(props['sources'])
     except ValueError:pass
    entry=items.setdefault(key,{'props':props,'geometries':[]})
    entry['geometries'].append(g)
  if found_tile:tiles_with_underground+=1
  if index%500==0:print('UNDERGROUND_SCAN',index,'/',len(PLAN['tiles']),'unique',len(items),flush=True)
 features=[]
 for key,item in items.items():
  g=unary_union(item['geometries'])
  if not PREPARED_CITY.covers(g):g=g.intersection(CITY)
  if g.is_empty:continue
  features.append({'type':'Feature','id':item['props']['id'],'properties':item['props'],'geometry':mapping(g)})
 summary={'source':'Overture Maps buildings','release':PLAN['release'],'boundary_sha256':BOUNDARY_HASH,'unique_underground_features':len(features),'tile_fragments':source_fragments,
  'source_tiles_with_underground':tiles_with_underground,'aboveground_renderable':False,'reason':'Source is_underground=true. Excluded from above-ground extrusion; geometry and source height attributes retained here.',
  'with_height':sum(f['properties'].get('height') is not None for f in features),'with_min_height':sum(f['properties'].get('min_height') is not None for f in features),
  'layers':dict(Counter(f['properties']['source_layer'] for f in features)),'license':'ODbL-1.0'}
 p=OUT/'excluded-underground.geojson.gz'
 with gzip.open(p,'wt',encoding='utf-8') as out:json.dump({'type':'FeatureCollection','metadata':summary,'features':features},out,ensure_ascii=False,separators=(',',':'))
 (OUT/'underground-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
 print('UNDERGROUND_COMPLETE',summary,flush=True)
 return summary

def export():
 underground=audit_underground()
 owners=[r[0] for r in CON.execute('SELECT DISTINCT ownertile FROM assembled ORDER BY ownertile')]
 allrows=[]
 for i,owner in enumerate(owners,1):
  z,x,y=map(int,owner.split('/'));bounds=tile_box(x,y);origin=[(bounds[0]+bounds[2])/2,(bounds[1]+bounds[3])/2]
  count,renderable,tagged=CON.execute('SELECT COUNT(*),SUM(renderable),SUM(has_height) FROM assembled WHERE ownertile=?',(owner,)).fetchone()
  districtcounts=dict(CON.execute('SELECT district,COUNT(*) FROM assembled WHERE ownertile=? GROUP BY district',(owner,)))
  meta={'tile':[z,x,y],'origin':origin,'bbox':bounds,'release':A.release,'complete':True,'crs':'EPSG:4326 / WGS84',
   'feature_count':count,'renderable_count':renderable,'features_with_height_or_floors':tagged,'district_counts':districtcounts,
   'owner_rule':'Whole source UUID assigned to footprint centroid tile; representative point used if centroid is outside geometry.',
   'geometry':'All source tile fragments merged by layer+UUID, then clipped to the supplied city boundary. Holes retained.',
   'source_url':URL,'license':'ODbL-1.0','attribution':'© OpenStreetMap contributors; © Overture Maps Foundation; Qian Shi et al. East Asian Buildings (CC BY 4.0)'}
  target=OUT/'tiles'/str(z)/str(x)/(str(y)+'.geojson.gz');target.parent.mkdir(parents=True,exist_ok=True)
  if not target.exists():
   temp=target.with_suffix('.gz.tmp')
   with gzip.open(temp,'wt',encoding='utf-8',compresslevel=6) as f:
    f.write('{"type":"FeatureCollection","metadata":'+json.dumps(meta,ensure_ascii=False,separators=(',',':'))+',"features":[')
    first=True
    for (feature,) in CON.execute('SELECT feature FROM assembled WHERE ownertile=? ORDER BY ident',(owner,)):
     if not first:f.write(',')
     first=False;f.write(feature)
    f.write(']}')
   temp.replace(target)
  row={'tile':[z,x,y],'origin':origin,'bbox':bounds,'feature_count':count,'renderable_count':renderable,
       'features_with_height_or_floors':tagged,'district_counts':districtcounts,'bytes':target.stat().st_size,'file':str(target.relative_to(OUT))}
  allrows.append(row)
  if i%100==0 or i==len(owners):say('EXPORT',i,'/',len(owners))
  if i%100==0:write_json(OUT/'export-progress.json',{'complete':False,'tiles_written':i,'total_tiles':len(owners),'tiles':allrows})
 decoded={r[0]:{'features':r[1],'success':bool(r[2]),'error':r[3]} for r in CON.execute('SELECT tilekey,feature_count,success,error FROM decoded')}
 missing=[];coverage=[]
 for t in PLAN['tiles']:
  if t['source'] is None:status='source_no_tile'
  elif t['key'] not in decoded:status='not_downloaded_or_decoded'
  elif not decoded[t['key']]['success']:status='decode_failed'
  elif decoded[t['key']]['features']==0:status='source_no_city_features'
  else:status='decoded'
  if status in ('not_downloaded_or_decoded','decode_failed'):missing.append(t['tile'])
  coverage.append({'tile':t['tile'],'bbox':t['bbox'],'district_ids':t['district_ids'],'status':status,
   'source_bytes':t['source']['length'] if t['source'] else 0,'decoded_features':decoded.get(t['key'],{}).get('features',0)})
 districts=[]
 for d in DISTRICTS:
  count,renderable,tagged=CON.execute('SELECT COUNT(*),SUM(renderable),SUM(has_height) FROM assembled WHERE district=?',(d['id'],)).fetchone()
  ds=[t for t in coverage if d['id'] in t['district_ids']]
  districts.append({'id':d['id'],'name':d['name'],'feature_count':count,'renderable_count':renderable or 0,'features_with_height_or_floors':tagged or 0,
   'intersecting_tiles':len(ds),'tile_status_counts':dict(Counter(t['status'] for t in ds)),
   'geometry_sources':dict(CON.execute('SELECT source,COUNT(*) FROM assembled WHERE district=? GROUP BY source',(d['id'],)))})
 last_assembled=CON.execute("SELECT value FROM state WHERE key='last_assembled_ident'").fetchone()
 maximum_piece=CON.execute('SELECT MAX(ident) FROM pieces').fetchone()[0]
 assembly_complete=maximum_piece is None or (last_assembled is not None and last_assembled[0]==maximum_piece)
 unique_count=CON.execute('SELECT COUNT(DISTINCT ident) FROM assembled').fetchone()[0]
 total_count=CON.execute('SELECT COUNT(*) FROM assembled').fetchone()[0]
 duplicate_count=total_count-unique_count
 download_failed=sum(1 for t in PLAN['tiles'] if t['source'] and (not (CACHE/'mvt'/f"{t['tile'][1]}-{t['tile'][2]}.pbf.gz").exists() or (CACHE/'mvt'/f"{t['tile'][1]}-{t['tile'][2]}.pbf.gz").stat().st_size!=t['source']['length']))
 decode_failed=sum(t['status']=='decode_failed' for t in coverage)
 complete=not missing and assembly_complete and duplicate_count==0 and download_failed==0 and decode_failed==0
 manifest={'type':'Shanghai full-city building footprint extraction','complete':complete,'release':A.release,'source_url':URL,
  'license':'ODbL-1.0','attribution':'© OpenStreetMap contributors; © Overture Maps Foundation; Qian Shi et al. East Asian Buildings (CC BY4.0)',
  'boundary_sha256':BOUNDARY_HASH,'boundary_bbox':list(CITY.bounds),'boundary_scope':'Exact supplied districts-display.geojson, including its documented visualization clipping.',
  'source_zoom':ZOOM,'planned_tiles':PLAN['planned_tiles'],'source_present_tiles':PLAN['source_present_tiles'],'source_absent_tiles':PLAN['source_absent_tiles'],
  'compressed_source_bytes':PLAN['compressed_tile_bytes'],'missing_tiles':missing,'tile_status_counts':dict(Counter(t['status'] for t in coverage)),
  'output_tile_count':len(allrows),'feature_count':sum(r['feature_count'] for r in allrows),'renderable_count':sum(r['renderable_count'] for r in allrows),
  'unique_feature_count':unique_count,'renderable_feature_count':sum(r['renderable_count'] for r in allrows),
  'excluded_underground_unique_count':underground['unique_underground_features'],
  'source_unique_total_including_underground':unique_count+underground['unique_underground_features'],
  'underground_geometry_file':'excluded-underground.geojson.gz',
  'duplicate_feature_count':duplicate_count,'download_failed_count':download_failed,'decode_failed_count':decode_failed,'assembly_complete':assembly_complete,
  'output_bytes':sum(r['bytes'] for r in allrows),'districts':districts,'tiles':allrows,
  'limitations':['Complete means all planned source tiles were processed, not that every physical building is mapped.',
   'The PMTiles source maxzoom14 has quantized/generalized geometry. Source acquisition dates vary.',
   'Missing heights are not filled here. Rendering estimates must be marked separately.',
   'Source-no-tile areas can represent water, undeveloped terrain, or missing source coverage. No buildings are invented.']}
 write_json(OUT/'manifest.json',manifest);write_json(OUT/'coverage.json',{'complete':complete,'tiles':coverage})
 gaps=[{'type':'Feature','properties':{k:v for k,v in t.items() if k!='bbox'},'geometry':mapping(box(*t['bbox']))} for t in coverage if t['status']!='decoded']
 write_json(OUT/'coverage-gaps.geojson',{'type':'FeatureCollection','features':gaps})
 write_json(OUT/'district-boundary.geojson',BOUNDARY)
 if complete:(OUT/'COMPLETE').write_text(json.dumps({'release':A.release,'boundary_sha256':BOUNDARY_HASH,'feature_count':manifest['feature_count']}))
 elif (OUT/'COMPLETE').exists():(OUT/'COMPLETE').unlink()
 say('EXPORT_DONE',manifest['feature_count'],'features',manifest['output_tile_count'],'tiles',manifest['output_bytes'],'bytes','COMPLETE',manifest['complete'])

if A.stage in ('all','download'):
 failures=download()
 if failures:say('WARNING incomplete downloads; retry command to resume',len(failures))
if A.stage in ('all','decode'):decode()
if A.stage in ('all','assemble'):
 decoded_success={r[0] for r in CON.execute('SELECT tilekey FROM decoded WHERE success=1')}
 unavailable=[t['tile'] for t in PLAN['tiles'] if t['source'] and t['key'] not in decoded_success]
 if unavailable:
  write_json(OUT/'manifest.json',{'complete':False,'release':A.release,'missing_tiles':unavailable,'phase':'incomplete source decode; rerun to resume'})
  raise RuntimeError(f'{len(unavailable)} planned source tiles remain unavailable; rerun before assembling.')
 assemble()
if A.stage in ('all','export'):export()
CON.close()
