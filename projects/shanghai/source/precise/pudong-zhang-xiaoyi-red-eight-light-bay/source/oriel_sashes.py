"""Four paired sashes in the shallow bay of the Zhang Xiaoyi residence, Xinchang Street."""
import math
from pathlib import Path
import numpy as np
from PIL import Image
from shapely.geometry import Polygon

ID='pudong-zhang-xiaoyi-red-eight-light-bay'
PAINT='Faded red timber window frames';BOARD='Weathered red boards below the sill';GLASS='Pale grey reflected glass';EDGE='Brown red timber fillet';CORNICE='Grey upper cornice';HINGE='Dark hinge barrel'
PALETTE={n:dict(color=c,roughness=r) for n,c,r in ((PAINT,[1,1,1],.81),(BOARD,[1,1,1],.89),(GLASS,[1,1,1],.26),(EDGE,[.41,.19,.115],.86),(CORNICE,[.44,.41,.35],.87),(HINGE,[.261,.192,.142],.64))}
def texture():
    f=Path(__file__).with_name('vermilion-glass-and-weathered-boards.png')
    if not f.exists():
        g=np.random.default_rng(867);h,w=216,256;y,x=np.indices((h,w))
        streak=np.asarray(Image.fromarray(g.integers(0,255,(14,200),dtype='uint8')).resize((w,h),Image.Resampling.BILINEAR),float)-127
        broad=np.asarray(Image.fromarray(g.integers(0,255,(7,13),dtype='uint8')).resize((w,h),Image.Resampling.BILINEAR),float)-127
        flake=np.maximum(0,streak*.70+.21*broad-16)
        pa=np.array([172,73,51])+(.14*streak+.10*broad+g.normal(0,2.8,(h,w)))[:,:,None]
        bo=np.array([160,107,82])+(.62*flake+.24*streak+.19*broad+g.normal(0,3.4,(h,w)))[:,:,None]
        gl=np.array([159,168,169])+(y/h*31-12+.1*broad+2.7*np.sin(x*.017+y*.029))[:,:,None]
        Image.fromarray(np.concatenate((pa,bo,gl),axis=1).clip(0,255).astype('uint8')).quantize(160).save(f)
    for mat in (PAINT,BOARD,GLASS):PALETTE[mat]['texture']=str(f)

WIDTH=.98
Y0=[.22,.06,0,.06,.22]
LOW=.73
HIGH=1.99
def frame(i):
    more=Y0[i+1]-Y0[i];a=math.hypot(WIDTH,more); ux=WIDTH/a;uy=more/a
    return (i-1.5)*WIDTH,(Y0[i]+Y0[i+1])*.5,ux,uy,a
def point(i,s,d,z):
    cx,cy,ux,uy,a=frame(i)
    return cx+ux*s+uy*d,cy+uy*s-ux*d,z
def add_building(b,far=False):
    texture()
    def part(i,s1,s2,z1,z2,d1,d2,mat,label):
        assert s2>s1 and d2>d1 and z2>z1
        vertices=[point(i,s,d,z) for z in (z1,z2) for d in (d2,d1) for s in (s1,s2)]
        b.add(vertices,[(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5)],mat,label)
    for i in range(4):
        cx,cy,ux,uy,a=frame(i)
        for side in (0,1):
            left=(side*.5-.5)*a;right=left+a*.5
            for s in (left+.021,right-.021):
                part(i,s-.020,s+.020,LOW,HIGH,-.045,.057,PAINT,'Paired sash upright')
            for z1,z2 in ((LOW,LOW+.058),(HIGH-.057,HIGH)):
                part(i,left+.035,right-.035,z1,z2,-.044,.056,PAINT,'Top or bottom of opening sash')
            v0=LOW+.053;v1=HIGH-.053;spacing=(v1-v0)/4
            for j in range(4):
                part(i,left+.039,right-.039,v0+j*spacing,v0+(j+1)*spacing,-.046,-.032,GLASS,'One of four glass panes in a red sash')
            for j in (1,2,3):
                z=v0+j*spacing
                part(i,left+.039,right-.039,z-.0085,z+.0085,-.031,.031,PAINT,'Fine red horizontal glazing bar')
            for j in range(3):
                l=left+j*(right-left)/3
                part(i,l+.003,l+(right-left)/3-.003,.10,.641,-.036,.002,BOARD,'Weathered upright panel beneath sash')
        for z1,z2,d1,d2,m,label in ((.02,.091,-.095,.068,EDGE,'Lower bead along boarded bay'),(.08,.112,-.062,.036,PAINT,'Red lower border'),(.625,.688,-.06,.044,PAINT,'Rail over vertical boarded skirt'),(.683,.743,-.071,.087,EDGE,'Projecting sill of upper windows'),(1.985,2.067,-.067,.074,PAINT,'Red head rail'),(2.06,2.113,-.082,.094,CORNICE,'Dark under edge of cornice'),(2.11,2.162,-.092,.116,CORNICE,'Projecting grey top course')):
            part(i,-a/2-.002,a/2+.002,z1,z2,d1,d2,m,label)
        for z in (.89,1.79):
            for s in (-a*.5+.023,a*.5-.023):
                rad=.011;num=7 if far else 17;pts=[]
                for zz in (z-.042,z+.042):
                    for k in range(num):
                        ang=2*math.pi*k/num;pts.append(point(i,s+rad*math.cos(ang),.060+rad*math.sin(ang),zz))
                faces=[(k,(k+1)%num,num+(k+1)%num,num+k) for k in range(num)]
                faces.extend((tuple(range(num-1,-1,-1)),tuple(range(num,2*num))))
                b.add(pts,faces,HINGE,'Small hinge barrel on two outer edges of each pair')
    for j,p in enumerate(b.parts):
        m=p['material']
        if m not in (PAINT,BOARD,GLASS):continue
        strip=(PAINT,BOARD,GLASS).index(m)
        p['texcoords']=[((strip+.025+.946*min(.99,max(0,(x+2)/4)))/3,.985-.963*min(1,max(0,z/2.17))) for x,y,z in p['vertices']]
