"""Original procedural stone colour fields and separately jointed terrace tiles."""
from pathlib import Path
import math
import numpy as np
from PIL import Image
from terraced_section import FRAME, FIRST, LAST, PITCH, LENGTH, UPPER, FRONT

from terrace_material import TILES, TEXTURE

def create_tiles():
    rng=np.random.default_rng(19340204)
    centers=[np.array(v) for v in [[155,152,144],[150,147,138],[122,121,115],[115,116,111]]]
    halves=[]
    for v in centers:
        grain=rng.normal(0,2.6,(96,96)); flecks=rng.random((96,96)); grain+=(flecks>.974)*7-(flecks<.035)*7
        halves.append(np.uint8(np.clip(v+grain[:,:,None],0,255)))
    atlas=np.vstack((np.hstack(halves[:2]),np.hstack(halves[2:])))
    Image.fromarray(atlas).save(TEXTURE,optimize=True)

def pavement(b,lod):
    reference=FRAME['grid_i_at_post_row'];inside=FRAME['upper_room_x_m']+.002;outside=FRONT[3]-.192
    for j in range(math.floor(FIRST),math.ceil(LAST)):
        ya=max(0,(j-FIRST)*PITCH)+.0024;yb=min(LENGTH-.193,(j+1-FIRST)*PITCH)-.0024
        if yb-ya<.009:continue
        for i in range(math.floor(inside/PITCH+reference),math.ceil(outside/PITCH+reference)):
            xa=max(inside,(i-reference)*PITCH)+.0024;xb=min(outside,(i+1-reference)*PITCH)-.0024
            if xb-xa<.009:continue
            base=UPPER-.002;top=UPPER+.009
            verts=[(xa,ya,top),(xb,ya,top),(xb,yb,top),(xa,yb,top), (xa,ya,base),(xb,ya,base),(xb,yb,base),(xa,yb,base)]
            faces=[(0,1,2,3)] if lod else [(0,1,2,3),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]
            b.add(verts,faces,TILES,'Sundeck/pavement row '+str(j+1))
            # Four independent fields in one original atlas. No reference-image pixels enter the model.
            dark=(i+j)%2;variant=((i*17+j*23)//4)%2;u=.5*variant;v=.5*dark
            uv=[(u+.021,v+.021),(u+.478,v+.021),(u+.478,v+.478),(u+.021,v+.478)]
            b.parts[-1]['texcoords']=uv+uv
if __name__=='__main__':create_tiles()
