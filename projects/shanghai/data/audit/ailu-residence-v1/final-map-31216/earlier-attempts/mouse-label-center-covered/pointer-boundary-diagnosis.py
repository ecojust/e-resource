"""Read the composed hit target across the real signed label, then close the stalled test page."""
from pathlib import Path
import json
from urllib.request import urlopen
from websockets.sync.client import connect
w=Path('/tmp/shanghai-main-216/final-map-31216/mouse')
tabs=json.load(urlopen('http://localhost:19416/json/list',timeout=2))
t=next(x for x in tabs if x['type']=='page' and 'xuhui-savoy-apartments' in x['url'])
with connect(t['webSocketDebuggerUrl'],open_timeout=2)as s:
 expr="""(()=>{const s=window.__SHANGHAI_APP__.scene,m=s.map;const a=s.getBuildingBeaconState();const l=a.labelPositions.find(x=>x.id==='xuhui-ailu-residence-garden-loggia');const e=m.getCanvas(),b=e.getBoundingClientRect();const rec=[];for(let u=-80;u<82;u+=6)for(let v=-23;v<=23;v+=3){const x=l.x+u,y=l.y+v;if(document.elementFromPoint(x+b.x,y+b.y)===e&&s.pickBuildingBeacon({x,y})===l.id)rec.push([x,y])}return{center:m.getCenter(),label:l,exposedHitPositions:rec,centerHit:document.elementFromPoint(l.x,l.y)?.outerHTML.slice(0,150),route:location.hash}})()"""
 s.send(json.dumps({'id':1,'method':'Runtime.evaluate','params':{'expression':expr,'returnByValue':True}}));r=json.loads(s.recv(timeout=4))['result']['result']['value'];assert r['route'].startswith('#landmark=xuhui-savoy') and r['exposedHitPositions'] and 'location-card' in r['centerHit']
 (w/'label-sampling-before-close.json').write_text(json.dumps(dict(**r,reason='The center-only test would wait 240 seconds while a different part of the same physically rendered label is exposed. Closed this test page to run the corrected normal interaction.'),indent=2)+'\n')
with connect(json.load(urlopen('http://localhost:19416/json/version',timeout=2))['webSocketDebuggerUrl'],open_timeout=2)as s:
 s.send(json.dumps({'id':1,'method':'Target.closeTarget','params':{'targetId':t['id']}}));print(s.recv(timeout=4),len(r['exposedHitPositions']),r['exposedHitPositions'][0])
