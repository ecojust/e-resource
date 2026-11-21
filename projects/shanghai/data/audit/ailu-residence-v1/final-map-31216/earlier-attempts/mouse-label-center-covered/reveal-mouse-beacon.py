"""Pan the running public map with ordinary mouse input until its visible beacon accepts a genuine click."""
import datetime,json,time
from pathlib import Path
from urllib.request import urlopen
from websockets.sync.client import connect
b=Path('/tmp/shanghai-main-216/final-map-31216')
p=b/'mouse/camera-adjustment.json'
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
t=next(x for x in json.load(urlopen('http://localhost:19416/json/list',timeout=2)) if x['type']=='page' and '31216/index.html' in x['url'])
expression="""(()=>{const s=window.__SHANGHAI_APP__.scene,m=s.map,el=m.getCanvas(),r=el.getBoundingClientRect(),b=s.getBuildingBeaconState();const id='xuhui-ailu-residence-garden-loggia';const f=b.labelPositions.find(x=>x.id===id||x.memberIds?.includes(id));const free=[];for(let y=163;y>=80;y-=8){for(let x=390;x<531;x+=12){if(document.elementFromPoint(x,y)===el){free.push({x,y});break;}}}return {route:location.hash,center:m.getCenter(),zoom:m.getZoom(),label:f,hit:f?document.elementFromPoint(f.x+r.x,f.y+r.y)?.outerHTML.slice(0,138):null,free}})()"""
with connect(t['webSocketDebuggerUrl'],open_timeout=2)as ws:
 sequence=0
 def call(cmd,args):
  global sequence
  sequence+=1;ws.send(json.dumps(dict(id=sequence,method=cmd,params=args)))
  while True:
   r=json.loads(ws.recv(timeout=5))
   if r.get('id')==sequence:
    assert 'error' not in r,r
    return r['result']
 def observe():return call('Runtime.evaluate',{'expression':expression,'returnByValue':True})['result']['value']
 before=observe();print(before,flush=True)
 assert 'xuhui-savoy-apartments' in before['route'] and before['label'] and 'location-card' in before['hit']
 x,y=before['free'][0].values();events=[]
 for step,ty in enumerate(['mouseMoved','mousePressed']+['mouseMoved']*12+['mouseReleased']):
  v=dict(type=ty,x=x,y=y-(max(0,step-1)*6 if step<=13 else 72),button='left' if step else 'none',buttons=1 if 0<step<14 else 0,clickCount=1 if ty in ('mousePressed','mouseReleased') else 0)
  call('Input.dispatchMouseEvent',v);events.append(v);time.sleep(.04)
 time.sleep(.30)
 after=observe();print(after,flush=True)
 p.write_text(json.dumps(dict(view='mouse-only',host='http://127.0.0.1:31216/',started_from=before,observed_after_physical_drag=after,when=now(),cdp_mouse_events=events),indent=2)+'\n')
