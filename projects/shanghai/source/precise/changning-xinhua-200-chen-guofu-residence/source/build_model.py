"""South garden entrance, double loggia and glazed swept roof at 200 Xinhua Road.

Local X follows the eaves towards the right of the 2010 garden photograph,
Y runs into the building, Z is up. The rear roof depth uses aerial controls.
"""
import argparse
import math
import json
import numpy as np
from pathlib import Path
import sys

HERE = Path(__file__).absolute().parent
PROJECT = next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
from photo_architecture import Builder
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from reclining_lions import add_lions

ID = 'changning-xinhua-200-chen-guofu-residence'
META = dict(id=ID,name='新华路200号陈果夫住宅南面重檐外廊',address='长宁区新华路200号',heritage_id='sh-historic-b3-109',protection_number='3M011',unit='metre',geometry_license='MIT',photos_embedded=False,viewer_page='xinhua-200-chen-guofu-residence.html',scope='南园双层透廊、卧狮入口、上堂立面和两重琉璃瓦檐；屋背未作室内外调查。')
CREAM='pale stucco'; BUFF='warm ochre stucco'; RED='red glazed pantile'; EDGE='dark red tile noses'
STONE='cut stone'; TIMBER='brown lacquerwork'; GLASS='recessed garden glazing'; JADE='painted bracket'; DARK='stained soffit'
PALETTE={k:{'color':c,'roughness':r} for k,c,r in (
 (CREAM,[.80,.795,.70],.91),(BUFF,[.858,.667,.357],.88),(RED,[.60,.112,.061],.46),
 (EDGE,[.47,.087,.051],.38),(STONE,[.555,.526,.453],.9),(TIMBER,[.155,.125,.096],.66),
 (GLASS,[.128,.176,.164],.27),(JADE,[.181,.290,.259],.72),(DARK,[.185,.106,.074],.77))}

PALETTE[GLASS]["alpha"]=.88
META["camera_views"]=json.loads((HERE/"cameras.json").read_bytes())

def block(b,x,y,z,w,d,h,mat,name):
    b.box((x,y,z),(w,d,h),mat,label=name)

def facing(b,shape,y,d,mat,name):
    b.prism(shape,-y-d,-y,lambda x,z,t:(x,-t,z),mat,name)

def beams(b,points,r,mat,name,lod):
    b.tube(points,r,mat,6 if lod else 10,name)

def multi_window(b,x,y,sill,w,h,cols,name,lod,door=False):
    casing=box(x-w/2,sill,x+w/2,sill+h)
    inner=casing.buffer(-.074,join_style=2)
    facing(b,casing.difference(inner),y,.11,TIMBER,name+' casing')
    block(b,x,y+.15,sill+h/2,w-.145,.036,h-.145,GLASS,name+' glazing')
    for i in range(1,cols):
        block(b,x+w*(i/cols-.5),y+.05,sill+h/2,.055,.066,h-.14,TIMBER,name+f' mullion {i}')
    for z in ((.69,.87) if door or lod else (.24,.66,.84)):
        block(b,x,y+.046,sill+h*z,w-.143,.07,.044,TIMBER,name+f' transom {z}')

def masonry(b,y,z0,z1,half,holes,mat,name,lod):
    wall=box(-half,z0,half,z1)
    cuts=[]
    for x,sill,w,h,n,t in holes:
        cuts.append(box(x-w/2,sill,x+w/2,sill+h))
        multi_window(b,x,y+.16,sill,w,h,n,name+'/'+t,lod,'door' in t)
    facing(b,wall.difference(unary_union(cuts)),y,.28,mat,name+' perforated wall')

def post(b,x,y,base,top,r,name,lod):
    block(b,x,y,base+.15,r*2.4,r*2.4,.30,STONE,name+' foot')
    b.lathe((x,y),[(base+.30,r*1.06),(base+.38,r*1.06),(base+.42,r),(top-.30,r*.89),(top-.25,r*1.02),(top-.12,r*1.02)],CREAM,12 if lod else 20,name+' shaft')
    block(b,x,y,top-.08,2.43*r,2.43*r,.16,CREAM,name+' square capital')

def slab(b,poly,z,thickness,mat,name):
    b.plan_prism(Polygon(poly),z,z+thickness,mat,name)

PIERS=(-10.70,-7.03,-3.68,-2.65,2.65,3.68,7.03,10.70)
BALCONY=[(-11.15,-.16),(-3.89,-.16),(-3.89,-.91),(3.89,-.91),(3.89,-.16),(11.15,-.16),(11.15,3.58),(-11.15,3.58)]

def gallery(b,lod):
    for z,t,name in ((.41,.16,'garden landing'),(5.08,.22,'upper balcony'),(9.54,.175,'intermediate eave soffit')):
        slab(b,BALCONY,z,t,CREAM,name)
    for i,x in enumerate(PIERS):
        y=-.55 if abs(x)<3.9 else .15
        for k,(base,top) in enumerate(((.57,5.08),(5.30,9.54))):
            post(b,x,y,base,top,.195 if abs(x)<3.9 else .202,f'column {i+1} level {k+1}',lod)
    for side in (-1,1):
        post(b,side*10.70,2.85,.57,5.08,.195,'side return lower '+str(side),lod)
        post(b,side*10.70,2.85,5.30,9.54,.195,'side return upper '+str(side),lod)
    for i,(left,right) in enumerate(zip(PIERS,PIERS[1:])):
        if right-left<1.08:continue
        yy=-.735 if left==-2.65 else (.06 if abs(left)>3.6 or right>3.6 else -.5)
        low,high=5.30,6.10
        plate=box(left+.15,low,right-.15,high)
        holes=[];num=max(4,round((right-left-.40)/.50));step=(right-left-.54)/num
        for j in range(num):
            xx=left+.27+step*(j+.5)
            holes.append(Polygon([(xx-.37*step,low+.60),(xx-.3*step,low+.35),(xx,low+.23),(xx+.27*step,low+.32),(xx+.38*step,low+.60)]))
        facing(b,plate.difference(unary_union(holes)),yy,.17,CREAM,f'open fretwork balcony bay {i+1}')
        block(b,(left+right)/2,yy+.075,high+.045,right-left+.01,.31,.09,CREAM,f'rail coping {i+1}')
    for z in (4.95,9.38):
        for x,w,y in [(-7.23,7.96,.15),(0,7.64,-.56),(7.23,7.96,.15)]:
            block(b,x,y,z,w,.35,.24,CREAM if z<6 else DARK,f'eave beam {x} {z}')
    for x in PIERS:
        y=-.58 if abs(x)<3.9 else .12
        for side in (-1,1):
            for j,(s,z) in enumerate(((.21,9.02),(.34,9.14),(.53,9.24))):
                block(b,x+side*s*.50,y,z,s+.08,.22,.105,JADE,f'painted bracket {x} {side} {j}')
    wings=[(x,1.53,w,1.98,3 if w>1.7 else 2,'window '+str(i+1)) for i,(x,w) in enumerate(((-8.45,1.66),(-5.54,1.85),(5.62,1.85),(8.44,1.65)))]
    doors=[(x,.57,w,3.05,n,'recessed door '+str(j+1)) for j,(x,w,n) in enumerate(((-1.77,1.15,2),(0,1.70,2),(1.77,1.15,2)))]
    masonry(b,3.03,.57,5.08,10.99,wings+doors,CREAM,'ground garden wall',lod)
    # A second pierced floral band hangs below the landing. Its four-petal
    # openings and paired cusps are distinct from the balcony rail above.
    for i,(left,right) in enumerate(zip(PIERS,PIERS[1:])):
        width=right-left
        if width<1.1:continue
        yy=-.75 if i==3 else -.065
        def open_fan(cx,z,r):
            from shapely.geometry import Point
            leaves=[Point(cx+r*.44*math.cos(a),z+r*.36*math.sin(a)).buffer(r*.63,quad_segs=3 if lod else 6) for a in (.32,1.85,3.48,5.02)]
            return unary_union(leaves)
        blank=box(left+.18,4.48,right-.18,4.87)
        repeats=max(2,int(width/.55))
        holes=[open_fan(left+(j+.5)*width/repeats,4.695,.135) for j in range(repeats)]
        facing(b,blank.difference(unary_union(holes)),yy,.159,CREAM,'pierced lower beam floral fret bay '+str(i+1))
        block(b,(left+right)/2,yy+.07,4.454,width-.18,.235,.074,CREAM,'lower beam lip '+str(i+1))
        block(b,(left+right)/2,yy+.065,4.924,width-.12,.26,.085,CREAM,'lower beam moulding '+str(i+1))
        # Each rafter-end bracket under the tiled roof has a dark painted V web.
        n=max(3,round(width/.80))
        for j in range(n):
            cx=left+width*(j+.5)/n
            for sign in (-1,1):
                beams(b,[(cx+sign*.21,yy-.017,9.45),(cx+sign*.078,yy-.027,9.19),(cx,yy-.030,9.14)],.036,JADE,'painted rafter scroll '+str((i,j,sign)),lod)
    windows=[(x,6.08,w,2.35,n,'bay '+str(j+1)) for j,(x,w,n) in enumerate(((-8.36,1.94,3),(-5.55,1.99,3),(-1.94,1.6,3),(0,1.78,3),(1.94,1.6,3),(5.55,1.99,3),(8.36,1.94,3)))]
    masonry(b,3.03,5.30,9.54,10.99,windows,CREAM,'upper gallery back wall',lod)
    for j in range(5):
        height=.57*(j+1)/5
        block(b,0,-2.90+.34*j,height/2,5.30,.342,height,STONE,'entrance tread '+str(j+1))
    for side in (-1,1):
        block(b,side*3.62,-1.96,.215,1.62,2.08,.43,STONE,'lion plinth '+str(side))
        block(b,side*3.62,-1.96,.49,1.54,1.98,.12,STONE,'lion slab '+str(side))

def attic(b,lod):
    holes=[(-7.65,10.83,2.17,1.88,4,'outer western window'),(-4.72,10.83,.86,1.91,2,'narrow western window'),(4.72,10.83,.86,1.91,2,'narrow eastern window'),(7.65,10.83,2.17,1.88,4,'outer eastern window')]
    profile=[(-2.87,10.50),(-2.87,12.29),(-2.57,12.29),(-2.48,12.52),(-2.22,12.56),(-2.12,12.77),(2.12,12.77),(2.22,12.56),(2.48,12.52),(2.57,12.29),(2.87,12.29),(2.87,10.50)]
    portal=Polygon(profile)
    cuts=[box(x-w/2,z,x+w/2,z+h) for x,z,w,h,_,_ in holes]
    wall=box(-9.71,9.98,9.71,13.72).difference(unary_union(cuts+[portal]))
    facing(b,wall,2.84,.26,BUFF,'ochre upper hall with bracket-ended central recess')
    for x,z,w,h,n,name in holes:multi_window(b,x,3.0,z,w,h,n,name,lod)
    masonry(b,3.77,10.48,12.85,3.27,[(0,10.70,4.08,1.73,7,'central ribbon window')],BUFF,'recess back',lod)
    for side in (-1,1):
        block(b,3.48*side,2.71,11.74,.23,.34,3.50,BUFF,'upper porch pier '+str(side))
        block(b,side*9.57,6.42,11.78,.28,7.16,3.72,BUFF,'observed eaves return '+str(side))
    block(b,0,2.71,10.51,5.74,.39,.21,CREAM,'recessed opening sill')

def swept_roof(b,w,d,y,base,rise,ridge,rise_tip,name,lod):
    # The centreline remains low at the eaves while the four corner rafters turn up.
    # Four curved trapezoidal planes share hip lines and have individually closed soffits.
    count=6 if lod else 11;steps=3 if lod else 6
    for face in range(4):
        side=face in (1,3)
        def xyz(s,t):
            a=w*(1-t)+ridge*t;depth=d*(1-t)
            if face==0:u,v=a*s,-depth
            elif face==1:u,v=a,depth*s
            elif face==2:u,v=-a*s,depth
            else:u,v=-a,-depth*s
            accent=(abs(s)**6 if not side else abs(s)**3)*(1-t)**3
            return (u,y+v,base+rise*(.49*t+.51*t*t)+rise_tip*accent)
        # The gable-end hip tapers to a point at the ridge. Make one shared terminal vertex.
        vs=[];faces=[]
        def v(point):
            key=tuple(round(x,7) for x in point)
            if key not in ix:ix[key]=len(vs);vs.append(point)
            return ix[key]
        ix={}
        for j in range(steps):
            for i in range(count*2):
                a=i/count-1;c=(i+1)/count-1;lo=j/steps;hi=(j+1)/steps
                p=[xyz(a,lo),xyz(c,lo),xyz(c,hi),xyz(a,hi)]
                top=list(dict.fromkeys(v(k) for k in p));bot=list(dict.fromkeys(v((x,yy,z-.18)) for x,yy,z in p))
                if len(top)>2:faces+=[top,list(reversed(bot))]
                for k,edge in enumerate((j==0,i==count*2-1,j==steps-1,i==0)):
                    if edge and p[k]!=p[(k+1)%4]:
                        pa,pb=p[k],p[(k+1)%4];faces.append((v(pb),v(pa),v((pa[0],pa[1],pa[2]-.18)),v((pb[0],pb[1],pb[2]-.18))))
        b.add(vs,faces,RED,f'{name}/swept closed face {face+1}')
        edge=[xyz(-1+i/count,0) for i in range(count*2+1)]
        beams(b,edge,.092,EDGE,f'{name}/raised outer eave {face+1}',lod)
        # Tile rolls follow the dip first and the steep climb towards the ridge.
        for i in range(1,(12 if lod else 32)):
            s=-1+2*i/(12 if lod else 32)
            pts=[xyz(s,j/steps) for j in range(steps+1)]
            beams(b,[(x,yy,z+.033) for x,yy,z in pts],.033,RED,f'{name}/tile roll {face+1}.{i}',lod)
        hip=[xyz(-1,j/steps) for j in range(steps+1)]
        beams(b,[(x,yy,z+.085) for x,yy,z in hip],.11,EDGE,f'{name}/hip roll {face+1}',lod)
    beams(b,[(-ridge-.14,y,base+rise+.26),(-ridge+.14,y,base+rise+.12),(ridge-.14,y,base+rise+.12),(ridge+.14,y,base+rise+.26)],.14,EDGE,name+'/ridge with raised ends',lod)

def build(lod=False):
    b=Builder(PALETTE);gallery(b,lod);attic(b,lod);add_lions(b,lod,STONE)
    # Lower main apron sits partly behind the centre pavilion eave.
    swept_roof(b,12.23,6.78,6.08,9.61,.94,7.2,.54,'lower glazed roof',lod)
    swept_roof(b,4.03,.98,-.34,9.84,.30,2.27,.47,'central projecting porch roof',lod)
    swept_roof(b,11.70,8.63,10.0,13.59,2.03,4.37,1.20,'upper glazed hip roof',lod)
    correction=json.loads((HERE.parent/'measurements/elevation-corrections.json').read_bytes())
    for part in b.parts:
        vertices=np.asarray(part['vertices']);vs=vertices.copy()
        vs[:,2]=np.interp(vertices[:,2],correction['original_levels'],correction['adopted_levels'])+np.maximum(0,vertices[:,2]-correction['original_levels'][-1])
        if part['label'].startswith('central projecting porch roof/'):
            vs[:,0]*=correction['porch_eave_width_factor']
        elif part['label'].startswith('upper glazed hip roof/'):
            # Scale the ridge end displacement continuously to zero at the full-width eaves.
            inward=np.clip(1-np.abs(vertices[:,1]-10.)/8.63,0,1)
            vs[:,0]*=1+(correction['ridge_length_factor']-1)*inward
        part['vertices']=vs.tolist()
    return b
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--lod',action='store_true');a=p.parse_args()
    from serialize_mesh import save_study
    print(save_study(build(a.lod),a.output,META)['sha256'])
