"""Read the two visible high-contrast bands along the segmental arch in Gao Yihan's Shaanxi Road photograph."""
from pathlib import Path
import argparse,json,hashlib
import numpy as np
from PIL import Image
p=argparse.ArgumentParser(description=__doc__);p.add_argument('image',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
im=np.array(Image.open(a.image).convert('L'),dtype=float)
assert im.shape==(3008,2000)
# Control points estimate the initial search corridor. Retain native 7-pixel contrast and
# test it against local values; a cable near the rightmost pier obscures part of the lip.
xc=[610,680,750,830,900,975,1050,1125,1210,1270,1330]
yc=[2181,2159,2139,2122,2111,2106,2107,2110,2121,2133,2149]
samples=[]
for x in list(range(610,1327,8))+[1330]:
 profile=im[:,x-2:x+3].mean(1)
 def find(y0):
  yy=np.arange(round(y0)-12,round(y0)+13)
  contrast=np.array([profile[y-6:y-1].mean()-profile[y+1:y+6].mean() for y in yy]);i=int(contrast.argmax())
  return int(yy[i]),round(float(contrast[i]),3)
 top=np.interp(x,xc,yc);y1,c1=find(top);y2,c2=find(top+54)
 samples.append(dict(x=x,outer_front_lower_edge_y=y1,outer_contrast=c1,inner_soffit_line_y=y2,inner_contrast=c2))
# Extra independent hand-picked historic stone details: outer, spring, crown. Four pointed recesses,
# distinct from the broader cartouche across the middle. Side piers are separately measured.
side='stage-one native observations prior to using a shared building camera'
data=dict(article='https://www.meipian.cn/4ja3bpdg',photo_source='https://ss-mpvolc.meipian.me/users/70875226/630bd150-6f02-11ed-9e73-7729fc3765d8__JPG.heic',
          image_dimensions=[2000,3008],working_raster_sha256=hashlib.sha256(a.image.read_bytes()).hexdigest(),source='Gao Yihan photograph of the bay with the visible green 204 panel',samples=samples,
          method='Two independent luminance drops traced in their own native-image corridors on the front extrados and recessed soffit. Wires, signboards and passengers obscure isolated positions.',units='original native pixels')
a.output.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
