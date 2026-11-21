from pathlib import Path
from urllib.request import urlopen
from websockets.sync.client import connect
import json,sys,datetime
w=Path(__file__).parent;tag=sys.argv[1];mode=sys.argv[2];pid=sys.argv[3] if len(sys.argv)>3 else None
p=w/tag/'main-browser.json';r=json.loads(p.read_bytes());assert r['id']=='xuhui-empire-mansions-street-front'
tabs=json.load(urlopen('http://127.0.0.1:19412/json/list'))
tab,=[q for q in tabs if q['type']=='page'and q['url'].startswith('http://127.0.0.1:31212/index.html')]
qry="""(()=>{const s=window.__SHANGHAI_APP__.scene,m=s.map,c=s.getCandidateIntegrationState(),t=s.getStreamingState();return {site:location.href,center:m.getCenter(),pitch:m.getPitch(),bearing:m.getBearing(),zoom:m.getZoom(),tiles:t.detail.active.filter(a=>a.id.startsWith('14-13719-6695')).map(a=>a.id),source:s.getLandmarkAssetState('xuhui-empire-mansions-street-front')?.status,vector:c.vector.map(q=>[q.active,q.pending]),groups:c.shader.ownerScopedSources.filter(a=>a.id.startsWith('14-13719-6695')).map(a=>[a.id,a.clip_feature_local_ids]),feature:m.getFeatureState({source:'overture-buildings',sourceLayer:'building',id:'f6143ecd-deae-485b-907a-04375a36d6af'})}})()"""
with connect(tab['webSocketDebuggerUrl'],max_size=1000000,open_timeout=5,close_timeout=2) as ws:
 def inspect(expr,nonce):
  ws.send(json.dumps(dict(id=nonce,method='Runtime.evaluate',params=dict(expression=expr,returnByValue=True))))
  while True:
   msg=json.loads(ws.recv(timeout=9))
   if msg.get('id')==nonce:
    assert 'exceptionDetails' not in msg['result'],msg
    return msg['result']['result'].get('value')
 state=inspect(qry,1)
 if mode=='zoom':
  assert Path('/proc')/str(int(pid));assert pid and 'check-map-stages.cjs' in (Path('/proc')/pid/'cmdline').read_text()
  assert tag in ('phone','desktop','mouse','touch') and ('map-mobile.png' if tag=='phone' else 'map-desktop.png' if tag=='desktop' else '') in [a['file']for a in r['screenshots']] and state['zoom']<17.31
  inspect("window.__SHANGHAI_APP__.scene.map.zoomTo(17.55,{duration:0});true",2)
  out=dict(stage=tag,at=datetime.datetime.now(datetime.timezone.utc).isoformat(),action='zoomTo(17.55) following the unchanged directory photograph',before=state,after=inspect(qry,3))
  (w/tag/'supplemental-zoom.json').write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps(state,indent=2))
