"""Paint original horizontal brick courses with stepped red diamonds and lozenge centres."""
from pathlib import Path
import numpy as np
from PIL import Image
SIZE = 1536
Y,X = np.indices((SIZE,SIZE))
height=(SIZE-1-Y)*25/SIZE-.2
x=X*27/SIZE-.5
# The two types of brick alternate in a stretcher bond. Individual headers define each diagonal.
course=np.floor(height/.081).astype(int)
t=x/.237+course%2*.5
brick=np.floor(t).astype(int)
xc=(brick+.5-course%2*.5)*.237
zc=(course+.5)*.081
ux=(xc+.36)%2.13/2.13
uz=(zc-.28)%1.98/1.98
distance=np.abs(2*ux-1)+np.abs(2*uz-1)
red=(np.abs(distance-1)<.165)|(distance<.16)
salt=((brick*37+course*53+brick*course*7)%23)-11
rgb=np.where(red[:,:,None],np.array([136,83,70]),np.array([210,181,142]))+salt[:,:,None]*.66
joint=(t%1<.040)|((height/.081)%1<.074)
rgb=np.where(joint[:,:,None],np.array([135,123,106]),rgb)
Image.fromarray(rgb.clip(0,255).astype('uint8')).save(Path(__file__).with_name('strand-diaper-brick.png'),optimize=True)
