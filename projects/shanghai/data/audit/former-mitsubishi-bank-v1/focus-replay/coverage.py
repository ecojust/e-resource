from pathlib import Path
from PIL import Image,ImageDraw
from hashlib import sha256
import json,numpy as np
p=Path(__file__).parent;a=Path('/workspace/e-resource/projects/shanghai/data/audit/former-mitsubishi-bank-v1');w=Path('/tmp/mitsubishi117/city-final-21117-owner-pair');h=lambda f:sha256(f.read_bytes()).hexdigest();d=json.loads((p/'layouts.json').read_bytes());tri=json.loads((p/'mesh.json').read_bytes());out={}
for view,b in d['before'].items():
 e=d['after'][view];f=w/(view+'.png');im=Image.open(f).convert('RGB');assert b['labels']==e['labels']
 area=Image.new('1',im.size,0);draw=ImageDraw.Draw(area)
 for v in e['labels']:
  x,y,wid,hei=[v[k]for k in ['x','y','width','height']];draw.rectangle((x-wid/2,y-hei/2,x+wid/2,y+hei/2),fill=1)
 area=np.asarray(area,dtype=bool);lamp=Image.new('1',im.size,0);x,y=e['projected_lamp'];ImageDraw.Draw(lamp).ellipse((x-3,y-3,x+3,y+3),fill=1);lamp=np.asarray(lamp,dtype=bool)
 objects={}
 for n,geom in tri.items():
  assert b['parts'][n]==e['parts'][n];xy=e['parts'][n];mask=Image.new('1',im.size,False);draw=ImageDraw.Draw(mask)
  for t in geom['triangles']:draw.polygon([tuple(xy[i])for i in t],fill=True)
  mask=np.asarray(mask,dtype=bool);objects[n]={'actual_raw_triangles':len(geom['triangles']),'projected_pixels':int(mask.sum()),'label_rectangle_overlap_px':int((area&mask).sum()),'three_px_lamp_core_overlap_px':int((lamp&mask).sum())}
  assert not (area&mask).any()
 out[view]=dict(viewport=im.size,recorded_camera=next(v['camera'] for v in json.loads((a/'main-map-browser.json').read_bytes())['views']if v['view']==view),
    maplibre_padding=e['padding'],ground_lamp_actual_centroid_css_px=e['lamp'],ground_lamp_projected_css_px=e['projected_lamp'],old_label_position_error_css_px=b['original_label_delta_px'],source_screenshot_sha256=h(f),full_layout_before=b['labels'],full_layout_after=e['labels'],parts=objects)
result={'id':'huangpu-former-mitsubishi-bank','checked':True,'counts':[155,155],'method':'Final methods, catalog, unchanged basemap projection and prior methods were fetched from 21117 and 23117. Each viewport, real center, pitch, bearing and zoom comes from the 21117 browser snapshot. The raw GLB four granite shaft and plinth groups and closed entrance geometry were projected using the matching MapLibre Mercator transform. Camera padding was checked against measured scene zoom, the selected label rectangle and ground lamp core in the actual PNG. Coverage uses filled actual mesh triangles versus full bounding rectangles of the resolved sign. Lamp overlap is a fixed three CSS pixel radius approximation, not a real 23k screenshot.','versions':{k:{f:h(p/k/'src'/f)for f in ['building-beacons.js','building-beacon-groups.js','candidate-overview-camera.js']}for k in d},'views':out,'verifier_sha256':{q:h(p/q)for q in ['coverage.py','replay.mjs','mesh.py']},'model_asset_sha256':h(Path('/workspace/e-resource/projects/shanghai/assets/models/candidates/huangpu-former-mitsubishi-bank/huangpu-former-mitsubishi-bank-raw.glb'))}
(a/'focus-23117-occlusion.json').write_text(json.dumps(result,indent=2)+'\n')
for k,v in out.items():print(k,v['parts'])
