"""Recover white enamel letter outlines in the plate photograph (external input, not distributed)."""
import argparse, json, hashlib
from pathlib import Path
import numpy as np
from PIL import Image
from shapely.geometry import box, MultiPolygon
from shapely.ops import unary_union
from scipy.ndimage import label
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
CORNERS=[[92,79],[382,102],[414,312],[96,315]]
def trace(file):
    im=np.array(Image.open(file).convert('RGB')).astype(float);h,w=182,258
    # A true homography is determined by the four corners of the enamel substrate.
    sys=[];aim=[]
    for (x,y),(u,v)in zip([(0,0),(1,0),(1,1),(0,1)],CORNERS):
        sys.extend([[x,y,1,0,0,0,-u*x,-u*y],[0,0,0,x,y,1,-v*x,-v*y]]);aim.extend([u,v])
    H=np.r_[np.linalg.solve(sys,aim),1].reshape(3,3)
    yy,xx=np.mgrid[:h,:w];obj=np.stack([(xx+.5)/w,(yy+.5)/h,np.ones_like(xx)]);uv=np.einsum('ij,jkl->ikl',H,obj);u,v=np.round(uv[:2]/uv[2]).astype(int);r,g,b=im[v,u].transpose(2,0,1)
    # Bound the two actual rows so that border, coatings and screws are separate objects.
    mask=(r>153)&(g>154)&(b>141)&(r>g-38)&((((yy>17)&(yy<118))&((xx>52)&(xx<206)))|((yy>119)&(yy<163)&(xx>12)&(xx<247)))
    ids,n=label(mask);sizes=np.bincount(ids.ravel());mask &= sizes[ids]>=3
    cells=[]
    for j,row in enumerate(mask):
        edges=np.flatnonzero(np.diff(np.r_[False,row,False].astype(int)))
        cells.extend(box(l/w,1-(j+1)/h,r/w,1-j/h)for l,r in zip(edges[::2],edges[1::2]))
    geom=unary_union(cells).simplify(.0016,preserve_topology=True)
    def ring(r):return [[round(x,6),round(y,6)] for x,y in list(r.coords)[:-1]]
    return dict(source='41629625',source_sha256=sha(file),native_size=[im.shape[1],im.shape[0]],corners=CORNERS,
        text='20 / 愚园路一一一二弄',orientation='normalized plaque, origin at lower left',width_ratio=1.38,
        measured_extent='Outline and aspect approximate from one oblique close-up. Centimetres are a display convention.',rings=[dict(exterior=ring(g.exterior),holes=[ring(h)for h in g.interiors]) for g in geom.geoms])
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('photo',type=Path);p.add_argument('out',type=Path);a=p.parse_args();a.out.write_text(json.dumps(trace(a.photo),ensure_ascii=False,separators=(',',':'))+'\n')
