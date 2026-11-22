"""Draw the warehouse window survey from material triangles in a checked GLB."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact'))
from glb_triangles import load_triangles
from check_west_return_windows import gable_coordinates

PAINT={
    'Guanger | blue grey window glass':'#8ca0ae','Guanger | pale reflective window glass':'#a6afa9',
    'Guanger | lower shop glass':'#8e9b9a','Guanger | painted steel sash':'#303e42',
    'Guanger | fixed dark steel':'#253136'
}
SAMPLES=[
 ('W1-F4','西翼四层宽窗','六列五层，窗中偏上的粗横梃分隔上下窗扇。'),
 ('W1-F2','西翼二层宽窗','上四层各十光，下层用两根竖梃分成三光。'),
 ('Cc-F4','中央四层窄窗','三列四层。三樘钢窗之间分别设石中梃。'),
 ('Cc-F2','中央二层窄窗','四列四层，下部水平粗梃低于窗框四分之一。'),
 ('E1-F1-w','底层侧光','窄侧光沿高分三段，与中间双扇以石柱分隔。'),
 ('E1-F1-m','底层双扇','双扇净宽由首层平面复核，两侧另设窄亮窗。'),
]
def font(size,bold=False):
    return ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-'+('Bold' if bold else 'Regular')+'.ttc',size,index=2)
def draw_model(tri,ids,labels,box,size):
    left,base,right,top=box
    w,h=size;scale=min(w/(right-left),h/(top-base))
    final=Image.new('RGB',(w*2,h*2),'#f4f2ec')
    draw=ImageDraw.Draw(final)
    def coords(a):
        return [((w-scale*(right-left)) + 2*scale*(x-left),
                 (h-scale*(top-base)) + 2*scale*(top-z)) for x,z in a[:,[0,2]]]
    lo,hi=tri.min(1),tri.max(1)
    select=(hi[:,0]>=left)&(lo[:,0]<=right)&(hi[:,2]>=base)&(lo[:,2]<=top)
    cross=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
    select&=(cross[:,1]<-1e-12)
    for material,col in PAINT.items():
        for face in tri[select & (ids==labels.index(material))]:draw.polygon(coords(face),fill=col)
    return final.resize(size,Image.Resampling.LANCZOS)
def make(model,layout,report,output):
    data=json.loads(layout.read_bytes());records={o['key']:o for o in data['openings']}
    q=json.loads(report.read_bytes());tri,ids,labels,asset=load_triangles(model)
    test=next(d for d in q['meshes'] if d['asset']['sha256']==asset['sha256'])
    used=np.isin(ids,[labels.index(p) for p in PAINT]);tri,ids=tri[used],ids[used]
    gable=gable_coordinates(tri,data)
    west=(gable[:,:,1].min(1)>.12)&(gable[:,:,1].max(1)<.23)&(gable[:,:,2].min(1)>14.3)
    wtri,wids=gable[west],ids[west]
    street=tri[:,:,0].max(1)>min(o['x0'] for o in records.values())-.012
    tri,ids=tri[street],ids[street]
    sheet=Image.new('RGB',(1500,1440),'#f4f2ec');draw=ImageDraw.Draw(sheet)
    def txt(x,y,msg,n=20,fg='#253136',bold=False):draw.text((x,y),msg,font=font(n,bold),fill=fg)
    txt(50,22,'交通银行仓库的临河钢窗与西山墙小窗',40,bold=True)
    txt(52,82,'光复路195号  ·  修缮后实物、标准层及首层图核定  ·  从西向东',22,'#4c595a')
    x0=min(pt[0] for pt in data['outer_ends_xy'])-.70
    x1=max(pt[0] for pt in data['outer_ends_xy'])+.70
    top=max(o['z1'] for o in records.values())+.36
    front=draw_model(tri,ids,labels,(x0,0,x1,top),(1400,342))
    sheet.paste(front,(50,122))
    s=min(1400/(x1-x0),342/top)
    for key in ('W5','W4','W3','W2','W1','Cc','E1','E2','E3','E4','E5'):
        o=records[key+'-F4'];x=(o['x0']+o['x1'])*.5
        xp=50+(1400-s*(x1-x0))/2+s*(x-x0)
        draw.text((xp,465),'中央' if key=='Cc' else key,font=font(17),fill='#516062',anchor='ma')
    txt(51,508,'六类窗格',26,bold=True)
    txt(227,516,'窗格取自已导出的三维网格，局部按各自尺寸等比放大。',17,'#506062')
    for i,(key,title,note)in enumerate(SAMPLES):
        column=i%3;row=i//3;x=52+475*column;y=561+248*row
        o=records[key];l,r,b,t=[o[v]for v in ('x0','x1','z0','z1')]
        crop=(l-.012,b-.012,r+.012,t+.012)
        sample=draw_model(tri,ids,labels,crop,(435,152))
        sheet.paste(sample,(x,y))
        txt(x,y+155,title,21,bold=True)
        txt(x+221,y+161,f'{r-l:.2f} × {t-b:.2f} m',17,'#506062')
        txt(x,y+194,note,16)
    txt(52,1067,f"69处净洞  ·  实测射线 {test['matched']}/{test['rays']} 命中预定窗材质和深度  ·  参考原图独立量读六处窗格内部横梃与竖杆",20)
    txt(52,1124,'西山墙临街段',26,bold=True)
    txt(260,1133,'从乌镇路桥望东，左侧为向后进深的横窗，右侧为临街的一对窄窗。',17,'#506062')
    return_schedule=json.loads((HERE/'west-return-windows.json').read_text())
    length=np.linalg.norm(np.diff(np.asarray(data['west_return']),axis=0)[0])
    west_front=draw_model(wtri,wids,labels,(0.,14.18,length,16.16),(800,168))
    sheet.paste(west_front,(50,1174))
    txt(905,1199,'两扇窄窗各有两道横梃。',21,bold=True)
    txt(905,1244,'横窗远侧窗边离街角10.33米。',19)
    txt(905,1286,'2026年实照与2020年乌镇路桥观察交核。',17,'#506062')
    txt(52,1370,'测量依据　设计院首层、标准层及完工斜照，2026年官方河岸立面照片、2020年桥上全景。图面由项目原创网格生成。',17,'#506062')
    output.mkdir(exist_ok=True,parents=True);p=output/'warehouse-window-elevation.jpg'
    sheet.save(p,quality=92,optimize=True,subsampling=0)
    meta=dict(title='交通银行仓库的临河钢窗与西山墙小窗',image=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
      model_sha256=asset['sha256'],layout_sha256=hashlib.sha256(layout.read_bytes()).hexdigest(),windows=72,south_windows=69,west_windows=return_schedule['openings'],
      study='Orthographic elevation of the actual exported window triangles. Each aperture detail is enlarged without changing its aspect ratio. Opaque surrounding masonry is omitted to show the grid.',
      source_records=['southern-window-image-observations.json','south-window-plan-layout.json','west-return-windows.json'],
      details=[dict(id=k,title=t,description=n) for k,t,n in SAMPLES],rights='Original drawing generated from the project geometry, MIT. Third-party photographs are referenced by their measurement registers.')
    (output/'warehouse-window-elevation.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
    print(meta['sha256'])
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('model',type=Path);ap.add_argument('report',type=Path);ap.add_argument('output',type=Path)
    a=ap.parse_args();make(a.model,HERE/'riverfront-layout.json',a.report,a.output)
