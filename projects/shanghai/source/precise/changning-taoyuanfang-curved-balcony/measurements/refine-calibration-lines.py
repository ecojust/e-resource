"""Locate the sustained edge of each photographed wall, frame or drying rail within its inspected strip."""
import hashlib,json,runpy,sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter,map_coordinates
here=Path(__file__).absolute().parent
model=runpy.run_path(here/'register-balcony.py')
def find(im,line):
    p,q=np.asarray(line,float).reshape(2,2)
    axis=(q-p)/np.linalg.norm(q-p);n=np.array([-axis[1],axis[0]])
    f=np.linspace(.045,.955,64);t=np.arange(-10,10.1,.5)
    a,b=np.meshgrid(t,t);a=a.ravel()[:,None];b=b.ravel()[:,None]
    delta=a*(1-f)+b*f
    x=p[0]+f*(q[0]-p[0])+delta*n[0];y=p[1]+f*(q[1]-p[1])+delta*n[1]
    # A true edge keeps a common polarity along most of its length, with some occlusion by wires.
    hi=map_coordinates(im,[y+n[1]*1.15,x+n[0]*1.15],order=1)
    lo=map_coordinates(im,[y-n[1]*1.15,x-n[0]*1.15],order=1);diff=hi-lo
    median=np.median(diff,axis=1);sgn=np.where(median>=0,1.,-1.);positive=diff*sgn[:,None]
    score=.45*np.quantile(positive,.32,axis=1)+.55*np.quantile(positive,.56,axis=1)
    rank=score-.08*(abs(a[:,0])+abs(b[:,0]))-.10*abs(b[:,0]-a[:,0])
    j=np.argmax(rank);s,e=p+n*a[j,0],q+n*b[j,0]
    return dict(manual_strip=line,edge=[*s.tolist(),*e.tolist()],sustained_contrast=float(score[j]),
                normal_offset_px=[float(a[j,0]),float(b[j,0])])
if __name__=='__main__':
    path=Path(sys.argv[1]);assert hashlib.sha256(path.read_bytes()).hexdigest()==model['IMAGE']
    im=np.asarray(Image.open(path).convert('L').resize((1062,597),Image.Resampling.LANCZOS),float)
    levels=[[find(im,j) for j in v] for v in model['LINES']]
    (here/'line-observations.json').write_text(json.dumps(dict(original_sha256=model['IMAGE'],working_size=[1062,597],axes=levels),indent=2)+'\n')
    for g in levels:print([(r['normal_offset_px'],round(r['sustained_contrast']))for r in g])
