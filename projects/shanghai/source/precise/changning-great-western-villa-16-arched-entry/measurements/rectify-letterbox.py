"""Rectify WQL's licensed relief-and-mailbox photograph. Record real medallion and numeral profiles."""
from pathlib import Path
import sys,hashlib,json,argparse
import numpy as np
from PIL import Image
from scipy.ndimage import label,gaussian_filter,binary_closing
HERE=Path(__file__).absolute().parent;SRC=HERE.parent/'source'
W,H=320,512
PLATE=[[73,34],[389,54],[344,489],[90,486]]
LABEL=[[136,418],[301,419],[296,450],[134,448]]
SHA='dd659672b9fb5873809f552a16e13d50682b3a3bcabb9b88921fa24d7855caec'
def matrix(src,dst):
    a=[];b=[]
    for (u,v),(x,y)in zip(src,dst):
        a.extend([[u,v,1,0,0,0,-x*u,-x*v],[0,0,0,u,v,1,-y*u,-y*v]]);b.extend([x,y])
    return np.r_[np.linalg.solve(a,b),1].reshape(3,3)
def rectified(im,corners,w,h):
    dst=np.asarray(corners)*[im.width/450,im.height/600]
    m=matrix([[0,0],[w,0],[w,h],[0,h]],dst)
    return im.transform((w,h),Image.Transform.PERSPECTIVE,m.ravel()[:8],Image.Resampling.BICUBIC)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('photo',type=Path);photo=ap.parse_args().photo
    assert hashlib.sha256(photo.read_bytes()).hexdigest()==SHA
    with Image.open(photo)as im:
        image=np.asarray(rectified(im,PLATE,W,H)).copy();label_image=rectified(im,LABEL,316,62)
    yy,xx=np.mgrid[:H,:W];u=xx/(W-1);v=yy/(H-1);r,g,b=np.moveaxis(image.astype(float),2,0)
    region=(u>.116)&(u<.579)&(v>.108)&(v<.404)
    maroon=region&(r>g+9)&(r>b+6)&(g<104)
    objs,n=label(binary_closing(maroon,iterations=2));a=np.bincount(objs.ravel());a[0]=0;blob=objs==a.argmax()
    ry,rx=np.where(blob);x0,x1=rx.min(),rx.max();y0,y1=ry.min(),ry.max()
    cx=(x0+x1)/2;cy=(y0+y1)/2;ra=(x1-x0+1)/2;rb=(y1-y0+1)/2
    disc=((xx-cx)/ra)**2+((yy-cy)/rb)**2
    digits=(disc<.865)&(r>106)&(g>86)&(g-b>19)&(r>b+33)
    objs,n=label(binary_closing(digits,iterations=1));s=np.bincount(objs.ravel());s[0]=0
    ids=np.argsort(s)[-2:];gold=np.isin(objs,ids)
    # The free-standing shelf hides the lower plate in the photograph. The model gives it its own solid.
    # Below the observed relief use local grey stone from the clean field above, with a soft transition.
    sample=image[185:236,144:169].reshape(-1,3);noise=np.random.default_rng(161453).standard_normal((H,W))
    grain=noise*.62+gaussian_filter(noise,1.6)*1.62
    substitute=np.clip(np.median(sample,axis=0)+grain[:,:,None]*np.std(sample,axis=0)*.68,0,255)
    blend=np.clip((v-.695)*12,0,1)
    cleaned=np.uint8(image*(1-blend[:,:,None])+substitute*blend[:,:,None])
    atlas=Image.new('RGB',(352,624),(108,113,109));atlas.paste(Image.fromarray(cleaned),(16,12));atlas.paste(label_image,(18,548))
    atlas.save(SRC/'letterbox-relief-atlas.png',optimize=True)
    Image.fromarray(np.uint8(gold)*255).save(SRC/'gilt-digits.png',optimize=True)
    data=dict(photo_sha256=SHA,closeup_working_size=[450,600],slate_corners=PLATE,mailbox_label_corners=LABEL,panel_rectified_size=[W,H],atlas_size=list(atlas.size),
        panel_rect=[16,12,336,524],label_rect=[18,548,334,610],medallion_center_uv=[cx/(W-1),cy/(H-1)],medallion_radii_uv=[ra/(W-1),rb/(H-1)],
        gilded_numeral_pixels=int(gold.sum()),numeral_components=[int(s[i])for i in ids],texture_sha256=hashlib.sha256((SRC/'letterbox-relief-atlas.png').read_bytes()).hexdigest(),
        license='CC BY-SA 4.0',author='WQL',adaptations='四角透视校正、真实铭牌裁切、下半遮挡区的灰石补面及图集排版。模型独立制作箱架前挡、螺帽和托盘。')
    assert min(s[ids])>90 and .21<data['medallion_center_uv'][0]<.48 and .16<data['medallion_center_uv'][1]<.4
    (HERE/'letterbox-relief.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');print(data['medallion_center_uv'],data['medallion_radii_uv'],data['numeral_components'])
