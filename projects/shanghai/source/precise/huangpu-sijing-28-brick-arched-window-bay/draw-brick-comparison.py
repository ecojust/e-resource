"""Project the downloaded east-bay brick faces over Antigng's 2017 photograph."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import runpy

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
from shapely.geometry import Polygon
from shapely.ops import unary_union

FACES = {'Red radial arch brick':-.022,'Blue-grey radial arch brick':-.022,
         'Cut red rim brick':-.036,'Pale keystone and skewbacks':-.060}

def read_fronts(project, source, mesh, sha):
    sys.path.insert(0,str(source))
    from photo_plane import pixel
    helper = runpy.run_path(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py')
    triangles, materials, names, identity = helper['load_triangles'](mesh)
    if identity['sha256'] != sha:
        raise ValueError('The file differs from the reviewed raw GLB')
    tags=np.asarray(names)[materials]
    outlines=[]
    for mat,y in FACES.items():
        faces = triangles[(tags==mat)&(np.max(np.abs(triangles[:,:,1]-y),axis=1)<.0001)]
        if not len(faces): raise ValueError('Missing arch face '+mat)
        # Adjacent source triangles share edges. Union first, leaving visible
        # brick and mortar boundaries without triangulation diagonals.
        quads=unary_union([Polygon(t[:,[0,2]])for t in faces])
        rings=quads.geoms if quads.geom_type == 'MultiPolygon' else [quads]
        for ring in rings:
            if ring.area<.00002:continue
            outlines.append((mat,[pixel((x,y,z)).tolist() for x,z in ring.exterior.coords]))
    return outlines

def make_photo_sheet(photo, profiles, report, out):
    im=Image.open(photo).convert('RGB')
    sheet=Image.new('RGB',(1280,886),'#f8f4eb')
    draw=ImageDraw.Draw(sheet)
    def label(x,y,value,size,bold=False):
        wt='Bold' if bold else 'Regular'
        font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-'+wt+'.ttc',size,index=2)
        draw.text((x,y),value,font=font,fill='#29332e')
    label(28,12,'泗泾路 28 号东端的两道砖券',36,True)
    label(30,70,'上海 · 黄浦　｜　2017 年 8 月 31 日沿街实拍与三维模型',20)
    draw.line((30,111,1249,111),fill='#9cafa5')
    label(31,125,'原照',21,True)
    label(652,125,'叠加三维砖边与中央券石的投影',21,True)
    def panels(y,title,box):
        label(31,y,title,17)
        scale=592/(box[2]-box[0])
        crop=im.crop(box).resize((592,round(scale*(box[3]-box[1]))),Image.Resampling.LANCZOS)
        sheet.paste(crop,(30,y+37));sheet.paste(crop,(652,y+37))
        overlay=ImageDraw.Draw(sheet)
        for mat,points in profiles:
            if not all(box[0]-2<=x<=box[2]+2 and box[1]-2<=v<=box[3]+2 for x,v in points):continue
            xy=[(652+(x-box[0])*scale,y+37+(v-box[1])*scale)for x,v in points]
            overlay.line(xy,fill='#ffda57'if mat.startswith('Pale')else '#8effe1',width=2 if mat.startswith('Pale')else 1)
    panels(174,'上层 · 浅色券石两边可辨交替排列的红砖和青砖',(2800,155,4140,679))
    panels(466,'下层 · 外圈平砖、径向砌砖和灰缝',(2695,1242,4280,1850))
    draw.line((30,770,1249,770),fill='#9cafa5')
    label(31,785,'青线为砖块与灰缝的三维边界，黄线为中央浅色券石。可见两层券洞的分砖与切砖略有差别。',17)
    label(31,821,'原始、网页近景和远景三档模型分别核过 '+str(report['roles']['raw']['count'])+' 个可读砖面与券石采样点。',16)
    label(31,850,'照片由 Antigng 拍摄，取自 Wikimedia Commons《泗泾路28号》，已裁切并加注投影。图板采用 CC BY-SA 4.0。',15)
    sheet.save(out,quality=91,subsampling=0,optimize=True)
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for field in ['project','source','mesh','photo','review','output']:
        ap.add_argument('--'+field,type=Path,required=True)
    a=ap.parse_args();report=json.loads(a.review.read_bytes())
    if hashlib.sha256(a.photo.read_bytes()).hexdigest()!=report['photo_sha256']:
        raise ValueError('Unexpected photograph')
    fronts=read_fronts(a.project,a.source,a.mesh,report['roles']['raw']['mesh_sha256'])
    make_photo_sheet(a.photo,fronts,report,a.output)
if __name__=='__main__':
    main()
