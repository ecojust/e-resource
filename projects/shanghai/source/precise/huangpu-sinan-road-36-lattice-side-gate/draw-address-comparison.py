"""Compare a rectified 2018 address plaque with projected faces of the delivered GLB."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

MATERIALS = ('Rolled enamel rim','Deep green enamel','Light address paint','Weathered paint highlights')

def plaque_projection(project, source, mesh, corners, homography):
    sys.path.insert(0,str(source))
    from photo_plane import H,D,CROP_SCALE,CROP_ORIGIN
    tools = runpy.run_path(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py')
    triangles, identifiers, names, _ = tools['load_triangles'](mesh)
    appearance = tools['material_appearance'](mesh)['materials']
    colors = {}
    for name in MATERIALS:
        linear = np.asarray(appearance[name]['baseColorFactor'][:3])
        srgb = np.where(linear<.0031308,12.92*linear,1.055*linear**(1/2.4)-.055)
        colors[name] = tuple(np.rint(255*srgb).astype(int))
    selected = np.isin(np.asarray(names)[identifiers],MATERIALS)
    tris, labels = triangles[selected], np.asarray(names)[identifiers[selected]]
    # The four thin material layers are parallel to the plaque. Paint the furthest
    # first, preserving the projected sides as well as the front faces.
    order = np.argsort(-np.mean(tris[:,:,1],axis=1),kind='stable')
    p = tris.reshape(-1,3)
    q = np.column_stack((p[:,0],p[:,2],np.ones(len(p))))@H.T + p[:,1,None]*D
    upright = q[:,:2]/q[:,2,None]*CROP_SCALE + CROP_ORIGIN
    rectification = homography(corners,[(0,0),(400,0),(400,326),(0,326)])
    q = np.column_stack((upright,np.ones(len(p))))@rectification.T
    screen = (2*q[:,:2]/q[:,2,None]).reshape(-1,3,2)
    picture = Image.new('RGB',(800,652),'#e9e9df')
    draw = ImageDraw.Draw(picture)
    for i in order:
        draw.polygon([tuple(p)for p in screen[i]],fill=colors[labels[i]])
    return picture.resize((400,326),Image.Resampling.LANCZOS)

def make_sheet(photo, rectified, mesh_view):
    sheet = Image.new('RGB',(1240,800),'#f7f5ed')
    draw = ImageDraw.Draw(sheet)
    def caption(px,py,label,size,bold=False):
        family = 'Bold' if bold else 'Regular'
        font = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-'+family+'.ttc',size,index=2)
        draw.text((px,py),label,font=font,fill='#213b35')
    caption(30,12,'思南路 36 号的边门门牌',38,True)
    caption(32,73,'上海 · 黄浦　｜　2018 年 7 月 30 日街面原照与三维模型对读',20)
    draw.line((32,115,1208,115),fill='#91a99a',width=1)
    upright = ImageOps.exif_transpose(Image.open(photo))
    views = [(32,'门牌在右侧门柱的位置',upright.crop((1770,2500,2970,3700))),
             (442,'原照校正到牌面正视角',rectified),(840,'三维模型的牌面与字漆',mesh_view)]
    for x,title,picture in views:
        caption(x,135,title,20,True)
        pic = ImageOps.contain(picture,(366,314),Image.Resampling.LANCZOS)
        sheet.paste(pic,(x+(366-pic.width)//2,183+(314-pic.height)//2))
    draw.line((32,514,1208,514),fill='#b2c2b5',width=1)
    caption(32,530,'“边门”小字放大',20,True)
    for x,title,pic in [(33,'原照',rectified),(267,'模型',mesh_view)]:
        crop=pic.crop((310,185,381,239)).resize((187,142),Image.Resampling.LANCZOS)
        sheet.paste(crop,(x,576));caption(x,720,title,16)
    caption(530,530,'路名与数字的笔画来自照片',20,True)
    caption(530,582,'门牌上有门号“36”、路名“思南路”，右侧另印“边门”。',19)
    caption(530,628,'三档模型均核对了 43 处浅色字漆和 9 处绿色底釉。',19)
    caption(530,675,'左下两图为同一处字样，按相同比例放大。',17)
    draw.line((32,755,1208,755),fill='#91a99a',width=1)
    caption(33,762,'照片由 Antigng 拍摄，取自 Wikimedia Commons《思南路36号住宅》，已裁切并校正透视。图板采用 CC BY-SA 4.0。',15)
    return sheet

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['project','source','photo','mesh','review','output']:
        parser.add_argument('--'+name,required=True,type=Path)
    args = parser.parse_args()
    methods = runpy.run_path(args.source.parent/'measurements/trace-address.py')
    report = json.loads(args.review.read_bytes())
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest(args.photo)==report['source_photo_sha256']
    assert digest(args.mesh)==report['roles']['raw']['mesh_sha256']
    result,corners,_ = methods['run'](args.photo)
    original = Image.fromarray(result.round().astype('uint8'))
    model_view = plaque_projection(args.project,args.source,args.mesh,corners,methods['homography'])
    make_sheet(args.photo,original,model_view).save(args.output,quality=90,optimize=True,subsampling=0)

if __name__=='__main__':
    main()
