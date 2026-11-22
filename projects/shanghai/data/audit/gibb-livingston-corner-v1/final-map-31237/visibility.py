"""Measure reddish masonry in the central field, excluding the viewer's controls."""
from pathlib import Path
import sys
from PIL import Image
import numpy as np
im=np.asarray(Image.open(Path(sys.argv[1])).convert('RGB')).astype(np.int16)
height,width=im.shape[:2]
r,g,b=im[height//4:3*height//4,width//5:4*width//5].transpose(2,0,1)
print(float(((r>g+9)&(r>b+16)&(r>55)&(g<158)).mean()))
