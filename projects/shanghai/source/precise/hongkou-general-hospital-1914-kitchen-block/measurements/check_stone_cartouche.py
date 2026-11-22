"""Project the actual model into the two 2020 prints and three dated 2019 street stations."""
import argparse, hashlib, json, runpy, sys, tempfile
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact'))
sys.path.insert(0,str(HERE.parents[1]/'jingan-bank-of-communications-warehouse-guangfu-riverfront/measurements'))
from glb_triangles import load_triangles
from render_riverfront_survey import load_raster,raster

def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def cameras():
    data=read(HERE/'stone-cartouche-registration.json')
    c=runpy.run_path(str(HERE/'camera-fit/registered.py'))
    street=np.diag([940/920,705/690,1.])@c['K']@np.c_[c['R'],-c['R']@c['eye']]
    b=data['layout'];sx=(b['x1']-b['x0'])/271;sz=(b['z1']-b['z0'])/384
    # The close print has no independently surveyed camera position. Set a parallel front reference
    # at the measured shield plane (0.145m) and use the wide image and panoramas for depth.
    distance=300.;fx=distance/sx;fy=distance/sz
    eye=np.array([b['x0']+(626-490)*sx,-distance-.145,b['z0']+(512-320)*sz])
    R=np.array([[1.,0,0],[0,0,-1.],[0,1.,0.]])
    front=np.array([[fx,0,626.],[0,fy,320.],[0,0,1.]])@np.c_[R,-R@eye]
    stations=read(HERE/'stone-cartouche-2019-street-views.json')
    return {'2020-detail':front,'2020-street':street,**{k:np.array(v['P'])for k,v in stations.items()}}

def observations():
    marks={}
    def points(key,items):
        marks[key]=[(part,[x,y],kind) for part,x,y,kind in items]
    notes=[
     ('flat stone upper',588,260,'field'),('flat stone right',685,278,'field'),('flat stone centre',628,317,'field'),
     ('flat stone left',565,350,'field'),('flat stone lower',644,389,'field'),
     ('left volute',513,159,'carving'),('right volute',742,160,'carving'),('left fluted crown',577,150,'stone'),
     ('right fluted crown',676,150,'stone'),('centre bead',627,149,'carving'),('upper cornice',621,180,'stone'),
     ('left hanging fruit',509,275,'carving'),('right hanging fruit',741,276,'carving'),
     ('left upper ribbon',501,246,'carving'),('right upper ribbon',753,246,'carving'),
     ('left lower ribbon',504,403,'carving'),('right lower ribbon',749,404,'carving'),
     ('left ear and pendant',544,306,'carving'),('right ear and pendant',710,309,'carving'),
     ('left apron fold',552,422,'carving'),('right apron fold',702,423,'carving'),('apron tongue',615,444,'carving'),
     ('shelf left',526,468,'stone'),('shelf centre',627,476,'stone'),('shelf right',730,468,'stone'),
     ('corbel one',540,499,'stone'),('corbel two',599,499,'stone'),('corbel three',659,499,'stone'),('corbel four',716,499,'stone'),
     ('brick beside left upright',481,314,'outside'),('brick beside right upright',772,322,'outside'),
     ('wall below shelf',632,520,'outside'),('above crown',626,120,'outside')]
    points('2020-detail',notes)
    points('2020-street',[('upper roll',570,401,'stone'),('outer strip left',562,424,'stone'),('outer strip right',580,431,'stone'),
                          ('bare centre',572,428,'field'),('bare lower centre',572,435,'field'),('foot shelf',572,453,'stone'),
                          ('brick left',554,433,'outside'),('brick below',573,467,'outside'),('brick right',589,440,'outside')])
    points('2019-s1',[('bare centre',416,371,'field'),('bare upper',425,349,'field'),('bare lower',409,390,'field'),
                      ('right garland',450,349,'stone'),('left garland',388,389,'stone'),('upper roll',408,306,'stone'),
                      ('foot shelf',418,425,'stone'),('right corbel',450,410,'stone'),('exterior brick',473,375,'outside')])
    points('2019-s2',[('bare centre clear of pole',377,410,'field'),('bare lower clear of pole',385,429,'field'),
                      ('left garland',341,415,'stone'),('right garland',483,393,'stone'),
                      ('left shelf',352,477,'stone'),('exterior brick',302,431,'outside')])
    points('2019-s3',[('bare centre',371,387,'field'),('bare upper',361,366,'field'),('bare lower',382,410,'field'),
                      ('left garland',323,352,'stone'),('right garland',401,424,'stone'),('left crown',349,315,'stone'),
                      ('left corbel',333,433,'stone'),('right shelf',407,465,'stone'),('exterior brick',292,386,'outside')])
    return marks

def observe(mesh):
    tris,ids,mats,info=load_triangles(mesh)
    a=tris[:,0];e=tris[:,1]-a;f=tris[:,2]-a
    marks=observations();result={}
    for name,P in cameras().items():
        inv=np.linalg.inv(P[:,:3]);eye=-inv@P[:,3];q=eye-a;cr=np.cross(q,e);dot=np.einsum('ij,ij->i',cr,f)
        xyz=tris.reshape(-1,3)@P[:,:3].T+P[:,3]
        z=xyz[:,2].reshape(-1,3);screen=(xyz[:,:2]/np.where(abs(xyz[:,2,None])>1e-12,xyz[:,2,None],1.)).reshape(-1,3,2)
        lo=screen.min(axis=1);hi=screen.max(axis=1);crosses=(z.min(axis=1)<=0)&(z.max(axis=1)>0)
        def hit(uv):
            keep=np.flatnonzero(((lo<=uv).all(axis=1)&(hi>=uv).all(axis=1)&(z.max(axis=1)>0))|crosses)
            if not len(keep):return None
            ray=inv@[*uv,1];ray/=np.linalg.norm(ray)
            h=np.cross(ray,f[keep]);det=np.einsum('ij,ij->i',e[keep],h);ok=abs(det)>1e-11
            nz=np.where(ok,det,1.);u=np.einsum('ij,ij->i',q[keep],h)/nz;v=cr[keep]@ray/nz;t=dot[keep]/nz
            good=np.flatnonzero(ok&(u>=0)&(v>=0)&(u+v<=1)&(t>1e-6))
            return mats[ids[keep[good[np.argmin(t[good])]]]] if len(good) else None
        items=[]
        for feature,uv,want in marks[name]:
            def match(m):
                if want=='outside':return not (m or '').startswith('Cartouche |')
                if want=='field':return m=='Cartouche | weathered tablet face'
                if want=='carving':return m=='Cartouche | carved limestone'
                return (m or '').startswith('Cartouche |')
            first=hit(uv);distance=0. if match(first) else None
            if distance is None:
                for radius in (1.,2.,3.):
                    if any(match(hit(uv+radius*np.array([np.cos(v),np.sin(v)])))for v in np.arange(8)*np.pi/4):
                        distance=radius;break
            items.append(dict(feature=feature,pixel=uv,expected=want,first_material=first,nearest_px=distance))
        result[name]=dict(samples=len(items),centre=sum(i['nearest_px']==0 for i in items),within_3_px=sum(i['nearest_px'] is not None for i in items),rays=items)
    return dict(model=info,whole_scene_triangles=len(tris),parts_filtered=False,images=result)

def board(mesh,output):
    sheet=Image.new('RGB',(1220,820),'#f5f1e9');pen=ImageDraw.Draw(sheet)
    def label(pos,text,size,bold=False,fill='#292d2f'):
        font='/usr/share/fonts/opentype/noto/NotoSansCJK-'+('Bold'if bold else 'Regular')+'.ttc'
        pen.text(pos,text,font=ImageFont.truetype(font,size,index=2),fill=fill)
    label((36,13),'原上海公济医院北街立面石饰',36,True)
    label((37,75),'上部成对卷耳与饰珠相连；两侧花果垂带夹住中央素面。',20)
    P=cameras();sun=np.array([.47,-.84,.30]);sun/=np.linalg.norm(sun);stats={}
    with tempfile.TemporaryDirectory()as tmp:
        lib=load_raster(tmp)
        for n,rect,dest,width in [('2020-detail',[473,110,783,531],(36,129),450),
                                   ('2020-street',[551,394,591,466],(521,129),302)]:
            im,stat=raster(mesh,lib,width*2,P[n],rect,sun,(0,0))
            im=im.resize((width,round(im.height/2)),Image.Resampling.LANCZOS);sheet.paste(im,dest);stats[n]=stat
    label((36,749),'近正面 · 依2020年细部照片轮廓',18,True)
    label((521,690),'街角原机位 · 可见托座出挑',16,True)
    label((849,150),'石饰构造',25,True)
    for i,t in enumerate(['上端双卷耳、斜叶和串珠','两列花果，由交叉石带束起','中央石面有风化痕迹','下缘叶舌承接分层石檐','底部四个短托块分列']):
        label((849,222+55*i),t,17)
    label((849,554),'尺寸',17,True);label((849,590),'宽约2.44米，高约3.37米。',17)
    label((36,784),'图像均从模型光栅化生成。测量依据为乔争月 / SHINE 2020年两幅照片及2019年5月三处街景。',15,fill='#55534f')
    output.parent.mkdir(parents=True,exist_ok=True);sheet.save(output,quality=91,subsampling=0)
    return dict(file=output.name,sha256=sha(output),contains_source_photo_pixels=False,renders=stats)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mesh',type=Path);parser.add_argument('output',type=Path);parser.add_argument('--board',type=Path);args=parser.parse_args()
    res=observe(args.mesh)
    if args.board:res['board']=board(args.mesh,args.board)
    args.output.write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n')
    print({k:(v['centre'],v['within_3_px'],v['samples']) for k,v in res['images'].items()})
