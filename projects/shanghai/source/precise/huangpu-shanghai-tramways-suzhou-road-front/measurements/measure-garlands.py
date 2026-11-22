"""Map the four individual red relief wreaths from the 2015 South Suzhou Road photograph."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image,ImageDraw,ImageOps
from scipy.ndimage import binary_closing,gaussian_filter,label
from shapely.geometry import Polygon
import contourpy

BOXES=[(185,2440,352,2750),(579,2145,798,2430),(1100,1830,1345,2130),(1790,1420,2034,1815)]
def large_ring(im):
    rgb=np.asarray(im,dtype=float)
    r,g,b=rgb.transpose(2,0,1)
    # Compared with the olive limestone, red fired pieces remain redder than
    # green in the shade. Fine highlights and shaded crevices are reconciled
    # from their neighbours in a limited band around the same ornament.
    red=(r-g)-.35*(g-b)
    chroma=gaussian_filter(red,.72)
    mask=(chroma>9.)&(r>30)
    lbl,n=label(binary_closing(mask,iterations=2))
    sizes=np.bincount(lbl.ravel());sizes[0]=0
    biggest=lbl==np.argmax(sizes)
    return rgb,chroma,biggest
def outline(mask):
    return [p for p in contourpy.contour_generator(z=mask.astype(float)).lines(.5)if np.linalg.norm(p[0]-p[-1])<2]
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('photo',type=Path);ap.add_argument('dir',type=Path);a=ap.parse_args()
    im=ImageOps.exif_transpose(Image.open(a.photo))
    sheet=Image.new('RGB',(4*232,338),'#f9f7f0')
    for i,bb in enumerate(BOXES):
        tile=im.crop(bb);rgb,ch,mask=large_ring(tile)
        pic=tile.copy();draw=ImageDraw.Draw(pic)
        lines=outline(mask)
        for p in lines:
            if len(p)>40:draw.line([tuple(v)for v in p],fill='#65ffb6',width=1)
        pic.thumbnail((225,325));sheet.paste(pic,(i*232,0))
        print(i,mask.sum(),[(len(t),int(Polygon(t).area))for t in lines if len(t)>40])
    sheet.save(a.dir/'first-mask.jpg',quality=93)
