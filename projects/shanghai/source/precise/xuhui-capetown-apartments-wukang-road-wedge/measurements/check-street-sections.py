"""Compare true model intersections with the archive profile and separately read photograph pixels."""
import argparse, json, sys, math
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
from build_model import DATA,META,PRECISE,L,D,x,z,nose_plan
from finishes import GLASS,LIGHT,CAP,RENDER,BASE,SEAM,METAL,ROOF,TOE
sys.path.insert(0,str(PRECISE/'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import SerialScene
MATERIAL={GLASS:'#97aeb1',LIGHT:'#adc0bd',RENDER:'#d4d0b9',BASE:'#adaca1',CAP:'#e4dfc6',
          SEAM:'#a69c88',METAL:'#4e5c57',ROOF:'#8d897f',TOE:'#908c80'}
PHOTO={
 'before-repair':[(152,190,'glass'),(148,289,'glass'),(141,389,'glass'),
                  (232,177,'glass'),(234,277,'glass'),(220,377,'glass'),
                  (351,171,'glass'),(352,277,'glass'),(350,376,'glass'),
                  (184,232,'render'),(172,338,'render'),(369,327,'render'),(370,216,'render'),
                  (597,320,'render'),(182,512,'base')],
 'after-repair':[(344,225,'glass'),(344,315,'glass'),(344,402,'glass'),
                 (390,245,'glass'),(391,325,'glass'),(391,411,'glass'),
                 (465,272,'glass'),(467,341,'glass'),(472,406,'glass'),
                 (324,263,'render'),(321,345,'render'),(355,374,'render'),
                 (470,305,'render'),(471,377,'render'),(316,480,'base')]}
def check(p):
    scene=SerialScene(p);results=[]
    def cast(group,feature,eye,direction,wanted,px=None):
        hit=scene.ray(np.asarray(eye,float),np.asarray(direction,float),180.)
        results.append(dict(group=group,feature=feature,pixel=px,wanted=wanted,first=hit,
                            match=bool(hit and hit['material']in wanted)))
    for i,(u,v)in enumerate(DATA['round_windows']):
        cx,cz=x(u),z(v)
        for label,ox,oz,wanted in [('square pane',0,0,[GLASS]),('edge frame',.215,0,[METAL]),
          ('round reveal',.29,0,[CAP]),('surround',.41,0,[CAP]),('wall',.51,0,[RENDER])]:
            cast('archive',f'Porthole {i+2} {label}',(cx+ox,-2,cz+oz),(0,1,0),wanted)
    for i,(v0,v1)in enumerate(DATA['corner_slits']):
        for f in (.16,.47,.68):
            cast('archive',f'Bow {i+2} transverse light',(x(31+59*f),-2,z((v0+v1)/2)),(0,1,0),[GLASS])
    for family in ['left_windows','centre_windows','paired_windows','stair_windows']:
        for level,(u0,v0,u1,v1)in enumerate(DATA[family],2):
            picks=(.12,.76,.84,.91) if family=='paired_windows' else (.095,.41,.89)
            for fx in picks:
                for fy in (.28,.65):
                    steel = family=='paired_windows' and fx==.84
                    cast('archive',f'{family} F{level} '+('mullion' if steel else 'light'),(x(u0+(u1-u0)*fx),-2,z(v0+(v1-v0)*fy)),(0,1,0),[METAL] if steel else [GLASS,LIGHT])
    cast('archive','flat roof behind street parapet',(L*.72,D*.20,25),(0,0,-1),[ROOF])
    cams=json.loads((HERE/'two-registered-street-photos.json').read_bytes())
    accept={'glass':[GLASS,LIGHT],'render':[RENDER],'base':[BASE]}
    for name,rows in PHOTO.items():
        c=cams[name];matrix=np.array(c['projection']);inv=np.linalg.inv(matrix[:,:3])
        for u,v,k in rows:
            cast(name,k,c['eye_xyz'],inv@[u,v,1.],accept[k],[u,v])
    groups={k:{'matched':sum(t['match']for t in results if t['group']==k),
               'total':sum(t['group']==k for t in results)}for k in ('archive',*cams)}
    return dict(asset=scene.asset,groups=groups,rays=results)
def plate(p,image):
    scene=SerialScene(p);im=Image.new('RGB',(1140,650),'#f2efe6');draw=ImageDraw.Draw(im)
    def font(sz):return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',sz)
    draw.text((38,22),'Kempton Apartments',font=font(33),fill='#293b36')
    draw.text((40,72),'Wukang Road elevation and 1947 plot outline',font=font(20),fill='#495a52')
    scale=min(700/L,415/z(33))
    def sx(xy):return 45+xy[0]*scale,550-xy[2]*scale
    pairs=[(np.mean(t[:,1]),t,idx)for t,idx in zip(scene.tri,scene.mi)]
    for _,t,i in sorted(pairs,key=lambda t:-t[0]):
        if np.cross(t[1]-t[0],t[2]-t[0])[1]>=-1.e-8:continue
        pts=[sx(v)for v in t];draw.polygon(pts,fill=MATERIAL[scene.materials[i]])
    draw.line((46,550,790,550),fill='#777166',width=2)
    draw.line((812,122,812,563),fill='#bfb8a9',width=1)
    draw.text((832,151),'Building footprint',font=font(20),fill='#2d4239')
    plan=[(842+v[0]*12,430-v[1]*12)for v in list(nose_plan(22).exterior.coords)]
    draw.polygon(plan,fill='#d4cebb',outline='#526257',width=3);draw.line((842,430,842+L*12,430),fill='#87513b',width=5)
    draw.text((844,447),'Wukang Road',font=font(17),fill='#80503e')
    draw.text((39,590),'Original projection from the downloadable model. Archive dimensions and photographic limits accompany the source.',font=font(16),fill='#536256')
    im.save(image,quality=92)
if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('glb',type=Path);cli.add_argument('json',type=Path);cli.add_argument('--plate',type=Path);o=cli.parse_args()
    report=check(o.glb);o.json.parent.mkdir(parents=True,exist_ok=True);o.json.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    if o.plate:plate(o.glb,o.plate)
    print(report['groups'])
