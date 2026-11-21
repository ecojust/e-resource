from pathlib import Path
from urllib.request import urlopen
from websockets.sync.client import connect
from datetime import datetime,timezone
import json
w=Path('/tmp/libo181');p=next(q for q in json.load(urlopen('http://127.0.0.1:9881/json/list',timeout=2))if q.get('type')=='page')
assert p['url'].startswith('http://127.0.0.1:31181/')
def now():return datetime.now(timezone.utc).isoformat()
with connect(p['webSocketDebuggerUrl'],open_timeout=2,close_timeout=1)as conn:
 seq=0
 def call(method,params):
  global seq
  seq+=1;conn.send(json.dumps({'id':seq,'method':method,'params':params}))
  while True:
   obj=json.loads(conn.recv(timeout=10))
   if obj.get('id')==seq:
    assert 'error'not in obj,obj
    return obj['result']
 def ev(expr):return call('Runtime.evaluate',dict(expression=expr,returnByValue=True))['result']['value']
 prepare="""(()=>{const s=window.__SHANGHAI_APP__.scene,m=s.map,e=document.querySelector('#zoom-out');const b=e.getBoundingClientRect(),x=b.left+b.width/2,y=b.top+b.height/2;const a=s.getLandmarkAssetState('xuhui-libo-garden-east-house');const tile=m.transform;const triggered={before:{zoom:m.getZoom(),pitch:m.getPitch(),eye:tile.getCameraLngLat(),altitude:tile.getCameraAltitude(),variant:a.variant,visible:a.visible},x,y,marked:document.elementFromPoint(x,y)===e||e.contains(document.elementFromPoint(x,y))};window.__liboPublicDistant=triggered;e.addEventListener('click',v=>{triggered.click={trusted:v.isTrusted,button:v.button,detail:v.detail,at:new Date().toISOString()}},{once:true,capture:true});return triggered})()"""
 before=ev(prepare);assert before['marked'] and before['before']['variant']=='full' and abs(before['before']['zoom']-15.65)<.02
 x,y=before['x'],before['y'];start=now()
 call('Input.dispatchMouseEvent',dict(type='mouseMoved',x=x,y=y))
 call('Input.dispatchMouseEvent',dict(type='mousePressed',x=x,y=y,button='left',buttons=1,clickCount=1))
 call('Input.dispatchMouseEvent',dict(type='mouseReleased',x=x,y=y,button='left',buttons=0,clickCount=1))
 outcome=ev('window.__liboPublicDistant');assert outcome['click']['trusted'] and outcome['click']['button']==0
 f=w/'public-distant-zoom.json';assert not f.exists();f.write_text(json.dumps(dict(passed=True,url=p['url'],started=start,finished=now(),selector='#zoom-out',**outcome),ensure_ascii=False,indent=2)+'\n');print(outcome)
