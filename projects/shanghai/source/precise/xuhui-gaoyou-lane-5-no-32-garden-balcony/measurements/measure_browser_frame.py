from pathlib import Path
import json,sys
import numpy as np
from PIL import Image
data=np.asarray(Image.open(sys.argv[1]).convert('RGB'))
area=data[:-14]
delta=np.abs(area.astype(np.int16)-data[1,1])
mask=delta.max(axis=2)>20
y,x=np.nonzero(mask)
rgb=area[mask].astype(np.uint32)
colours=(rgb[:,0]<<16)+(rgb[:,1]<<8)+rgb[:,2]
print(json.dumps(dict(foreground=int(mask.sum()),colors=len(np.unique(colours)),width=int(x.max()-x.min()+1) if len(x) else 0,height=int(y.max()-y.min()+1) if len(y) else 0)))
