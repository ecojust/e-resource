"""Fetch a small, reproducible OSM road/node extract for the Bund streetscape."""
from pathlib import Path
import json, urllib.request, urllib.parse, hashlib, datetime
ROOT=Path(__file__).resolve().parent
BBOX=(31.2347,121.4833,31.2426,121.4898)
query='[out:json][timeout:60];(way["highway"~"^(primary|primary_link|secondary|secondary_link|tertiary|tertiary_link|residential|unclassified|service|living_street|trunk|trunk_link)$"]('+','.join(map(str,BBOX))+');node["natural"="tree"]('+','.join(map(str,BBOX))+');node["highway"~"^(street_lamp|crossing|traffic_signals)$"]('+','.join(map(str,BBOX))+'););out geom;'
errors=[]
for endpoint in ['https://overpass-api.de/api/interpreter','https://overpass.kumi.systems/api/interpreter']:
 try:
  request=urllib.request.Request(endpoint,data=urllib.parse.urlencode({'data':query}).encode(),headers={'User-Agent':'ShanghaiPublicHeritageReconstruction/4.0 (OSM geometry research)'})
  with urllib.request.urlopen(request,timeout=85) as response: payload=response.read()
  data=json.loads(payload)
  if not data.get('elements'):raise ValueError('Empty road extract')
  (ROOT/'osm-roads.json').write_bytes(payload)
  (ROOT/'road-source.json').write_text(json.dumps({'endpoint':endpoint,'query':query,'bbox_south_west_north_east':BBOX,'fetched_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'timestamp_osm_base':data.get('osm3s',{}).get('timestamp_osm_base'),'bytes':len(payload),'sha256':hashlib.sha256(payload).hexdigest(),'license':'ODbL-1.0','attribution':'© OpenStreetMap contributors'},ensure_ascii=False,indent=2))
  print('Fetched',len(data['elements']),'elements,',len(payload),'bytes');break
 except Exception as exc:errors.append(str(exc))
else:raise RuntimeError(errors)
