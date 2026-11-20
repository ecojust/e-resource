"""Parametric reconstruction of the 51–59 Guangdong Road street facade."""
import json
import math
import sys
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
sys.path.insert(0,str(PROJECT/'tools'))
from package_architectural_model import build
from photo_architecture import Facade,opening

P=json.loads((HERE/'parameters.json').read_bytes())
META={'id':P['id'],'name':'大来大楼（广东路拱门与上层阳台）','status':'photo-informed-partial-exterior',
      'scope':'The long north-facing Robert Dollar Building elevation, including the nine splayed ashlar arches, steel sash pairs and the upper balcony.',
      'model_scope_zh':'广东路51、59号北偏西正面九孔拱门、折线石缝与卷饰檐带、上部成对钢窗和托座悬挑阳台。侧后栋及遮挡的屋面附属保留城市底图。',
      'viewer_page':'robert-dollar.html','audit_directory':'data/audit/robert-dollar-v1/',
      'coordinate_convention':'glTF X west-southwest along Guangdong Road, Y up, Z north-northwest toward the street.',
      'source_register':'source/precise/'+P['id']+'/reference-review.json','map_reference_license':'OpenStreetMap / Overture Maps, ODbL-1.0.','interiors_modeled':False}
PAL={'granite basement':{'color':[.273,.237,.205],'roughness':.91},'cut granite':{'color':[.470,.405,.345],'roughness':.87},
     'limestone':{'color':[.545,.513,.461],'roughness':.88},'light granite':{'color':[.559,.518,.463],'roughness':.9},
     'side stone':{'color':[.361,.342,.305],'roughness':.93},'carved pale stone':{'color':[.571,.535,.465],'roughness':.88},
     'bronze window frame':{'color':[.118,.126,.128],'metallic':.3,'roughness':.49},
     'recessed glass':{'color':[.144,.184,.201],'metallic':.29,'roughness':.33},'deep glass':{'color':[.095,.118,.107],'metallic':.27,'roughness':.34},
     'weathered iron':{'color':[.116,.121,.12],'metallic':.48,'roughness':.57},'street door':{'color':[.154,.145,.122],'roughness':.70},
     'roof':{'color':[.314,.302,.263],'roughness':.93}}
R=1.32
SPRING=2.55
PITCH=5.10
AXES=[k*PITCH for k in range(-4,5)]
WINDOW_ROWS=[(5.70,2.23),(9.25,2.10),(12.73,2.17),(16.26,2.11),(19.81,2.12),(23.31,2.18),(26.85,2.10)]


class GuangdongFront(Facade):
    def box(self,u,z,w,h,depth=.30,d=0,material='carved pale stone',label='trim'):
        # The ordinary historic sash has its own broad projecting sill. These
        # office windows sit in a nearly flush stone wall in the 2015 photo.
        if label=='recessed steel sash-sill':
            w-=.24
            h=.085
            depth=.16
            d=-.033
            material='light granite'
        super().box(u,z,w,h,depth,d,material,label)


def splayed_piers(f,arches,lod):
    holes=unary_union([s.buffer(.025)for s in arches])
    face=box(-f.length/2,.12,f.length/2,5.09).difference(holes)
    # Below the spring, the photograph shows straight, deeply rusticated joints.
    for lo,hi in zip([.14,.54,1.,1.47,1.94,2.38],[.505,.967,1.44,1.90,2.35,SPRING-.018]):
        f.prism(box(-f.length/2,lo,f.length/2,hi).intersection(face),-.035,.106,'cut granite','horizontal basement courses')
    # Each upper course rises away from the arch on its spring radii, then
    # levels across the pier. The resulting joints have a visibly stepped fan.
    for left in [AXES[0]-PITCH]+AXES:
        def edge(a):
            right=left+PITCH
            xi=R*math.cos(a);xo=(R+.73)*math.cos(a)
            inner=SPRING+R*math.sin(a);outer=SPRING+2.50*math.sin(a)
            return [(left+xi,inner),(left+xo,outer),(right-xo,outer),(right-xi,inner)]
        for k in range(8):
            a=k*math.pi/16+.006 if k else .006
            b=(k+1)*math.pi/16-.006
            strip=Polygon(edge(a)+edge(b)[::-1]).intersection(face)
            if not strip.is_empty:f.prism(strip,-.025,.132 if k%2 else .111,'cut granite','splayed arch joint bands')
    # Behind the fanlight, the ground entrances are recessed. The easternmost
    # and westernmost door types and the centre retain radiating ironwork.
    for i,(x,hole) in enumerate(zip(AXES,arches)):
        f.prism(hole.buffer(.008),-.366,-.344,'deep glass','arched street glazing')
        f.prism(hole.buffer(-.017).difference(hole.buffer(-.107)),-.30,-.15,'weathered iron','tall iron arch perimeter')
        for a,b in [(0,2.22),(-.61,1.72),(.61,1.72)]:
            f.box(x+a,1.22,.055,b,.14,-.215,'street door','door leaf stiles')
        f.box(x,2.30,2.49,.13,.14,-.20,'weathered iron','door and fanlight transom')
        for y in (.30,1.70):
            f.box(x,y,2.42,.092,.12,-.23,'street door','door leaf rails')
        if i in (0,4,8):
            for r in (.39,.76,1.12):
                pts=[f.point(x+r*math.cos(a),SPRING+r*math.sin(a),-.177)for a in np.linspace(0,math.pi,13 if lod else 27)]
                f.builder.tube(pts,.021,'weathered iron',5 if lod else 7,'Front/fanlight concentric arcs')
            for a in np.linspace(.22,math.pi-.22,7):
                f.line((x+.38*math.cos(a),SPRING+.38*math.sin(a),-.175),(x+1.18*math.cos(a),SPRING+1.18*math.sin(a),-.175),.022,'weathered iron',5,'fanlight rays')


def floor_band(f,lod):
    f.beam(5.12,.14,.28,'cut granite',label='top of basement')
    f.beam(5.35,.33,.22,'limestone',label='scroll-band backing')
    f.beam(5.56,.12,.30,'carved pale stone',label='scroll-band cornice')
    n=round(f.length/.49)
    for k in range(n):
        x=(k+.5-n/2)*f.length/n
        path=[]
        for t in np.linspace(0,1,10 if lod else 17):
            a=.25+1.63*math.pi*t;r=.115*(1-.83*t)
            path.append(f.point(x+r*math.cos(a),5.35+r*math.sin(a),.335))
        f.builder.tube(path,.022,'cut granite',5 if lod else 7,'Front/continuous curled frieze')


def balcony(f,lod):
    # Deep projecting platform carried by a central run of original shelf
    # brackets. Spacing and thickness derive from the 2015 oblique view.
    half=8.63;z=23.22
    f.box(0,z,2*half,.23,1.26,.38,'cut granite','central balcony deck')
    f.box(0,z+.115,2*half+.13,.10,1.31,.40,'light granite','balcony front edge')
    for u in np.linspace(-half+.33,half-.33,8):
        section=[(-.07,z-.14),(.99,z-.14),(.96,z-.40),(.67,z-.53),(.51,z-.82),(.21,z-.91),(-.07,z-.92)]
        # Extrude the bracket across its width in the local facade frame.
        poly=Polygon(section)
        f.builder.prism(poly,-.19,.19,lambda delta,height,t:f.point(u-t,height,delta),'cut granite','Front/eight balcony brackets')
        f.box(u,z-.97,.56,.15,.33,.10,'light granite','bracket base moulding')
    for x in (-half,half):
        f.line((x,z+.18,.97),(x,z+.95,.97),.042,'weathered iron',6,'balcony end newel')
        for hi in (.34,.91):f.line((x,z+hi,.07),(x,z+hi,.97),.032,'weathered iron',6,'balcony end rail')
    for hi in (.31,.88,.95):
        f.line((-half,z+hi,.98),(half,z+hi,.98),.033,'weathered iron',6,'balcony handrail')
    n=round(half*2/.31)
    for i in range(n+1):
        x=half*(2*i/n-1)
        f.line((x,z+.21,.98),(x,z+.91,.98),.024 if i%6 else .034,'weathered iron',5,'balcony vertical rods')


def assemble(b,lod):
    pts=np.array(P['study_uv_m'])
    front=GuangdongFront(b,pts[3],pts[2],'Guangdong Road')
    base=[opening(x,.135,2*R,SPRING+R-.135,R,18 if lod else 34)for x in AXES]
    front.wall(.12,5.12,base,.48,'granite basement')
    splayed_piers(front,base,lod);floor_band(front,lod)
    windows=[]
    for row,(z,h)in enumerate(WINDOW_ROWS):
        for i,x in enumerate(AXES):
            for side in (-1,1):
                u=x+side*(.91 if row<6 else .87)
                width=1.13 if row<6 else 1.02
                windows.append((row,i,u,opening(u,z,width,h)))
    front.wall(5.50,30.13,[s for *_,s in windows],.39,'limestone')
    for row,i,u,s in windows:
        front.window(s,2,3 if row!=6 else 2,trim=False,label='recessed steel sash')
        if row==0:
            # Low stone string runs between windows, interrupted at every reveal.
            x0,x1=s.bounds[0],s.bounds[2];centre=u-AXES[i]
            if centre>0:
                front.box(AXES[i],6.46,.65,.105,.19,.055,'light granite','paired window waist course')
        if row==6:
            front.box(u,s.bounds[3]+.09,1.45,.15,.26,.057,'light granite','upper window lintels')
    for lo,h,d in [(25.98,.1,.21),(26.16,.12,.29),(29.56,.17,.28),(29.82,.18,.43),(30.09,.22,.57),(30.36,.14,.41),(30.65,.18,.26)]:
        front.beam(lo,h,d,'light granite',label='upper architectural courses')
    for k in range(round(front.length/.50)):
        n=round(front.length/.50);u=(k+.5-n/2)*front.length/n
        front.box(u,29.98,.20,.16,.50,.12,'cut granite','small cornice blocks')
    balcony(front,lod)
    for label,a,e in [('West building boundary',pts[2],pts[1]),('Rear study cut',pts[1],pts[0]),('East building boundary',pts[0],pts[3])]:
        w=Facade(b,a,e,label);w.wall(.13,30.74,[],.18,'side stone')
    plan=Polygon(pts)
    b.plan_prism(plan,0,.175,'granite basement','Plan/arcade thresholds')
    b.plan_prism(plan,30.65,30.86,'roof','Plan/section roof')


if __name__=='__main__':
    from final_preview import finish
    build(HERE,META,PAL,assemble)
    finish()
