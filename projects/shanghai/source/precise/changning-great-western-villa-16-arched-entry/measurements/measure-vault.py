"""Locate the light red face to shaded brick soffit transition and its radial mortar joints."""
from pathlib import Path
import argparse,json,hashlib,sys
import numpy as np
from scipy.ndimage import gaussian_filter1d,map_coordinates
from scipy.optimize import least_squares
from scipy.signal import find_peaks
from PIL import Image
HERE=Path(__file__).absolute().parent;sys.path.insert(0,str(HERE.parent/'source'))
from registration import C,projected,wall
Y=C['outer_front_y_m'];TRAIN=[149,173,188,213,232,246,252,263,273,291,312,336,354,374,397,417,438,457,478,498,518,536,557,579,589,596,610]
def source(p):
    assert hashlib.sha256(p.read_bytes()).hexdigest()==C['photo_sha256']
    with Image.open(p)as im:return np.asarray(im.resize((800,600),Image.Resampling.LANCZOS).convert('RGB'),float)
def edge(im,x):
    # The foreground face is lighter than the shadowed vault beneath.
    # The near edge is interrupted by two silver risers and a white service pipe.
    # Mask them in the photograph before any comparison with the exported model.
    if any(a<=x<=b for a,b in [(155,209),(220,231),(549,576)]):return None
    chart=np.asarray([[149,225],[173,191],[195,170],[220,150],[249,131],[278,117],[304,108],
                      [332,104],[358,101],[380,100],[402,102],[426,105],[449,111],[471,120],
                      [495,128],[518,141],[541,158],[561,177],[582,199],[600,225],[611,245]])
    expected=np.interp(x,chart[:,0],chart[:,1])
    lo,hi=int(expected-7),int(expected+8)
    line=np.median(im[:,x-1:x+2,:],axis=1)@[.24,.58,.18]
    filt=gaussian_filter1d(line,1.12)
    score=filt[np.arange(lo,hi)-4]-filt[np.arange(lo,hi)+4]
    j=int(np.argmax(score));y=lo+j
    if j in (0,len(score)-1) or score[j]<19:return None
    if np.median(line[y-7:y-3])-np.median(line[y+4:y+8])<20:return None
    before=im[y-7:y-3,x-1:x+2].mean(axis=(0,1));after=im[y+4:y+8,x-1:x+2].mean(axis=(0,1))
    if min(before[0]-before[1],after[0]-after[1])<13 or before[0]-after[0]<22:return None
    cen=y+.5*(score[j-1]-score[j+1])/(score[j-1]-2*score[j]+score[j+1]) if score[j-1]-2*score[j]+score[j+1]<-.005 else y
    return dict(x=x,v=float(cen),contrast=float(score[j]))
def arc(u,t):
    cx,cz,rx,rz,slant=u
    return np.stack([cx+rx*np.cos(t),cz+rz*np.sin(t)+slant*np.cos(t)],axis=-1)
def fit(pts):
    xz=wall([[p['x'],p['v']]for p in pts],Y);ends=wall([[126,298],[631,327]],Y)
    def residual(v):
        cx,cz,rx,rz,slant=v;dx=(xz[:,0]-cx)/rx;dy=(xz[:,1]-cz-slant*dx)/rz
        return np.r_[(dx*dx+dy*dy-1)*100.,(arc(v,np.array([np.pi,0]))-ends).ravel()*85]
    return least_squares(residual,[-.018,-.063,.878,.786,-.023],loss='soft_l1').x
def joints(im,u):
    t=np.linspace(.105,np.pi-.105,1700);radii=[.074,.087,.098,.112,.126]
    sample=[]
    for depth in radii:
        v=np.array(u);v[2:4]+=depth;xz=arc(v,t);uv=projected(np.c_[xz[:,0],np.full(len(t),Y),xz[:,1]])
        sample.append(np.array([map_coordinates(im[:,:,j],uv.T[::-1],order=1)for j in range(3)]))
    # Pale radial mortar has both a luminance peak and less redness than the adjacent fired clay.
    a=np.array(sample);ch=.55*a[:,1]+.45*a[:,2]-.27*(a[:,0]-a[:,2]);val=np.median(ch,axis=0);score=gaussian_filter1d(val,1.25)-gaussian_filter1d(val,9)
    peaks,_=find_peaks(score,prominence=9.5,distance=13)
    result=[dict(degrees=float(np.degrees(t[i])),contrast=float(score[i])) for i in peaks if score[i]>5]
    return result
if __name__=='__main__':
    args=argparse.ArgumentParser();args.add_argument('original',type=Path);arg=args.parse_args()
    im=source(arg.original);pts=[p for x in TRAIN if (p:=edge(im,x))]
    u=fit(pts);joint=joints(im,u)
    out=dict(photo_sha256=C['photo_sha256'],image_size=[800,600],outer_front_y_m=Y,training=pts,conic_parameters=u.tolist(),radial_mortar_observations=joint,
             specified_outer_spring_uv=[[126,298],[631,327]],crown_uv=projected([[u[0],Y,u[1]+u[3]]])[0].tolist(),
             criterion='从街面亮红砖到拱腹深红砖的亮度落差；管线、表箱或檐边遮挡处留空。角度由右侧起，沿拱顶至左侧。')
    assert len(pts)>=16 and len(joint)>=18
    (HERE/'vault-profile.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(len(pts),u.round(4),[(round(j['degrees'],1),round(j['contrast']))for j in joint])
