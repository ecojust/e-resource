"""Rasterize the measured camera projections and overlay bounds in the accompanying screenshots."""
from pathlib import Path
from hashlib import sha256
import json
import sys
import numpy as np
from PIL import Image,ImageDraw
w=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parent;r=json.loads((w/'public-zoom-steps.json').read_bytes())
def mask(size,polys):
 o=Image.new('1',size);d=ImageDraw.Draw(o)
 for v in polys:d.polygon([tuple(p)for p in v],fill=1)
 return np.asarray(o,dtype=bool)
def rect(x0,y0,x1,y1):return [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
all=[]
for state in r['views']:
 f=w/state['file'];assert sha256(f.read_bytes()).hexdigest()==state['sha256'];im=Image.open(f).convert('RGB');size=im.size
 left=lambda a:rect(a['x']-a['width']/2,a['y']-a['height']/2,a['x']+a['width']/2,a['y']+a['height']/2)
 labels=mask(size,[left(c)for c in state['labels']]);dom=mask(size,[rect(c['x0'],c['y0'],c['x1'],c['y1'])for c in state['controls']])
 pix=np.asarray(im,dtype=np.int32);green=(pix[:,:,1]>pix[:,:,0]*1.27)&(pix[:,:,1]>32)&(pix[:,:,1]<139)&(pix[:,:,2]>pix[:,:,0]*1.2)
 label=state['selectedLabel'];spot=mask(size,[left(label)]);result={}
 for name,poly in state['polygons'].items():
  reg=mask(size,[poly]);n=int(reg.sum()); clear=reg&~(labels|dom)
  result[name]={'projected_in_view_pixels':n,'pixels_under_rendered_beacon_bounds':int((reg&labels).sum()),'pixels_under_active_ui_bounds':int((reg&dom).sum()),
   'remaining_projection_pixels':int(clear.sum()),'remaining_fraction':round(clear.sum()/max(n,1),3),'covered_with_observed_green_sign_pixels':int((reg&labels&green).sum())}
 all.append({'step':state['step'],'screenshot':state['file'],'sha256':state['sha256'],'camera':state['camera'],'nav_open':state['navExpanded']=='true','geometry':result,'target_sign_bounds':left(label),'target_sign_dark_green_pixels':int((spot&green).sum())})
out={'source_report_sha256':sha256((w/'public-zoom-steps.json').read_bytes()).hexdigest(),'checker_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),'basis':'Screen projections of three photographed faces plus the central tower, with the public map projection at actual model heights. Projection counts estimate possible visible area. Screen UI and actually rendered name-label bounds are removed, with green pixels read from the unmodified screenshot. Values do not subtract other 3-D mesh occlusion or invent hidden surface pixels.','completed':r['completed'],'steps':all}
(w/'projected-pixel-review.json').write_text(json.dumps(out,indent=2)+'\n')
print([(v['step'],[(k,c['remaining_projection_pixels'],c['remaining_fraction'])for k,c in v['geometry'].items()])for v in all],flush=True)
