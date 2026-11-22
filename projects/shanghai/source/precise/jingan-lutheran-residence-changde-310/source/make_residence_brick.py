"""Draw a seamless grey face-brick texture for the Lutheran residence, in metres."""
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter
from PIL import Image
def create(output):
    # 6 long faces by 24 courses. One long face measures about 2 short faces.
    height,width=480,480
    rng=np.random.default_rng(600)
    y,x=np.mgrid[:height,:width];course=y//20
    phase=(x+(course%4)*20)%width
    # The front reveals a mix of long faces and headers. Each repeat is 120px
    # (one stretcher and one header), with two half-brick-lapped courses.
    head=phase%120>=80;cell=2*(phase//120)+head.astype(int)
    local=np.where(head,phase%120-80,phase%120)
    edge_x=np.minimum(local,np.where(head,39,79)-local)
    edge_y=np.minimum(y%20,19-y%20)
    m=np.clip((1.80-np.minimum(edge_x,edge_y))/.92,0,1)[...,None]
    offset=rng.normal(0,6.3,(24,8))[course,cell]
    tint=rng.normal(0,2.8,(24,8))[course,cell]
    texture=gaussian_filter(rng.normal(size=(height,width)),2.2,mode='wrap')*16+rng.normal(0,2.4,(height,width))
    face=np.array([115,105,98])+(offset+texture)[...,None]+tint[...,None]*np.array([1,.3,-.55])
    mortar=np.array([170,161,153])+texture[...,None]*.42
    Image.fromarray(np.uint8(np.clip(m*mortar+(1-m)*face,0,255))).save(output,optimize=True)
if __name__=='__main__':create(Path(__file__).with_name('changde-grey-brick.png'))
