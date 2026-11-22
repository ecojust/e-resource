"""Three gabled piers and the two ironwork spans photographed at 42 Huating Road."""
from pathlib import Path
import numpy as np
from PIL import Image
from shapely.geometry import Polygon, box, LineString
from shapely.affinity import translate
ID = 'xuhui-huating-42-gabled-gateposts'
RENDER, BORDER, BASE = 'Yellow panel render', 'Pale grey rendered border', 'Grey cement plinth'
TILE, RIDGE, IRON, PLATE, MARK = 'Brown ceramic tiles', 'Rounded pale ridge cap', 'Black ironwork', 'Green enamel', 'Painted address digits'
PALETTE = {m: dict(color=c,roughness=r) for m,c,r in [
    (RENDER,[1,1,1],.94),(BORDER,[.738,.738,.675],.93),(BASE,[.381,.395,.39],.94),
    (TILE,[.426,.241,.178],.90),(RIDGE,[.75,.755,.69],.84),(IRON,[.095,.091,.085],.67),
    (PLATE,[.09,.317,.206],.65),(MARK,[.87,.853,.70],.68)]}
CENTRES = (-1.32,.20,1.37)
def texture():
    target=Path(__file__).with_name('buff-painted-render.png')
    if not target.exists():
        rng=np.random.default_rng(779)
        field=rng.normal(0,2.6,(240,240,1))+np.array([211,190,139])
        Image.fromarray(field.clip(0,255).astype('uint8')).quantize(80).save(target)
    PALETTE[RENDER]['texture']=str(target)
def digit_lines():
    four=[(-.066,1.750),(-.101,1.692),(-.043,1.692)]
    stem=[(-.061,1.755),(-.061,1.660)]
    two=[(-.021,1.731),(-.012,1.747),(.008,1.753),(.024,1.750),(.036,1.738),(.034,1.722),(.022,1.706),(-.014,1.669),(.038,1.669)]
    return [translate(LineString(points).buffer(.0055,cap_style=2,join_style=2),CENTRES[0]+.024) for points in [four,stem,two]]
def add_building(b,far=False):
    texture()
    def face(poly,d0,d1,mat,name):
        b.prism(poly,d0,d1,lambda x,z,d:(x,-d,z),mat,name)
    def rect(l,r,z,t,d0,d1,mat,name):
        face(box(l,z,r,t),d0,d1,mat,name)
    def stroke(points,radius,mat,name,depth=-.14):
        face(LineString(points).buffer(radius,resolution=3 if far else 6,join_style=1),depth,depth+.018,mat,name)
    for idx,x in enumerate(CENTRES):
        rect(x-.201,x+.201,0,1.92,-.39,0,BORDER,'Grey-edged gatepost '+str(idx+1))
        rect(x-.206,x+.206,0,.20,-.396,.007,BASE,'Cement base')
        rect(x-.130,x+.130,.273,1.811,.0005,.005,RENDER,'Buff panel on the street face')
        head=Polygon([(x-.222,1.90),(x+.222,1.90),(x+.222,1.96),(x,2.27),(x-.222,1.96)])
        face(head,-.404,.015,BORDER,'Rendered triangular gable')
        face(Polygon([(x-.140,1.972),(x+.140,1.972),(x,2.190)]),.015,.020,RENDER,'Pale triangular tympanum')
        for sx in [-1,1]:
            for row in range(3):
                for col in range(6 if not far else 3):
                    count=3 if far else 6
                    y0=-.022+.443*col/count;y1=-.022+.443*(col+1)/count-.003
                    u0=row*.075;u1=(row+1)*.075+.003
                    levels=(.013*(2-row),.013*(2-row)+.013)
                    b.prism(box(min(sx*u0,sx*u1),y0,max(sx*u0,sx*u1),y1),*levels,lambda u,y,h:(x+u,y,2.254-sx*u*1.38+h),TILE,'Overlapping row of brown roof tiles')
        profile=Polygon([(x+.047*np.cos(t),2.281+.047*np.sin(t)) for t in np.linspace(0,2*np.pi,13 if far else 29)[:-1]])
        face(profile,-.43,.032,RIDGE,'Pale cylindrical ridge with projecting end')
    x=CENTRES[0]
    rect(x-.129,x+.129,1.626,1.788,.006,.020,PLATE,'Green enamel address plate on first pier')
    for digit in digit_lines():face(digit,.019,.028,MARK,'Hand-drawn address 42')
    left=CENTRES[0]+.20;right=CENTRES[1]-.20
    for xx in np.linspace(left+.08,right-.08,5):
        stroke([(xx,.22),(xx,1.43)],.009,IRON,'Thin iron upright')
    for zz in [.28,.71]:
        stroke([(left,zz),(right,zz)],.011,IRON,'Gate rail')
    for xx,zz,scale,sign in [(left+.28,1.67,.21,1),(right-.19,1.45,.14,-1),(left+.53,1.09,.13,1),(right-.22,.86,.11,1),(left+.30,.48,.105,-1)]:
        ts=np.linspace(-1.8,4.85,23 if far else 41);rr=scale*(1-(ts-ts[0])/(ts[-1]-ts[0])*.74)
        pts=[(xx+sign*r*np.cos(t),zz+r*np.sin(t)) for t,r in zip(ts,rr)]
        attach=min(np.linspace(left+.08,right-.08,5),key=lambda upright:abs(upright-pts[0][0]))
        toe=min(1.35,zz-.35)
        s=np.linspace(0,1,9 if far else 18)
        headx,headz=pts[0]
        stem=[(attach+(headx-attach)*v*v,toe+(headz-toe)*v) for v in s]
        stroke(stem+pts,.012,IRON,'Forged iron scroll rising from its upright')
    left=CENTRES[1]+.20;right=CENTRES[2]-.20
    rect(left,right,0,.18,-.25,.004,BASE,'Low wall below the shorter railing')
    for xx in np.linspace(left+.06,right-.06,5):stroke([(xx,.18),(xx,1.49)],.009,IRON,'Railing upright')
    for zz in [.26,1.37]:stroke([(left,zz),(right,zz)],.010,IRON,'Horizontal railing')
    for xx in [left+.15,(left+right)/2,right-.15]:
        ts=np.linspace(.14,2.95,11 if far else 24)
        stroke([(xx+.098*np.cos(t),1.355+.076*np.sin(t)) for t in ts],.009,IRON,'Shallow bowed railing crest')
    for part in b.parts:
        if part['material']==RENDER:
            part['texcoords']=[[(x+.19)/.67,z/.67] for x,y,z in part['vertices']]
