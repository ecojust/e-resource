"""Paint softly weathered red running-bond brick at Lixi Road and fine lime joints, without using photographic pixels."""
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
rng=np.random.default_rng(465);height,width=600,740
canvas=np.full((height,width,3),[120,87,76],dtype=np.float64)
for row in range((height+8)//9):
 for col in range(-1,28):
  x=col*29+(row%2)*14;y=row*9
  left=max(x+1,0);right=min(x+28,width)
  if right<=left:continue
  clr=np.array([153,79,60])+rng.integers(-13,14)+rng.integers(-3,4,3)
  canvas[y+1:y+9,left:right]=clr
  canvas[y+1,left:right]+=5
canvas+=rng.normal(0,3,size=canvas.shape[:2])[:,:,None]
Image.fromarray(np.uint8(np.clip(canvas,0,255))).save(Path(__file__).with_name('lixi-running-bond.png'),optimize=True)
