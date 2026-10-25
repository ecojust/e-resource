import pathlib,json,urllib.request,urllib.parse,datetime,time
B=pathlib.Path(__file__).parent;E=B/'evidence'
ds=json.loads((B.parent/'districts.geojson').read_text())['features'];q=['[out:json][timeout:45];'];m=[]
for f in ds:
 p=f['properties'];q.append(f"area({3600000000+p['osm_id']})->.a;")
 for key in ['roof:shape','roof:height','building:part']:
  q.append(f'wr(area.a)["{key}"];out count;');m.append({'adcode':p['adcode'],'name':p['name'],'key':key})
q='\n'.join(q);(B/'osm-16district-core-counts.overpassql').write_text(q);u='https://overpass-api.de/api/interpreter?'+urllib.parse.urlencode({'data':q});log={'endpoint':'https://overpass-api.de/api/interpreter','fetched_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'manifest':m};t=time.time()
try:
 r=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'ShanghaiPublicRoofCoverageAudit/1.0'}),timeout=60);d=r.read(500000);(E/'osm-16district-core-response.json').write_bytes(d);j=json.loads(d);log.update(status=r.status,bytes=len(d),osm3s=j.get('osm3s'),remark=j.get('remark'))
 if j.get('remark') or len(j['elements'])!=len(m):raise ValueError(f"incomplete: {len(j['elements'])}/{len(m)}; {j.get('remark')}")
 rows={}
 for meta,item in zip(m,j['elements']):
  row=rows.setdefault(str(meta['adcode']),{'adcode':meta['adcode'],'name':meta['name']});row[meta['key']]=int(item['tags']['total'])
 log['districts']=list(rows.values());(B/'osm-16district-core-counts.json').write_text(json.dumps(log,ensure_ascii=False,indent=2))
except Exception as e:log['error']=str(e)
log['elapsed_seconds']=time.time()-t;(E/'osm-16district-core-fetch-log.json').write_text(json.dumps(log,ensure_ascii=False,indent=2));print(json.dumps(log,ensure_ascii=False,indent=2))
