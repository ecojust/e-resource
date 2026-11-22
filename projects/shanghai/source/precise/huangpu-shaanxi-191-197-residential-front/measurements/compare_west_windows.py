"""Render the two real window assemblies through WQL's 2018 camera and compare."""
import argparse
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageOps
from check_west_windows import SerialScene
from glb_triangles import material_appearance
from west_photo_plane import matrix

def font(s):
    return ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',s,index=2)
def comparison(model,photo,output):
    scene=SerialScene(model);p=matrix();colors=material_appearance(model)['materials']
    tri=scene.tri;screen=tri@p[:,:3].T+p[:,3]
    uv=screen[:,:,:2]/screen[:,:,2,None]
    normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
    normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-12)
    light=.84+.43*np.maximum(0,normal@np.array([-.32,-.52,.77]))
    base=np.array([colors[m]['baseColorFactor'][:3] for m in scene.materials])[scene.mi]*light[:,None]
    rgb=255*np.where(base<=.0031308,12.92*base,1.055*base**(1/2.4)-.055)
    pic=Image.open(photo).convert('RGB');grey=Image.blend(Image.new('RGB',pic.size,'#f4f0e4'),ImageOps.grayscale(pic).convert('RGB'),.20)
    draw=ImageDraw.Draw(grey)
    eye=-np.linalg.solve(p[:,:3],p[:,3]);front=np.sum(normal*(eye-tri.mean(1)),axis=1)>0
    for i in np.argsort(screen[:,:,2].mean(1))[::-1]:
        if front[i] and min(screen[i,:,2])>0:draw.polygon([tuple(p) for p in uv[i]],fill=tuple(np.clip(rgb[i],0,255).astype('u1')))
    page=Image.new('RGB',(980,865),'#f5f3ed');d=ImageDraw.Draw(page)
    d.text((30,16),'陕西南路195号住宅 · 临街二层窗',font=font(39),fill='#213332')
    d.text((32,80),'2018年6月10日　从陕西南路朝东摄',font=font(21),fill='#384c48')
    bounds=[(1101,926,1565,1275),(1950,931,2380,1280)]
    for col,rect in enumerate(bounds):
        x=32+col*477
        for row,img in enumerate((pic,grey)):
            target=img.crop(rect).resize((int((rect[2]-rect[0])*.89),int((rect[3]-rect[1])*.89)),Image.Resampling.LANCZOS)
            page.paste(target,(x,151+row*345))
        d.text((x,111),['北组','南组'][col]+'　原照局部',font=font(22),fill='#31433f')
        d.text((x,459),'实物近景网格 · 同机位',font=font(21),fill='#31433f')
    d.line((32,818,947,818),fill='#aeb4a5')
    d.text((32,824),'原照 WQL《陕西南路195号》，2018。原照裁切及本对照图采用 CC BY-SA 4.0。',font=font(19),fill='#384b43')
    page.save(output,quality=91,optimize=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('model',type=Path);p.add_argument('source_photo',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();comparison(a.model,a.source_photo,a.output)
