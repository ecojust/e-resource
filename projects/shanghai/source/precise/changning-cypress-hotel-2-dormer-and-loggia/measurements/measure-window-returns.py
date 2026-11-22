"""Locate the two second-storey openings in the district photograph of Cypress Hotel number 2."""
from pathlib import Path
import hashlib, json, os
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
from scipy.stats import theilslopes
p=Path(__file__).resolve().parent
photo=Path(os.environ.get('CYPRESS_LAWN_PHOTO',p.parent/'lawn-original.jpg'))
im=np.asarray(Image.open(photo).convert('RGB'),float)
chrom=gaussian_filter(im[:,:,0]-im[:,:,2],.75)
light=gaussian_filter(im@np.array([.30,.57,.13]),.78)
def line(q):
    q=np.asarray(q)
    slope,intercept,*_=theilslopes(q[:,1],q[:,0])
    fit=[slope,intercept]
    residual=q[:,1]-np.polyval(fit,q[:,0]);center=np.median(residual)
    keep=abs(residual-center)<max(.7,2.*np.median(abs(residual-center)))
    return np.polyfit(q[keep,0],q[keep,1],1)

def peak(sig,lo,hi):
    x=np.arange(lo,hi+1);v=sig[x];i=np.argmax(v);k=x[i]
    if i and i<len(x)-1:
        a,b,c=v[i-1:i+2];den=a-2*b+c
        if abs(den)>.01:return k+float(np.clip(.5*(a-c)/den,-.5,.5))
    return float(k)
samples=[]
for start,end,lo,hi in [(471,487,255,284),(498,515,253,282)]:
    xl=[];xr=[];yt=[];yb=[]
    for y in range(261,279):
        slope=np.gradient(chrom[y]);xl.append((y,peak(-slope,start-2,start+3)));xr.append((y,peak(slope,end-3,end+3)))
    for x in range(start+4,end-3):
        grad=np.gradient(light[:,x]);yt.append((x,peak(-grad,lo-2,lo+3)));yb.append((x,peak(grad,hi-2,hi+3)))
    left,right,top,bottom=map(line,[xl,xr,yt,yb])
    def cross(pair_x,pair_y):
        a,b=pair_x;c,d=pair_y;x=(a*d+b)/(1-a*c);return [x,c*x+d]
    samples.append(dict(corners=[cross(left,top),cross(right,top),cross(right,bottom),cross(left,bottom)],samples=dict(left=xl,right=xr,top=yt,bottom=yb)))
out=dict(source_sha256=hashlib.sha256(photo.read_bytes()).hexdigest(),source_pixels=[1028,686],record='4M044 / 龙柏饭店2号楼',windows=samples,method='采用两个二层洞口的红色墙面与暗框色差、框顶及窗台的明度梯度。阈值取样区和可见边缘点均保留。')
(p/'second-storey-openings.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print([np.round(s['corners'],2).tolist()for s in samples])
