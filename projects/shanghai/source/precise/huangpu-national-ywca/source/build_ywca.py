"""Yuanmingyuan Road east elevation and southeast return of the National YWCA."""
import math
import json
import sys
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,box
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3];sys.path.insert(0,str(PROJECT/'tools'))
from package_architectural_model import build
from photo_architecture import Facade,opening
from sign_lettering import add_facade_lettering
P=json.loads((HERE/'parameters.json').read_bytes())
ID=P['id']
META={'id':ID,'name':'中华基督教女青年会大楼圆明园路主立面','status':'photo-informed-partial-exterior',
      'scope':'East elevation, decorated portal, photographed southeast return and upper setbacks of the National YWCA building. Depth limited to 12 m.',
      'model_scope_zh':'圆明园路133号东面七组竖窗、清水砖和花岗石、带琉璃瓦小檐的中央石门框、菱格门楣、南转角与上层退台。院内及后翼另计。',
      'source_register':'source/precise/'+ID+'/reference-review.json','viewer_page':'national-ywca.html','audit_directory':'data/audit/national-ywca-v1/',
      'coordinate_convention':'glTF +X follows Yuanmingyuan Road northwards, +Y up, +Z eastward to the street; origin at the central street elevation.',
      'map_reference_license':'OpenStreetMap / Overture Maps, ODbL-1.0.','inscription_font_license':'SIL Open Font License 1.1, Noto Serif CJK SC Regular subset','interiors_modeled':False}
PAL={'brick':{'color':[.518,.300,.225],'roughness':.93},'brick variation':{'color':[.471,.262,.202],'roughness':.91},
     'mortar':{'color':[.435,.321,.276],'roughness':.93},'granite':{'color':[.513,.482,.416],'roughness':.86},
     'relief granite':{'color':[.619,.588,.516],'roughness':.83},'carved pale stone':{'color':[.549,.514,.437],'roughness':.86},
     'portal timber':{'color':[.190,.094,.058],'roughness':.61},'glazed tile':{'color':[.26,.34,.314],'roughness':.45,'metallic':.13},
     'blue lamp glass':{'color':[.073,.193,.216],'roughness':.29,'metallic':.17},'recessed glass':{'color':[.112,.164,.181],'roughness':.24,'metallic':.27},
     'bronze window frame':{'color':[.129,.131,.120],'roughness':.53,'metallic':.31},'awning canvas':{'color':[.103,.099,.092],'roughness':.90},
     'roof membrane':{'color':[.310,.293,.258],'roughness':.87}}
XS=[-12.07,-7.00,-3.50,0,3.50,7.00,12.07]
FLOORS=[5.18,9.05,12.92,16.79,20.66]


def panel_border(f,x,z,w,h,depth,label):
    g=box(x-w/2,z-h/2,x+w/2,z+h/2)
    inset=g.buffer(-.07,join_style=2)
    f.prism(g.difference(inset),depth-.055,depth+.024,'relief granite',label)


def patterned_panel(f,x,z,w,h,lod):
    """Square fret units like the geometric reliefs above the ground-storey sashes."""
    f.box(x,z,w,h,.14,.068,'granite','relief window apron')
    panel_border(f,x,z,w-.09,h-.08,.143,'relief apron border')
    if lod:
        f.box(x,z,w*.63,.075,.09,.14,'relief granite','apron horizontal bar')
        return
    n=max(2,round(w/.42))
    for j in range(n):
        u=x+(j+.5-n/2)*w/n;r=min(.15,w/n*.35);dz=min(.18,h*.26)
        for s in [-1,1]:
            pts=[(u-r,z+s*dz*.38,.161),(u-r,z+s*dz,.161),(u+r*.39,z+s*dz,.161),
                 (u+r*.39,z+s*dz*.26,.161),(u+r,z+s*dz*.26,.161)]
            f.builder.tube([f.point(*q)for q in pts],.025,'relief granite',5,f.label+'/apron meanders')


def plinth(f, doorway=False):
    for z,h,d,mat in [( .16,.30,.25,'granite'),(.45,.20,.35,'relief granite'),
                     (.61,.15,.25,'granite'),(.75,.16,.31,'relief granite')]:
        spans=[(-f.length/2,-1.08),(1.08,f.length/2)] if doorway else [(-f.length/2,f.length/2)]
        for a,c in spans:
            f.box((a+c)/2,z,c-a,h,.48+d,d/2-.20,mat,'lotus-profile granite base')


def shop_awning(f,x,w):
    poly=Polygon([(x-w/2,4.06),(x+w/2,4.06),(x+w/2+.12,3.91),(x-w/2-.12,3.91)])
    f.prism(poly,.24,.94,'awning canvas','modern entrance canopy hem')
    pts=[f.point(x-w/2,4.47,.03),f.point(x+w/2,4.47,.03),f.point(x+w/2+.12,4.06,.95),f.point(x-w/2-.12,4.06,.95)]
    f.builder.add(pts,[(3,2,1,0)],'awning canvas',f.label+'/sloping shop awning')


def portal(f,lod):
    # Real opening and a backstop far behind the lattice avoid flattening the entry to a painted rectangle.
    for sign in [-1,1]:
        u=sign*1.30
        f.box(u,2.45,.48,4.88,.50,.14,'granite','carved portal jamb')
        panel_border(f,u,2.57,.37,4.54,.406,'portal jamb incised border')
        for k in range(2 if lod else 6):
            n=2 if lod else 6;z=.42+(k+.5)*4.24/n
            for direction in [-1,1]:
                pts=[(u+direction*.16,z-.16,.425),(u+direction*.035,z-.16,.425),(u+direction*.035,z+.035,.425),(u+direction*.118,z+.035,.425),(u+direction*.118,z+.145,.425)]
                f.builder.tube([f.point(*q)for q in pts],.027,'relief granite',5,f.label+'/interlocking jamb fretwork')
        f.box(u,2.98,.095,.63,.104,.49,'blue lamp glass','blue vertical lamp')
        for z in [2.63,3.34]:f.box(u,z,.157,.066,.15,.47,'bronze window frame','lamp caps')
    f.box(0,4.62,3.10,.43,.54,.13,'granite','inscribed lintel')
    f.box(0,4.62,2.10,.30,.10,.442,'relief granite','inscription tablet')
    add_facade_lettering(f,'中華基督教女青年會全國協會'[::-1],0,4.62,1.99,.179,.503,.535,'portal timber',label='right-to-left inscription',font=HERE/'fonts/YuanmingyuanPortalSubset.otf')
    # Stepped Chinese scrolls at each side of the small tiled roof.
    for side in [-1,1]:
        for j in range(3):
            x=side*(1.34-.20*j);z=4.95+j*.15
            f.box(x,z,.36,.25,.32,.18,'granite','stepped portal shoulder')
            f.box(x,z+.04,.20,.045,.08,.374,'relief granite','scroll recess bars')
    f.box(0,5.145,2.15,.16,.67,.20,'granite','small eave beam')
    for i in range(11 if lod else 19):
        n=11 if lod else 19;u=(i-(n-1)/2)*2.09/n
        f.builder.tube([f.point(u,5.30,-.02),f.point(u,5.12,.64)],.061,'glazed tile',8 if lod else 14,f.label+'/round glazed roof tiles')
    entrance=opening(0,.17,2.18,4.19)
    f.prism(entrance,-1.08,-1.04,'interior shadow','deep entrance backstop')
    f.box(0,1.995,2.09,3.55,.09,-.91,'portal timber','recessed wooden entrance')
    upper=box(-1.065,3.42,1.065,4.26)
    f.prism(upper,-.19,-.14,'interior shadow','lattice transom background')
    for x in [-1.06,-.355,.355,1.06]:f.box(x,3.83,.072,.84,.15,.005,'portal timber','three transom lights')
    for z in [3.43,4.23]:f.box(0,z,2.20,.09,.15,.005,'portal timber','transom frame')
    for cx in [-.71,0,.71]:
        for s in [-1,1]:
            for j in [-1,0,1]:
                line_start=cx+j*.24
                a=np.array([line_start-.40,3.43]);b=np.array([line_start+.40,4.23])
                if s<0:a[1],b[1]=b[1],a[1]
                from shapely.geometry import LineString
                cut=LineString([a,b]).intersection(box(cx-.30,3.47,cx+.30,4.19))
                if cut.geom_type=='LineString' and cut.length>.04:
                    f.builder.tube([f.point(t,z,.025)for t,z in cut.coords],.022,'portal timber',5,f.label+'/repeated diamond lattice')
    f.box(0,.124,2.11,.24,.54,-.33,'granite','entrance threshold')


def elevation(f,xs,lod,main=False):
    apertures=[];sashes=[]
    for j,x in enumerate(xs):
        is_center=main and j==3
        width=(3.13 if j in (0,6) and main else 2.03) if not is_center else 2.44
        if is_center:apertures.append(opening(x,.12,2.19,4.25))
        else:
            g=opening(x,.79,width,3.10);apertures.append(g);sashes.append((g,3,2))
        for z in FLOORS:
            g=opening(x,z,width,2.29)
            apertures.append(g);sashes.append((g,3 if is_center or (main and j in (0,6)) else 2,2))
    f.wall(.12,24.06,apertures,thickness=.49,material='brick')
    for j,x in enumerate(xs):
        centre=main and j==3
        w=3.13 if main and j in (0,6)else (2.44 if centre else 2.03)
        # Stone spandrels and reveals sit between uninterrupted pale brick piers.
        strip=box(x-w*.59,.75,x+w*.59,23.62)
        f.prism(strip.difference(unary_union(apertures)),-.025,.065,'granite','granite window strips')
        if not centre:
            shop_awning(f,x,w+.41)
            patterned_panel(f,x,4.60,w+.12,.53,lod)
        else:portal(f,lod)
        for z in FLOORS[1:]:
            if centre:patterned_panel(f,x,z-.68,w-.12,.82,lod)
            elif not lod:
                for side in [-1,1]:f.box(x+side*w*.29,z-.54,.049,.65,.11,.08,'relief granite','vertical spandrel divisions')
    for g,cols,rows in sashes:f.window(g,cols,rows,trim=False,label='dark framed sash')
    plinth(f,doorway=main)
    # Cast a restrained shadow at the roof edge; the street-facing parapet is shallow and stepped.
    f.beam(24.03,.12,.12,material='granite',label='stone parapet cap')
    if main:
        for x in [-14.56,-9.54,-5.22,-1.74,1.74,5.22,9.54,14.56]:
            for j in range(6 if lod else 12):
                z=23.73+(j%3)*.085
                u=x+((j//3)-(.5 if lod else 1.5))*.094
                f.box(u,z,.073,.077,.075,.05,'brick variation','brick crown relief')
        # The Southeast corner foundation plaque is recorded in the architectural literature.
        f.box(-f.length/2+.43,.96,.67,.32,.12,.14,'granite','southeast foundation stone')


def stepped_floor(b,left,right,y,front_z,top,count,label,lod):
    rear=12
    for edge,name in [(((left,y),(right,y)),'east'),(((right,y),(right,rear)),'north side'),(((left,rear),(left,y)),'south return')]:
        f=Facade(b,*edge,label+' '+name)
        n=count if name=='east'else max(1,round((rear-y)/3.1))
        spacing=f.length/n
        windows=[opening((i+.5-n/2)*spacing,front_z+.48,spacing*.51,top-front_z-1.02)for i in range(n)]
        f.wall(front_z,top,windows,material='brick')
        for h in windows:f.window(h,2,2,trim=False,label='setback-floor sash')
        f.beam(top,.14,.14,material='granite',label='setback parapet')
    p=box(left,y,right,rear);b.plan_prism(p,top-.12,top,'roof membrane',label+'/flat top')
    rear_face=Facade(b,(right,rear),(left,rear),label+' section');rear_face.wall(front_z,top,[],thickness=.15,material='brick')


def assemble(b,lod):
    a,c,d,e=P['study_uv_m']
    front=Facade(b,a,c,'Yuanmingyuan Road')
    elevation(front,XS,lod,True)
    side=Facade(b,e,a,'South passage')
    elevation(side,[-3.84,0,3.84],lod)
    # The north edge meets a separate building; avoid adding invented party-wall windows.
    north=Facade(b,c,d,'North party wall');north.wall(.13,24.03,[],thickness=.20,material='brick')
    rear=Facade(b,d,e,'Western cut');rear.wall(.13,24.03,[],thickness=.18,material='brick')
    shape=Polygon(P['study_uv_m'])
    b.plan_prism(shape,0,.17,'granite','Front study/footing')
    b.plan_prism(shape,23.91,24.04,'roof membrane','Front study/street parapet roof')
    stepped_floor(b,-10.28,10.28,2.67,24.05,26.88,6,'7F setback',lod)
    stepped_floor(b,-3.85,3.85,4.43,26.89,29.37,3,'8F central block',lod)
    b.tube([(1.18,3.53,24.10),(1.18,3.53,31.10)],.045,'bronze window frame',6 if lod else 10,'Roof/flagstaff')


if __name__=='__main__':
    from final_preview import finish
    build(HERE,META,PAL,assemble)
    finish()
