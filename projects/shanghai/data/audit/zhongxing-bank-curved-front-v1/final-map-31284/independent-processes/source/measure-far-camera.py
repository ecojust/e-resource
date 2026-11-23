from pathlib import Path
import json,urllib.request,datetime,sys
from websockets.sync.client import connect
def camera(ws,expression):
 ws.send(json.dumps(dict(id=1,method='Runtime.evaluate',params=dict(expression=expression,returnByValue=True,awaitPromise=True))))
 answer=json.loads(ws.recv(timeout=6))
 if not 'value' in answer['result']['result']:raise RuntimeError(answer)
 return answer['result']['result']['value']
tab=next(t for t in json.load(urllib.request.urlopen('http://127.0.0.1:19484/json/list',timeout=2)) if t['type']=='page')
read="""(()=>{const s=window.__SHANGHAI_APP__.scene,m=s.map,eye=m.transform.getCameraLngLat(),z=m.transform.getCameraAltitude(),id='huangpu-zhongxing-bank-curved-front',a=s.getLandmarkAssetState(id),anchor=a.anchor,x=(eye.lng-anchor[0])*Math.cos(anchor[1]*Math.PI/180)*111195,y=(eye.lat-anchor[1])*111195,d=Math.hypot(x,y,z-10.8);return {route:location.hash,zoom:m.getZoom(),eye:[eye.lng,eye.lat,z],distance:d,variant:a.variant,visible:a.visible,triangles:a.triangles};})()"""
with connect(tab['webSocketDebuggerUrl'],open_timeout=2) as ws:
 before=camera(ws,read);print(before,flush=True)
 if len(sys.argv)>1 and before['distance']<950 and before['variant']=='full':
  delta=max(.3,min(1.4,__import__('math').log2(1050/before['distance'])))
  camera(ws,'(()=>{const s=window.__SHANGHAI_APP__.scene,m=s.map;m.jumpTo({zoom:'+str(before['zoom']-delta)+'});s.loadLandmarks();s.refreshBuildingBeacons();return true;})()')
  after=camera(ws,read); print(after,flush=True)
  path=Path('/dev/shm/zhongxing284-live/evidence/distant/far-camera-adjustment.json')
  path.write_text(json.dumps(dict(at=datetime.datetime.now(datetime.timezone.utc).isoformat(),before=before,after=after),indent=2)+'\n')
