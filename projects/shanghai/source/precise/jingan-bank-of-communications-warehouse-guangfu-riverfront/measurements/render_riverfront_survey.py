"""Render the released riverfront and draw its measured plan on an original public plate."""
import argparse,ctypes,hashlib,json,os,subprocess,sys,tempfile
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent
RASTER=HERE.parents[1]/'jingan-jiaozhou-450-garden-residence/measurements'
sys.path.insert(0,str(RASTER))
from photo_glb_raster import raster

def perspective(eye,target,w,h,focal):
    eye=np.array(eye,float);forward=np.array(target,float)-eye;forward/=np.linalg.norm(forward)
    east=np.cross(forward,[0.,0.,1.]);east/=np.linalg.norm(east);up=np.cross(east,forward)
    rotation=np.stack([east,up,forward])
    return np.array([[focal,0,w/2],[0,-focal,h/2],[0,0,1.]])@np.c_[rotation,-rotation@eye]

def load_raster(tmp):
    library=Path(tmp)/'river-render.so';args=[]
    if hasattr(os,'memfd_create'):
        fd=os.memfd_create('river-model-render',0);library=Path(f'/proc/self/fd/{fd}');args=[fd]
    try:
        subprocess.run(['cc','-O2','-shared','-fPIC',str(RASTER/'photo_glb_raster.c'),'-lm','-o',str(library)],check=True,pass_fds=tuple(args))
        lib=ctypes.CDLL(str(library));lib.paint.restype=lib.shadow_depth.restype=None;return lib
    finally:
        for fd in args:os.close(fd)

def draw(mesh,out):
    layout=json.loads((HERE/'riverfront-layout.json').read_bytes());survey=layout['survey']
    roof=json.loads((HERE/'roof-terrace-survey.json').read_bytes());aerial=json.loads((HERE/'south-parapet-aerial-measurements.json').read_bytes());heights=json.loads((HERE/'four-station-front-height.json').read_bytes())
    board=Image.new('RGB',(1440,1040),'#f4f1e9');pen=ImageDraw.Draw(board)
    def lbl(x,y,text,size,bold=False,fill='#283d41'):
        f='/usr/share/fonts/opentype/noto/NotoSansCJK-'+('Bold'if bold else'Regular')+'.ttc'
        pen.text((x,y),text,fill=fill,font=ImageFont.truetype(f,size,index=2))
    lbl(42,17,'原交通银行仓库',41,True);lbl(44,86,'光复路 195 号　上海市第五批优秀历史建筑 5H003',22)
    lbl(1060,56,'苏州河北岸 · 静安',25);pen.line([(42,133),(1396,133)],fill='#819992',width=2)
    sun=np.array([-.49,-.76,.56],dtype=np.float32);sun/=np.linalg.norm(sun)
    sun_angles=[float(np.degrees(np.arctan2(sun[0],sun[1]))%360),float(np.degrees(np.arcsin(sun[2])))]
    shots=[]
    with tempfile.TemporaryDirectory() as tmp:
        lib=load_raster(tmp)
        for title,e,t,ww,hh,focal,x,y in [
            ('Riverfront and east gable',[26,-100,30],[0,1,10.8],1354,475,1730,43,147),
            ('Central entrance and ground route',[-2.45,-22,4.0],[0,2.2,3.15],638,249,688,760,702)]:
            cam=perspective(e,t,ww,hh,focal)
            hi,stats=raster(mesh,lib,ww*2,cam,[0,0,ww,hh],sun,sun_angles)
            board.paste(hi.resize((ww,hh),Image.Resampling.LANCZOS),(x,y))
            shots.append(dict(view=title,projection=cam.tolist(),crop=[0,0,ww,hh],stats=stats))
    lbl(44,629,'临河十个宽开间与中央三列钢窗。现状招牌和修缮后的露台取自完工资料。',19)
    pen.line([(43,682),(1397,682)],fill='#aab4aa',width=1)
    lbl(46,697,'南檐曲线',23,True)
    def screen(xy):
        q=np.asarray(xy);return tuple(np.rint([356+9.75*q[0],935-9.75*q[1]]).astype(int))
    model=np.array([[p['x'],p['y']]for p in survey['outer_plan_stations']])
    A=np.array(survey['plan_pixel_to_xy'])
    back=[A@[*p,1] for p in roof['roof_plan_edges']['southern_paved_field_back_line']]
    pen.polygon([screen(p)for p in [*model,back[1],back[0]]],fill='#e0ded4')
    # Align the independently traced image-space roof endpoints to the same metrical chord.
    observed=np.array(aerial['xy_signed_per_chord']);v=model[-1]-model[0];v/=np.linalg.norm(v);normal=np.array([-v[1],v[0]])
    q=(observed-observed[0])@np.stack([v,normal])+model[0]
    pen.line([screen(x)for x in model],fill='#315a58',width=5)
    for p in q[::3]:
        u,v=screen(p);pen.ellipse((u-2,v-2,u+2,v+2),fill='#b1693d')
    for p in (model[0],model[-1]):
        u,v=screen(p);pen.line((u,v+5,u,960),fill='#9c9688',width=1)
    pen.line((67,958,644,958),fill='#757469',width=2)
    lbl(221,963,'端点直距约 59.4 米',17)
    lbl(65,808,'屋面平面',16,True);pen.line((67,842,103,842),fill='#315a58',width=4);lbl(112,830,'设计方屋面南边',15)
    for u in (69,83,97):pen.ellipse((u-2,870,u+2,874),fill='#b1693d')
    lbl(112,858,'航片独立读点',15)
    lbl(760,959,'门额「光二倉庫」与贯通车道，保留前三对柱。',18)
    lbl(46,1002,'原模型视图与数值制图　·　依据修缮团队公布平面、四处 2019 年街景及卫星影像。',14,fill='#5c6969')
    out.parent.mkdir(parents=True,exist_ok=True);board.save(out,quality=91,subsampling=0)
    out.with_suffix('.json').write_text(json.dumps(dict(model_sha256=hashlib.sha256(mesh.read_bytes()).hexdigest(),board_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),
        street_crest=heights['estimates']['middle_parapet_crest_above_threshold_m'],roof_check=roof['aerial_registration']['median_absolute_vertical_residual_m'],renders=shots),ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('model',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();draw(args.model,args.output)
