"""Paint weathered multicoloured Shanghai grey brick and fine lime joints, without using photographic pixels."""
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
rng=np.random.default_rng(453);height,width=600,740
canvas=np.full((height,width,3),[106,103,86],dtype=np.float64)
for row in range(75):
 for col in range(-1,28):
  x=col*29+(row%2)*14;y=row*8
  left=max(x+1,0);right=min(x+28,width)
  if right<=left:continue
  clr=np.array([76,79,66])+rng.integers(-13,14)+rng.integers(-3,4,3)
  canvas[y+1:y+8,left:right]=clr
  canvas[y+1,left:right]+=5
canvas+=rng.normal(0,3,size=canvas.shape[:2])[:,:,None]
Image.fromarray(np.uint8(np.clip(canvas,0,255))).save(Path(__file__).with_name('grey-brick.png'),optimize=True)
