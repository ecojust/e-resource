"""Reproject the 2019 photo and sample both edges of the staircase spandrels."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter1d
from register_street import Camera, SIZE

def rectify(path):
    camera=Camera(22)
    image=Image.open(path).convert('L')
    grid=np.array([[1/80,0,-12.2],[0,-1/80,16.75],[0,0,1]])
    homogeneous=np.column_stack([[1.,0,0],[0.,0,1.],-camera.C])
    matrix=camera.K@camera.R@homogeneous@grid
    matrix[0,:]*=image.width/SIZE[0]
    matrix[1,:]*=image.height/SIZE[1]
    matrix/=matrix[2,2]
    return np.asarray(image.transform((1920,1340),Image.Transform.PERSPECTIVE,
                        matrix.flatten()[:8],Image.Resampling.BICUBIC),dtype=float)

def controls(path):
    grey=rectify(path)
    result=[]
    searches=[('upper panel head',196,1),('upper panel foot',262,-1),
              ('middle panel head',360,1),('middle panel foot',426,-1),
              ('lower panel head',540,1),('lower panel foot',603,-1)]
    for name,limits in [('left',(575,596)),('right',(615,633))]:
        start,end=np.rint(np.array(limits)*1.6).astype(int)
        profile=np.quantile(grey[:,start:end],.7,axis=1)
        gradient=gaussian_filter1d(profile,3.,order=1)
        for tag,guess,sign in searches:
            # A large branch crosses the upper right panel's head; it has no clear light edge.
            if name=='right' and tag=='upper panel head':continue
            lo,hi=round((guess-4)*1.6),round((guess+4)*1.6)+1
            idx=lo+np.argmax(sign*gradient[lo:hi])
            px=idx/1.6
            result.append(dict(side=name,edge=tag,profile_limits=limits,
                               rectified_y=round(px,3),elevation_in_22m_frame=round(16.75-px/50,5),
                               signed_gradient=round(float(gradient[idx]),3)))
    return dict(photograph='42 Wanping Road.jpg, Livelikerw, 2019-02-23, CC BY-SA 4.0',
                original_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                method='Scene plane at Y=0, 22 m working frontage. In the 1920×1340 rectification X=px/80−12.2 and Z=16.75−py/80. Listed pixel positions are at the 1200×838 review size. A 70th-percentile luminance profile reduces wire occlusion.',
                readings=result)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('photo',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();a.output.write_text(json.dumps(controls(a.photo),indent=2,ensure_ascii=False)+'\n')
