"""Resect the independent sign-side view against the photographed passage and its roof."""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import least_squares
from fit_gallery import GalleryPlane,project

HERE=Path(__file__).parent
# Primary image, depth from its exterior face, sign-side image, use in camera fit.
CLICKS=[
    ('passage upper left',(108,433),0,(900,359),True),
    ('passage upper right',(252,435),0,(1009,355),True),
    ('passage lower left',(108,569),0,(898,446),True),
    ('passage lower right',(252,568),0,(1006,452),False),
    ('small window upper left',(299,463),0,(1049,376),True),
    ('small window lower left',(299,514),0,(1047,411),False),
    ('small window upper right',(325,463),0,(1078,375),False),
    ('rainpipe foot',(269,563),-.07,(1023,450),True),
    ('rainpipe below collector',(270,341),-.08,(1029,289),True),
    ('main gutter step',(246,287),-.20,(1017,250),True),
    ('side ridge junction',(243,228),3.55,(984,213),False),
    ('portal garden upper right',(236,457),7.10,(952,370),True),
    ('portal garden upper left',(137,457),7.10,(867,371),False),
]
def make(p):
    x,y,z,yaw,pitch,roll,focal,horizon=p
    sy,cy=np.sin(yaw),np.cos(yaw);sp,cp=np.sin(pitch),np.cos(pitch)
    target=np.array([sy*cp,cy*cp,sp]);right=np.array([cy,-sy,0])
    down=np.cross(target,right)
    eye=np.array([x,y,z])
    def row(v):return np.r_[v,-v@eye]
    depth=row(target)
    px=focal*row(np.cos(roll)*right-np.sin(roll)*down)
    py=focal*row(np.sin(roll)*right+np.cos(roll)*down)
    return np.stack((540*depth+px,horizon*depth+py,depth))
def solve():
    plane=GalleryPlane();controls=[]
    for name,uv,depth,pixels,used in CLICKS:
        x,z=plane.at_depth(*uv,depth)
        controls.append(dict(feature=name,primary_pixel=uv,local=[x,depth,z],pixel=pixels,fit=used))
    def residual(p):
        m=make(p)
        out=[v for q in controls if q['fit'] for v in project(m,q['local'])-q['pixel']]
        out.extend([(p[6]-800)/160,(p[2]-1.55)/.45,p[4]/.09,(p[7]-405)/70])
        return out
    start=[-13,-13,1.65,.22,-.01,-.025,810,405]
    q=least_squares(residual,start,bounds=([-45,-50,.5,-1.45,-.45,-.10,450,250],[15,-4,3.8,1.45,.45,.10,1700,600]),max_nfev=8000)
    m=make(q.x)
    for a in controls:a['projected']=project(m,a['local']).tolist();a['error_px']=float(np.linalg.norm(np.subtract(a['projected'],a['pixel'])))
    return dict(photo='https://imagepphcloud.thepaper.cn/pph/image/149/275/342.jpg',size=[1080,810],parameters=q.x.tolist(),projection=m.tolist(),controls=controls,note='The sign and foliage conceal the left side of the portal. The last garden-side left corner and ridge are weak readings.',median_fit_px=float(np.median([v['error_px']for v in controls if v['fit']])),median_heldout_px=float(np.median([v['error_px']for v in controls if not v['fit']])))
if __name__=='__main__':
    r=solve();(HERE/'passage-station.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(r['parameters'],r['median_fit_px'],r['median_heldout_px'])
    for q in r['controls']:print(q['feature'],round(q['error_px'],2))
