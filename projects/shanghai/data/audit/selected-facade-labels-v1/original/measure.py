"""Measure label rectangle coverage of exactly the primary mesh's rasterised triangle silhouette."""
from PIL import Image,ImageDraw
from pathlib import Path
import json,numpy as np,hashlib
w=Path(__file__).resolve().parent
src=Path('/workspace/e-resource/projects/shanghai/data/audit/hamilton-house-v1')
load=lambda p:json.loads(p.read_bytes())
sha=lambda b:hashlib.sha256(b).hexdigest()
run=load(w/'result.json');bind=load(w/'bindings.json');idx=np.load(w/'indices.npy')
oldD=load(src/'public-zoom-steps.json')['views'][0]
out=dict(estimate='Triangle-silhouette mask at one pixel per real CSS pixel, intersected with actual symbol sprite rectangles. A street building in front of these triangles can separately occlude them. Screenshots show actual drawn colour and neighbouring buildings.',web_sha256=bind['mesh']['input_sha256'],num_triangles=len(idx),checks={})
for key,view in run['views'].items():
 W,H=view['viewport'];xy=load(w/(key+'-projection.json'));img=Image.new('1',(W,H));dr=ImageDraw.Draw(img)
 for tri in idx:dr.polygon([tuple(xy[i])for i in tri],fill=1)
 mask=np.asarray(img,dtype=bool);total=int(mask.sum())
 def region(bb):return [max(0,round(bb[0])),max(0,round(bb[1])),min(W,round(bb[2])),min(H,round(bb[3]))]
 def count(labels):
  out=np.zeros((H,W),bool)
  for i in labels:
   x,y=i['x'],i['y'];w,h=i['width'],i['height'];l,t,r,b=region([x-w/2,y-h/2,x+w/2,y+h/2]);out[t:b,l:r]=True
  return int((out&mask).sum())
 names=[{'id':i['id'],'labelX':i['x'],'labelY':i['y'],'width':i['width'],'height':i['height'],'compact':i['compact']}for i in view['labels']]
 measures=dict(screenshot_sha256=view['sha256'],projected_mesh_pixels=total,mesh_pixels_beneath_actual_label_rectangles=count(view['labels']),ids=names,nine_point_app_hits=sum(len(i['hits'])for i in view['labels']),old_unchanged_camera=True)
 if key=='desktop':
  assert set(i['id']for i in oldD['labels'])==set(i['id']for i in view['labels'])
  measures['old_mesh_pixels_beneath_actual_label_rectangles']=count(oldD['labels'])
  assert measures['mesh_pixels_beneath_actual_label_rectangles']<measures['old_mesh_pixels_beneath_actual_label_rectangles']
  measures['old_file_sha256']=sha((src/'main-desktop.png').read_bytes())
 else:measures['old_file_sha256']=sha((src/'main-mobile.png').read_bytes())
 out['checks'][key]=measures
(w/'mesh-and-labels.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print({k:(v['projected_mesh_pixels'],v['mesh_pixels_beneath_actual_label_rectangles'],v.get('old_mesh_pixels_beneath_actual_label_rectangles')) for k,v in out['checks'].items()})
