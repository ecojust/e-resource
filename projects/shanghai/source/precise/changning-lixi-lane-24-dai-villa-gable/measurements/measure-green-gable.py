"""Align the single gable plane between two photographs and sample its boundary at the roof trim."""
from pathlib import Path
import json,hashlib,sys
from PIL import Image
import numpy as np
from scipy.ndimage import gaussian_filter1d
m=Path(__file__).absolute().parent
DISTRICT='b4b92c039830a099078231ddab830537e34f58f6e0a0582c96c6bb2d802e1961'
B_CORNERS=[[177,65],[396,78],[26,304],[572,371]]
A_CORNERS=[[256,22],[507,39],[79,280],[690,323]]
TRAIN=[106,124,146,169,195,223,250,276,300,322,344]
COARSE=[[77,394],[130,405],[210,437],[265,471],[310,512],[371,570]]
def homography(src,dst):
    matrix=[];rhs=[]
    for (u,v),(x,y) in zip(src,dst):
        matrix.extend([[u,v,1,0,0,0,-u*x,-v*x],[0,0,0,u,v,1,-u*y,-v*y]]);rhs.extend([x,y])
    return np.r_[np.linalg.solve(matrix,rhs),1].reshape(3,3)
def transform(uv,H):
    a=np.atleast_2d(uv);q=np.column_stack([a,np.ones(len(a))])@H.T
    return q[:,:2]/q[:,2,None]
def read(source):
    assert hashlib.sha256(source.read_bytes()).hexdigest()==DISTRICT
    im=Image.open(source).convert('RGB').resize((1490,1000),Image.Resampling.LANCZOS).crop((85,140,475,592)).resize((639,740),Image.Resampling.LANCZOS)
    return np.asarray(im,int)
def measure(im,y):
    # The dark green paint changes to the grey-beige strip beneath the clay tile.
    # The outer edge of that strip meets much redder fired clay.
    c=im[y-2:y+3,:,0]-im[y-2:y+3,:,1];c=gaussian_filter1d(np.median(c,axis=0),1.35)
    approx=np.interp(y,*np.transpose(COARSE));start,end=int(approx-17),int(approx+22)
    candidates=[x for x in range(start,end)if c[x]<=14<c[x+1] and np.median(c[x-8:x-1])<10 and np.median(c[x+3:x+11])>14]
    if not candidates:return None
    x=min(candidates,key=lambda j:abs(j-approx));u=x+(14-c[x])/(c[x+1]-c[x])
    return dict(v=int(y),u=float(u),chroma_before=float(np.median(c[x-8:x-1])),chroma_after=float(np.median(c[x+3:x+11])))
if __name__=='__main__':
    im=read(Path(sys.argv[1]));pts=[measure(im,y)for y in TRAIN];assert all(pts)
    H=homography(B_CORNERS,A_CORNERS)
    out=dict(district_sha256=DISTRICT,district_working_size=[1490,1000],district_local_crop=[85,140,475,592],district_local_size=[639,740],
             district_anchors=B_CORNERS,street_anchors=A_CORNERS,district_to_street_gable_only=H.tolist(),training=pts,
             manual_left_curve=[[26,304],[55,287],[87,263],[116,228],[136,188],[153,145],[169,98],[177,65]],
             right_terminal_limits=[[396,78],[399,96],[556,355],[572,371]],
             upper_arch=[[149,263],[150,224],[155,201],[165,178],[182,155],[205,135],[229,121],[255,111],[279,107],[304,109],
                         [332,117],[358,130],[381,147],[402,171],[418,195],[430,221],[438,247],[439,274]],
             limitations='只在绿色山墙平面内用四个边界点对应两幅照片。瓦面、凸阳台和窗后侧各有自己的进深，单独按可见界面重建。')
    (m/'green-gable-profile.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print([(r['v'],round(r['u'],1))for r in pts])
