"""Build the west entrance block of Shanghai's former Oriental Hotel."""
import math, json, sys
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
sys.path.insert(0,str(PROJECT/'tools'))
from package_architectural_model import build
from photo_architecture import Facade,opening
from sign_lettering import add_facade_lettering

P=json.loads((HERE/'parameters.json').read_bytes())
ID=P['id']
META={'id':ID,'name':'东方饭店旧址（上海市工人文化宫西端主楼）','status':'photo-informed-partial-exterior',
      'scope':'The west entrance and first 19 m of the two street-facing returns of the 1929 Grand Oriental Hotel, in its present use as Shanghai Workers’ Cultural Palace.',
      'model_scope_zh':'西藏中路120号船首形主入口、西端三组跨层爱奥尼柱、转角券窗、阳台、1929铭牌和北海路、广东路两侧近段；五层副楼、后院和长翼余部单列。',
      'source_register':'source/precise/'+ID+'/reference-review.json','viewer_page':'oriental-hotel.html','audit_directory':'data/audit/oriental-hotel-v1/',
      'coordinate_convention':'glTF X to the right along the short main front, Y up, Z west-southwest towards Xizang Middle Road.',
      'inscription_font_license':'SIL Open Font License 1.1, Noto Serif CJK SC Regular subset','interiors_modeled':False,'map_reference_license':'OpenStreetMap / Overture Maps, ODbL-1.0.'}
PAL={'ashlar':{'color':[.442,.353,.273],'roughness':.90},'stone band':{'color':[.535,.443,.334],'roughness':.86},
     'limestone':{'color':[.686,.599,.447],'roughness':.87},'carved pale stone':{'color':[.774,.687,.525],'roughness':.79},
     'recessed glass':{'color':[.091,.116,.124],'roughness':.27,'metallic':.30},
     'balcony iron':{'color':[.126,.118,.106],'roughness':.57,'metallic':.38},
     'bronze window frame':{'color':[.143,.132,.109],'roughness':.56,'metallic':.24},
     'roof membrane':{'color':[.289,.265,.236],'roughness':.9},'roof tile':{'color':[.377,.214,.146],'roughness':.9},
     'letter bronze':{'color':[.556,.435,.243],'roughness':.54,'metallic':.42}}


def ground(f,main,flank,centre,lod):
    if main:
        holes=[opening(0,.07,4.28,5.64)]
    else:
        holes=[opening(c,.17 if flank else .56,(3.10 if flank else 2.30),7.15 if flank else 6.56,1.53 if flank else .97,
                       12 if lod else 24) for c in centre]
    f.wall(.07,8.51,holes,thickness=.56,material='ashlar')
    aperture=unary_union([s.buffer(.23)for s in holes])
    for j in range(10):
        row=box(-f.length/2,.11+j*.81,f.length/2,.84+j*.81).difference(aperture)
        f.prism(row,-.028,.079 if j%2 else .104,'stone band','rusticated base courses')
    for c,h in zip(centre,holes):
        f.window(h,columns=2 if main else 3,rows=3,trim=False,label='street door or glazing')
        if main:
            for sign in [-1,1]:
                x=sign*2.46
                f.box(x,3.22,.53,6.36,.43,.13,'limestone','rectangular entrance jamb')
                f.box(x,6.49,.78,.24,.54,.13,'carved pale stone','doorway shoulder')
            f.box(0,6.08,4.87,.41,.52,.14,'limestone','rectangular contemporary lintel')
            for sign in [-1,1]:f.box(sign*.15,1.53,.059,.61,.13,-.06,'letter bronze','entrance door pulls')
        else:
            ar=1.53 if flank else .97
            z=h.bounds[3]-ar
            w=(h.bounds[2]-h.bounds[0])/2
            n=9 if lod else 15
            for k in range(n):
                lo=k*math.pi/n+.01;hi=(k+1)*math.pi/n-.01
                out=.30 if k!=n//2 else .43
                shape=Polygon([(c+r*math.cos(a),z+v*math.sin(a))for r,v,a in [(w,ar,lo),(w,ar,hi),(w+out,ar+out,hi),(w+out,ar+out,lo)]])
                f.prism(shape,-.02,.16 if k!=n//2 else .235,'stone band','radial arch stones')
            f.box(c,4.02,2*w,.28,.16,-.10,'bronze window frame','street transom')
    for z,h,d in [(7.89,.22,.31),(8.37,.32,.40),(8.72,.18,.55),(8.86,.09,.61)]:
        f.beam(z,h,d,label='entrance entablature')
    if main:
        f.box(0,8.37,f.length-.14,.77,.25,.49,'carved pale stone','name frieze')
        add_facade_lettering(f,'上海市工人文化宫',0,8.36,7.56,.52,.622,.664,'letter bronze',label='cultural palace lettering',font=HERE/'fonts/OrientalSignSubset.otf')


def column(f,x,lod):
    yz=f.point(x,0,.36);cx,cy,_=yz
    profile=[(8.94,.54),(9.10,.54),(9.18,.48),(9.28,.494),(9.40,.439),(9.48,.451),
             (9.59,.403),(13.8,.388),(18.8,.368),(21.28,.356),(21.37,.39),(21.51,.415),(21.74,.442),(21.89,.47)]
    f.builder.lathe((cx,cy),profile,'carved pale stone',12 if lod else 24,f.label+'/giant Ionic shaft')
    for z,w,h in [(8.94,1.22,.25),(21.85,1.15,.17),(22.02,1.22,.17)]:
        f.box(x,z,w,h,w,.36,'carved pale stone','column base and abacus')
    # Ionic spirals are formed in the visible street plane on both front and back of the capital.
    for d in ([.70] if lod else [.63,.15]):
        for side in [-1,1]:
            u=x+side*.35;z=21.66
            pts=[]
            for j in range(13 if lod else 27):
                n=12 if lod else 26;t=j/n
                th=math.pi*.42+t*math.pi*2.4;r=.178*(1-.79*t)
                pts.append(f.point(u+side*r*math.cos(th),z+r*math.sin(th),d))
            f.builder.tube(pts,.052,'carved pale stone',6 if lod else 8,f.label+'/Ionic volutes')


def balcony(f,x,z,width,lod):
    f.box(x,z,width,.23,1.09,.35,'carved pale stone','balcony projecting floor')
    for side in [-1,1]:
        u=x+side*(width*.31)
        bracket=Polygon([(u-.12,z-.08),(u+.13,z-.08),(u+.10,z-.48),(u-.10,z-.61)])
        f.prism(bracket,-.04,.49,'stone band','balcony console')
    front=.82
    f.box(x,z+.76,width,.074,.075,front,'balcony iron','balcony cap rail')
    f.box(x,z+.20,width,.07,.063,front,'balcony iron','balcony lower rail')
    n=max(5,round(width/(.34 if lod else .20)))
    for i in range(n+1):
        u=x+(i/n-.5)*(width-.10)
        f.box(u,z+.46,.043,.62,.061,front,'balcony iron','iron rail uprights')
        if not lod and i<n and i%2==0:
            dx=width/n
            for a,c in [(0,.5),(.5,1)]:
                f.line((u+a*dx,z+.25 if a==0 else z+.66,front),(u+c*dx,z+.66 if c==.5 else z+.25,front),.019,'balcony iron',5,'balcony rail chevrons')
    for side in [-1,1]:
        u=x+side*width/2
        f.line((u,z+.76,.08),(u,z+.76,front),.044,'balcony iron',6,'balcony side rails')


def middle(f,xs,large,lod):
    zrows=[(9.03,3.24),(13.41,3.17),(17.72,3.18)]
    width=f.length*(.315 if large else .66/len(xs))
    holes=[opening(x,z,width,h) for x in xs for z,h in zrows]
    f.wall(8.80,22.50,holes,material='limestone')
    for idx,h in enumerate(holes):
        x=xs[idx//3];tier=idx%3
        f.window(h,3 if large else 2,2,trim=True,label='principal storey sash')
        if tier>0 or not large:balcony(f,x,zrows[tier][0]-.11,width+.57,lod)
        elif large:
            f.box(x,9.64,width+.50,.10,.16,.23,'balcony iron','low front rails')
            for j in range(10):f.box(x+(j-4.5)*width/10,9.33,.041,.58,.09,.23,'balcony iron','low rail bars')
    if large:
        for side in [-1,1]:
            column(f,side*f.length*.282,lod)
            x=side*(f.length/2-.42)
            f.box(x,15.49,.77,13.23,.28,.07,'carved pale stone','corner Ionic pilaster')
            for z,w,h in [(9.09,.91,.30),(21.65,.95,.18),(21.92,1.00,.26)]:
                f.box(x,z,w,h,.44,.105,'carved pale stone','pilaster collar')
        if not lod:
            for j in range(13):
                for side in [-1,1]:
                    f.box(side*(f.length/2-.42),9.3+j*.93,.74,.043,.10,.22,'stone band','pilaster course joints')
    for z,h,d in [(22.12,.23,.40),(22.46,.36,.56),(22.73,.15,.67)]:
        f.beam(z,h,d,label='Ionic entablature')


def top(f,xs,large,lod):
    for low,high,winz,winh in [(22.75,26.54,23.19,2.08),(26.84,29.19,27.02,1.39)]:
        centres=[-.278*f.length,0,.278*f.length] if large else xs
        width=.26*f.length if large else .74*f.length/len(xs)
        holes=[opening(x,winz,width,winh)for x in centres]
        f.wall(low,high,holes)
        for h in holes:f.window(h,2 if lod else 3,2,trim=False,label='upper ribbon sash')
    for z,h,d in [(25.73,.17,.38),(26.03,.39,.65),(26.34,.29,.85),(26.61,.30,1.03),
                  (26.81,.15,.77),(29.07,.22,.42),(29.34,.23,.62)]:
        f.beam(z,h,d,label='upper stone cornice')
    n=max(4,round(f.length/(1.03 if lod else .65)))
    for i in range(n):f.box(((i+.5)/n-.5)*f.length,25.85,.24,.28,.69,.40,'carved pale stone','dentil corbels')


def dated_crown(f,lod):
    f.box(0,30.50,7.62,2.45,.98,-.06,'limestone','1929 central attic screen')
    f.box(0,30.57,6.9,1.75,.27,.48,'carved pale stone','raised plaque')
    add_facade_lettering(f,'1929',0,30.56,4.02,.86,.63,.72,'stone band',label='relief numerals',font=HERE/'fonts/OrientalSignSubset.otf')
    for z,w,h,d in [(29.62,8.14,.26,1.28),(31.72,8.02,.23,1.27),(31.93,8.24,.18,1.44)]:
        f.box(0,z,w,h,d,-.03,'carved pale stone','crown cornice')
    for side in [-1,1]:
        u=side*4.39
        f.box(u,30.04,.85,1.29,.83,-.09,'limestone','attic shoulder')
        f.box(u,30.77,.99,.15,1.01,-.07,'carved pale stone','attic shoulder cap')
        if not lod:
            pts=[f.point(u+side*.34*math.cos(t),30.63+.29*math.sin(t),.34)for t in np.linspace(0,math.pi,12)]
            f.builder.tube(pts,.061,'carved pale stone',7,f.label+'/attic relief')
    origin=f.point(0,30.72,-1.38)
    f.builder.tube([origin,origin+[0,0,4.88]],.053,'bronze window frame',7 if lod else 10,'Attic/flag mast')


def assemble(b,lod):
    left,right,right_chamfer,cut_right,cut_left,left_chamfer=P['study_uv_m']
    faces=[(left,right,'Central west entrance',True,True),
           (right,right_chamfer,'Guangdong Road chamfer',True,False),(right_chamfer,cut_right,'Guangdong Road return',False,False),
           (cut_left,left_chamfer,'Beihai Road return',False,False),(left_chamfer,left,'Beihai Road chamfer',True,False)]
    for a,c,label,large,main in faces:
        f=Facade(b,a,c,label)
        xs=[0] if large else [-f.length*.25,f.length*.25]
        ground(f,main,large and not main,xs,lod);middle(f,xs,large,lod);top(f,xs,large,lod)
        if main:dated_crown(f,lod)
    plan=Polygon(P['study_uv_m']);b.plan_prism(plan,0,.16,'ashlar','Building/ground slab')
    b.plan_prism(plan,28.95,29.21,'roof membrane','Building/roof section')
    rear=Facade(b,cut_right,cut_left,'East section')
    rear.wall(.12,29.16,[],thickness=.18,material='limestone')
    # A small setback service block matches the mass behind the west attic seen in the aerial.
    short=plan.buffer(-2.48,join_style=2).intersection(box(-4,4.20,4,11.22))
    b.plan_prism(short,29.14,29.83,'stone band','Roof/setback western service volume')
    b.plan_prism(short.buffer(.12,join_style=2),29.80,29.94,'roof tile','Roof/setback covering')


if __name__=='__main__':
    from final_preview import finish
    build(HERE,META,PAL,assemble)
    finish()
