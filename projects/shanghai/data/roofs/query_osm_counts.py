import pathlib,json,urllib.request,urllib.parse,datetime,time,hashlib
B=pathlib.Path(__file__).parent;E=B/'evidence'
districts=json.loads((B.parent/'districts.geojson').read_text())['features']
# Count ways/relations carrying each key, not unique real-world buildings.
cats=[('all_roof_or_part','wr.r'),('roof_shape','wr.r["roof:shape"]'),('roof_nonflat','wr.r["roof:shape"]["roof:shape"!~"^(flat|no|none|unknown)$"]'),('roof_height','wr.r["roof:height"]'),('roof_direction','wr.r["roof:direction"]'),('roof_orientation','wr.r["roof:orientation"]'),('roof_angle','wr.r["roof:angle"]'),('building_part','wr.r["building:part"]["building:part"!="no"]')]
lines=['[out:json][timeout:95];'];manifest=[]
for f in districts:
 p=f['properties']; aid=3600000000+int(p['osm_id'])
 lines.append(f'area({aid})->.a;wr(area.a)[~"^(roof:shape|roof:height|roof:direction|roof:orientation|roof:angle|building:part)$"~"."]->.r;')
 for cat,s in cats:
  lines.append(s+';out count;');manifest.append({'adcode':p['adcode'],'name':p['name'],'osm_relation':p['osm_id'],'metric':cat})
query='\n'.join(lines);(B/'osm-16district-counts.overpassql').write_text(query)
(B/'osm-16district-count-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
endpoint='https://overpass.kumi.systems/api/interpreter';started=time.time()
log={'endpoint':endpoint,'fetched_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'query_file':'osm-16district-counts.overpassql'}
try:
 req=urllib.request.Request(endpoint,data=urllib.parse.urlencode({'data':query}).encode(),headers={'User-Agent':'ShanghaiPublicRoofCoverageAudit/1.0'})
 r=urllib.request.urlopen(req,timeout=115);payload=r.read(2000000);(E/'osm-16district-counts-response.json').write_bytes(payload);d=json.loads(payload)
 log.update(status=r.status,bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest(),osm3s=d.get('osm3s'),remark=d.get('remark'),elapsed_seconds=time.time()-started)
 if d.get('remark') or len(d.get('elements',[]))!=len(manifest):raise ValueError(f"Incomplete count output: {len(d.get('elements',[]))}/{len(manifest)}; {d.get('remark')}")
 rows={}
 for expected,got in zip(manifest,d['elements']):
  if got['type']!='count':raise ValueError('Unexpected output type')
  code=str(expected['adcode']);row=rows.setdefault(code,{'adcode':expected['adcode'],'name':expected['name'],'osm_relation':expected['osm_relation']});row[expected['metric']]=int(got['tags']['total'])
 out={'metadata':log,'meaning':'OSM way/relation counts by administrative area. Categories overlap; counts are not unique real-world buildings. Keys present are not quality verification.','districts':list(rows.values())}
 (B/'osm-16district-counts.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)); print(json.dumps(out,ensure_ascii=False,indent=2))
except Exception as e:log.update(error=str(e),elapsed_seconds=time.time()-started);print(json.dumps(log,ensure_ascii=False,indent=2))
(E/'osm-16district-fetch-log.json').write_text(json.dumps(log,ensure_ascii=False,indent=2))
