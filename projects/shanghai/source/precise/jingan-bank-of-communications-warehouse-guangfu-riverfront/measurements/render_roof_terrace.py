"""Draw the south terrace from a released GLB and its registered, measured plan."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from render_riverfront_survey import load_raster, perspective, raster

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
from roof_terrace import terrace_layout, STEEL, PAVING, LENS

INK='#22383b'
GREY='#4e6564'
BASE='#f4f1e9'
GREEN='#3b746d'
WALL='#777769'


def font(size,bold=False):
    face='Bold' if bold else 'Regular'
    return ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-'+face+'.ttc',size,index=2)


def label(draw,xy,msg,size=20,fill=INK,bold=False,anchor='la'):
    draw.text(xy,msg,fill=fill,font=font(size,bold),anchor=anchor)


def board(title,subtitle,h):
    sheet=Image.new('RGB',(1460,h),BASE)
    d=ImageDraw.Draw(sheet)
    label(d,(42,18),title,40,bold=True)
    label(d,(43,86),subtitle,21,GREY)
    d.line((42,132,1418,132),fill='#90a49d',width=2)
    return sheet,d


def save(sheet,out):
    sheet.save(out,quality=92,subsampling=0,optimize=True)
    return {'file':out.name,'bytes':out.stat().st_size,'sha256':sha256(out.read_bytes()).hexdigest()}


def render(mesh,out):
    sheet,d=board('原交通银行仓库的南露台','光复路195号  ·  修缮后的铺装、沿河扶手和嵌地灯',1120)
    target1=[0,8,18.2];target2=[10,1,19.0];target3=[14.9,12.4,18.2]
    views=[
        ('南侧露台',[-28,-54,87],target1,1376,505,1715,42,144),
        ('扶手与托架',[60,30,45],target2,676,280,3230,42,735),
        ('七盏嵌地灯',[50,49,68],target3,676,280,2870,742,735)]
    sun=np.array([-.49,-.76,.56],np.float32);sun/=np.linalg.norm(sun)
    angles=[float(np.rad2deg(np.arctan2(sun[0],sun[1]))%360),float(np.rad2deg(np.arcsin(sun[2])))]
    shots=[]
    with tempfile.TemporaryDirectory() as tmp:
        lib=load_raster(tmp)
        for name,e,t,w,h,f,x,y in views:
            proj=perspective(e,t,w,h,f)
            photo,stats=raster(mesh,lib,w*2,proj,[0,0,w,h],sun,angles)
            sheet.paste(photo.resize((w,h),Image.Resampling.LANCZOS),(x,y))
            key={'南侧露台':PAVING,'扶手与托架':STEEL,'七盏嵌地灯':LENS}[name]
            assert stats['materials_visible_samples'].get(key,0)>100,(name,stats['materials_visible_samples'])
            shots.append({'name':name,'projective_camera_native_px':proj.tolist(),'output_view_rect':[x,y,w,h],'stats':stats})
    label(d,(42,659),'屋面南缘顺苏州河转弯。中央抬高的女儿墙将两侧扶手分开。',22)
    label(d,(43,691),'扶手内侧的石材铺地抵至设备房南界，绝对标高按建筑统一坐标取18.20米。',18,GREY)
    label(d,(42,1026),'沿女儿墙的金属扶手与折形托架',23,bold=True)
    label(d,(742,1026),'铺地内的方形灯框、圆形灯盘和中心灯点',23,bold=True)
    label(d,(42,1068),'相邻托架约0.94米，扶手顶较铺地高约0.95米。',18,GREY)
    label(d,(742,1068),'七盏灯的位置均由屋面完工照片上的灯心投影取得。',18,GREY)
    item=save(sheet,out/'south-terrace-model.jpg')
    return item,shots


def plan(out):
    field,inner,fit=terrace_layout({})
    survey=json.loads((HERE/'roof-terrace-survey.json').read_bytes())
    lines=survey['roof_plan_edges'];A=np.asarray(fit['plan_pixel_to_xy'])
    def project(xy):return (int(round(726+20*xy[0])),int(round(700-20*xy[1])))
    def uv(p):return project(A @ [*p,1.])
    sheet,d=board('沿河屋面的平面与定位','原交通银行仓库  ·  屋顶平面图、航空影像和修缮后照片的交叉测量',1105)
    d.polygon([project(v) for v in field.exterior.coords],fill='#c9ded8',outline=GREEN,width=3)
    edges=[uv(v)for v in lines['outer_south']]
    d.line(edges,fill=WALL,width=5)
    d.line([uv(v)for v in lines['inner_south']],fill=INK,width=3)
    for line in ['west_return_outer','east_return_outer']:
        # Only the south terrace is shown. Terminate the returns at its documented back line.
        a,b=[np.array(p,dtype=float)for p in lines[line][:2]]
        y=lines['southern_paved_field_back_line'][0][1];t=(y-a[1])/(b[1]-a[1])
        d.line([uv(a),uv(a+t*(b-a))],fill=WALL,width=5)
    d.line([uv(p)for p in lines['southern_paved_field_back_line']],fill=GREEN,width=3)
    for xy in fit['light_centres_xy']:
        x,y=project(xy)
        d.rectangle((x-8,y-8,x+8,y+8),fill='#586e70')
        d.ellipse((x-5,y-5,x+5,y+5),fill='#ede2ae',outline=INK,width=1)
    for index,anchor,msg,tip in [
        (0,project((15.6,12.6)),'七盏实见嵌地灯',(1110,245)),
        (1,uv(lines['southern_paved_field_back_line'][0]),'铺装北界',(232,252)),
        (2,edges[len(edges)//2],'沿河女儿墙与扶手',(625,783))]:
        d.line([anchor,tip],fill=GREY,width=2)
        label(d,(tip[0],tip[1]-15),msg,20,INK,True,'ms')
    label(d,(117,734),'西端',18,GREY)
    label(d,(1295,718),'东端',18,GREY)
    label(d,(53,172),'平面定位',25,bold=True)
    label(d,(1173,172),'苏州河在图下方',18,GREY)
    for k in range(2):
        x=1144+100*k
        d.rectangle((x,783,x+100,791),fill=GREY if k==0 else BASE,outline=GREY)
    label(d,(1140,804),'0',16,GREY);label(d,(1330,804),'10 m',16,GREY)
    d.line((42,862,1418,862),fill='#90a49d',width=2)
    label(d,(44,876),'南边界约59.64米',24,bold=True)
    label(d,(440,876),'铺装约899平方米',24,bold=True)
    label(d,(885,876),'平面复核',24,bold=True)
    label(d,(45,929),'测线沿南女儿墙弯折，图中以',19,GREY)
    label(d,(45,964),'墙内外两条边界区分实际厚度。',19,GREY)
    label(d,(441,929),'平面取南女儿墙内侧至设备房南界。',19,GREY)
    label(d,(441,964),'铺装排版与灯具构造为实物外观近似。',19,GREY)
    label(d,(885,929),'两端定标后，15个中间测点与航片',19,GREY)
    label(d,(885,964),'南檐的偏差中位数为0.21米。',19,GREY)
    label(d,(44,1040),'资料据华建集团历史建筑保护设计院公布的屋顶层平面图及完工影像。图面由模型和测点重新绘制。',18,GREY)
    return save(sheet,out/'south-terrace-plan.jpg')


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mesh',type=Path)
    ap.add_argument('output',type=Path)
    args=ap.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    image,shots=render(args.mesh,args.output)
    receipt={'model_sha256':sha256(args.mesh.read_bytes()).hexdigest(),'files':[image,plan(args.output)],'model_views':shots}
    (args.output/'renders.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
