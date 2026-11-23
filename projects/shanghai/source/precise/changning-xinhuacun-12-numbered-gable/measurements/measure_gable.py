"""Rectify the material boundaries and trace the two pale applied numerals on the numbered gable."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image
from shapely.geometry import box
from shapely.ops import unary_union

REFERENCE=[[451,233],[701,222],[703,445],[449,455]]
CONDITIONAL=[[0,8.17],[7.40,8.17],[7.40,1.58],[0,1.58]]
def solve(points,meters):
    A=[]
    for (u,v),(x,z) in zip(points,meters):
        A.extend([[u,v,1,0,0,0,-u*x,-v*x,-x],[0,0,0,u,v,1,-u*z,-v*z,-z]])
    _,_,V=np.linalg.svd(A)
    mat=V[-1].reshape(3,3)
    return mat/mat[2,2]
def convert(mat,p):
    q=mat@[*p,1.]
    return np.round(q[:2]/q[2],6).tolist()
def numerals(im,mat):
    intensity=np.asarray(im.convert('L'));out=[]
    for number,(left,top,right,bottom) in [('1',(522,308,535,328)),('2',(535,307,550,328))]:
        mask=intensity[top:bottom,left:right]>137
        patches=[]
        for v,bits in enumerate(mask):
            edges=np.flatnonzero(np.diff(np.r_[False,bits,False]))
            patches.extend(box(left+a,top+v,left+b,top+v+1)for a,b in edges.reshape(-1,2))
        glyph=unary_union(patches);rings=[]
        for piece in getattr(glyph,'geoms',[glyph]):
            if piece.area<2.8:continue
            curve=piece.simplify(.29,preserve_topology=True)
            rings.append([[convert(mat,p)for p in list(r.coords)[:-1]]for r in [curve.exterior,*curve.interiors]])
        out.append(dict(number=number,rings=rings))
    return out
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('photo',type=Path);p.add_argument('out',type=Path);a=p.parse_args()
    mat=solve(REFERENCE,CONDITIONAL)
    with Image.open(a.photo)as im:
        assert im.size==(780,520)
        glyphs=numerals(im,mat)
    record=dict(original_sha256=hashlib.sha256(a.photo.read_bytes()).hexdigest(),image_pixels=[780,520],face_controls=REFERENCE,conditional_control_xz_metres=CONDITIONAL,image_to_xz=mat.tolist(),digit_outlines=glyphs,scale_basis='Initial conditional gable eaves width 7.4 m. The 6.59 m interval covers two floor transitions. Absolute widths and outside chimney depths remain to be checked.')
    a.out.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n');print([(x['number'],len(x['rings']))for x in glyphs])
