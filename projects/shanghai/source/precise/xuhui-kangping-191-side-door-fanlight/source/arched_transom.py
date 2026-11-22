"""Radial fanlight and the shallowly rising timber head at 191 Kangping Road."""
from pathlib import Path
import math
import numpy as np
from PIL import Image
from shapely.geometry import box,Polygon,LineString
ID='xuhui-kangping-191-side-door-fanlight'
STUCCO='Warm white lime finish';MOULD='Raised light moulding';RIM='Outer brown curved frame';RING='Brown circular glazing bar';SPOKE='Dark brown sunray bar';GLASS='Warm light behind fanlight';HEAD='Dark brown shaped head';FRAME='Brown upper edge of leaf'
PALETTE={m:dict(color=c,roughness=r)for m,c,r in [(STUCCO,[1,1,1],.94),(MOULD,[.846,.833,.788],.90),(RIM,[.280,.219,.212],.81),(RING,[.235,.189,.184],.79),(SPOKE,[.240,.190,.183],.80),(GLASS,[.720,.649,.599],.38),(HEAD,[.257,.200,.194],.83),(FRAME,[.296,.232,.224],.83)]}
LEVEL=.307
ANGLES=[20,55,90,125,160]
def texture():
    f=Path(__file__).with_name('cream-lime-finish.png')
    if not f.exists():
        r=np.random.default_rng(827);a=np.array([208,203,191])+r.normal(0,2.5,(512,640,1))
        Image.fromarray(a.clip(0,255).astype('uint8')).quantize(64).save(f)
    PALETTE[STUCCO]['texture']=str(f)
def arc(r,steps):
    return [(r*math.cos(i*math.pi/steps),LEVEL+r*math.sin(i*math.pi/steps))for i in range(steps+1)]
def ring(outer,inner,steps):
    return Polygon(arc(outer,steps)+arc(inner,steps)[::-1])
def bottom(x):
    return LEVEL+.062*(math.cos(min(abs(x)/.764,1)*math.pi)+1)/2-.033
def add_building(b,far=False):
    texture();steps=26 if far else 78
    def face(shape,inner,outer,mat,name):b.prism(shape,inner,outer,lambda x,z,d:(x,-d,z),mat,name)
    hole=Polygon(arc(.810,steps)+[(-.810,-.005),(.810,-.005)])
    face(box(-1.018,0,1.018,1.322).difference(hole),-.169,0,STUCCO,'Cream plaster with arched opening')
    for part in b.parts:
        if part['material']==STUCCO:part['texcoords']=[[(x+1.018)/2.036,z/1.322]for x,y,z in part['vertices']]
    for rad in [.833,.855,.881,.906]:
        for s in [-1,1]:
            face(box(s*rad-.005,0,s*rad+.005,LEVEL),-.001,.008,MOULD,'Straight return of an archivolt moulding')
        face(ring(rad+.006,rad-.006,steps),-.001,.010,MOULD,'Fine raised concentric plaster moulding')
    face(ring(.814,.714,steps),-.145,.017,RIM,'Broad outer fanlight frame')
    face(ring(.737,.701,steps),-.106,.043,HEAD,'Stepped dark inner frame')
    for s in [-1,1]:
        l,r=sorted([s*.811,s*.710]);face(box(l,0,r,LEVEL+.0001),-.145,.017,RIM,'Vertical end of curved timber frame')
    fan=Polygon(arc(.714,steps))
    face(fan,-.164,-.138,GLASS,'Glazing set behind the radial frame')
    for rad in [.397,.133]:
        face(ring(rad+.017,rad-.017,steps),-.140,-.079,RING,'Concentric circular glazing bar')
    for deg in ANGLES:
        a=math.radians(deg);dx,dz=math.cos(a),math.sin(a)
        pts=[(r*dx,LEVEL+r*dz)for r in [.125,.719]]
        face(LineString(pts).buffer(.011,cap_style=2),-.136,-.082,SPOKE,'Individual radiating glazing bar at '+str(deg)+' degrees')
    xs=np.linspace(-.720,.720,17 if far else 41)
    rail=Polygon([(x,bottom(x)+.018)for x in xs]+[(x,bottom(x)-.054)for x in xs[::-1]])
    face(rail,-.142,.034,HEAD,'Shaped timber head with higher centre and lower ends')
    face(box(-.016,0,.037,bottom(0)-.049),-.100,.013,FRAME,'Visible head of the meeting stile')
    face(box(.032,.191,.717,.242),-.098,.012,FRAME,'Upper crosspiece of right door leaf')
