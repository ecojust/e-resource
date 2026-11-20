"""Model the river-facing exterior of Jardine Matheson at 27 The Bund."""
import json
import math
from pathlib import Path
import sys

import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
sys.path.insert(0, str(PROJECT / "tools"))
from package_architectural_model import build
from photo_architecture import Facade, opening

P = json.loads((HERE / "parameters.json").read_text())
PLAN = P["study_uv_m"]
WIDTH = P["width_m"]
META = {
    "id":P["id"], "name":"怡和洋行大楼临江立面与北京东路转角",
    "status":"photo-informed-partial-exterior",
    "scope":"Present riverfront exterior of the 1920–1922 Jardine Matheson Building, with its later upper storeys, cut at 11 m depth. West court and interiors excluded.",
    "model_scope_zh":"外滩27号东面九开间、花岗石拱券、四根跨层圆柱、东北斜角及后加楼层。西侧凹院、侧后翼及室内另计。",
    "source_register":"source/precise/"+P["id"]+"/reference-review.json",
    "viewer_page":"jardine-matheson.html", "audit_directory":"data/audit/jardine-matheson-v1/",
    "coordinate_convention":"GLB +X north along the facade (6.82 degrees), +Y up and +Z outward to the Bund (96.82 degrees).",
    "map_reference_license":"Registered footprint derived from OpenStreetMap / Overture Maps, ODbL-1.0.",
    "interiors_modeled":False,
}
PALETTE = {
    "limestone":{"color":[.57,.494,.406],"roughness":.85},
    "carved pale stone":{"color":[.65,.566,.461],"roughness":.76},
    "granite base":{"color":[.43,.382,.331],"roughness":.90},
    "granite courses":{"color":[.515,.453,.383],"roughness":.90},
    "attic stone":{"color":[.685,.623,.530],"roughness":.82},
    "roof zinc":{"color":[.26,.28,.27],"roughness":.81},
    "section":{"color":[.46,.428,.384],"roughness":.87},
    "lantern glass":{"color":[.76,.70,.50],"roughness":.31},
    "recessed glass":{"color":[.135,.171,.174],"roughness":.25,"metallic":.30},
    "bronze window frame":{"color":[.135,.122,.106],"roughness":.52,"metallic":.27},
}


def band(f, z, h, projection, label):
    f.beam(z,h,projection,label=label)


def rusticated_arcade(f, centres, width, lod):
    seg = 14 if lod else 28
    arches = [opening(x,.24,width,7.87,width*.49,seg) for x in centres]
    f.wall(.12,9.43,arches,thickness=.62,material="granite base")
    # Front relief follows each independent course and stops at the real arches.
    border=unary_union([p.buffer(.47,quad_segs=5) for p in arches])
    count=13 if lod else 15
    h=8.96/count
    for j in range(count):
        row=box(-f.length/2,j*h+.18,f.length/2,(j+1)*h+.11).difference(border)
        f.prism(row,-.03,.12 if j%2==0 else .155,"granite courses","split-face rustication")
    for x,arch in zip(centres,arches):
        f.window(arch,columns=2,rows=3,trim=False,label="recessed two-storey opening")
        # Dark transom separating the shop glazing below and the arch window above.
        for z,h in [(3.26,.15),(4.18,.64),(4.75,.14)]:
            f.box(x,z,width-.09,h,.13,-.085,"bronze window frame","deep shop transoms")
        r=width/2
        spring=.24+7.87-width*.49
        n=9 if lod else 15
        for j in range(n):
            a=j*math.pi/n+.012;b=(j+1)*math.pi/n-.012
            crown=.60 if j==n//2 else .45
            ring=[(x+rr*math.cos(t),spring+rr*math.sin(t)) for rr,t in [(r,a),(r,b),(r+crown,b),(r+crown,a)]]
            f.prism(Polygon(ring),-.015,.34 if j==n//2 else .23,"carved pale stone","radiating voussoirs")
        if not lod:
            for sign in [-1,1]:
                for j in range(10):
                    f.box(x+sign*(r+.22),.46+j*.59,.44,.53,.32,.055,"granite courses","rusticated arch jamb")
        f.box(x,.12,width+.45,.24,.66,.04,"granite base","granite sill")
    for z,h,depth in [(8.57,.19,.26),(9.05,.23,.39),(9.37,.19,.46)]:
        band(f,z,h,depth,"arcade string course")


def shaft(f, x, lod, slender=False):
    k=.82 if slender else 1
    cx,cy,_=f.point(x,0,.32)
    profile=[(9.48,.53),(9.61,.59),(9.74,.57),(9.82,.49),(9.91,.515),(10.04,.46),
             (10.22,.43),(12,.437),(17,.411),(20.97,.38),(21.10,.42),
             (21.22,.38),(21.46,.50),(21.80,.58),(21.97,.61)]
    f.builder.lathe((cx,cy),[(z,r*k) for z,r in profile],"carved pale stone",12 if lod else 24,f.label+"/column shaft, base and capital")
    for z,extent in [(9.48,1.30),(22.04,1.35),(22.20,1.42)]:
        f.box(x,z,extent*k,.18,extent*k,.32,"carved pale stone","square abacus and plinth")
    # Foliage massed from the silhouette. Individual capitals are not direct casts.
    if not lod:
        for j in range(8):
            phi=j*math.pi/4
            dx,dy=math.cos(phi),math.sin(phi)
            pts=[(cx+dx*.39*k,cy+dy*.39*k,21.26),
                 (cx+dx*.57*k,cy+dy*.57*k,21.55),
                 (cx+dx*.62*k,cy+dy*.62*k,21.78)]
            f.builder.tube(pts,.071*k,"carved pale stone",6,f.label+"/capital leaf tips")


def pavilion(f,x,pitch,lod):
    # Projecting second and eighth axes, including banded jambs and a recessed panel.
    for s in [-1,1]:
        u=x+s*.358*pitch
        f.box(u,15.86,.55,12.67,.38,.105,"limestone","pavilion pilaster")
        for j in range(12 if lod else 18):
            n=12 if lod else 18
            f.box(u,9.66+(j+.5)*12.3/n,.65,12.3/n-.07,.37,.17,"carved pale stone","pavilion quoin courses")
    for z in [13.78,18.38,22.01]:
        f.box(x,z,pitch*.76,.20,.63,.15,"carved pale stone","pavilion hood")
    for z in [14.18,18.78]:
        f.box(x,z,pitch*.60,.47,.18,.075,"carved pale stone","pavilion spandrel")
        f.box(x,z,pitch*.51,.33,.12,.21,"limestone","spandrel inset")


def middle(f, centres, pitch, lod, front=True):
    holes=[]
    for j,x in enumerate(centres):
        for z,h in [(9.86,2.92),(14.14,2.87),(18.79,2.30)]:
            w=pitch*(.56 if front else .43)
            holes.append(opening(x,z,w,h))
    f.wall(9.43,23.70,holes,material="limestone")
    for i,aperture in enumerate(holes):
        j=i//3;tier=i%3;x=centres[j]
        f.window(aperture,columns=2 if lod or not front else 3,rows=(2 if tier!=2 else 1),
                 trim=True,label="upper sash openings")
        if front and 2<=j<=6 and tier==0:
            w=pitch*.67
            triangle=Polygon([(x-w/2,13.04),(x+w/2,13.04),(x,13.84)])
            f.prism(triangle,-.045,.23,"carved pale stone","pediment above first gallery windows")
            if not lod:
                for s in [-1,1]:f.line((x,13.85,.26),(x+s*w*.51,13.01,.26),.075,"carved pale stone",7,"pediment slopes")
        if front and 2<=j<=6 and tier==1 and not lod:
            for s in [-1,1]:f.box(x+s*pitch*.26,17.24,.17,.40,.34,.08,"carved pale stone","window-console brackets")
    if front:
        for q in (-1.5,-.5,.5,1.5):shaft(f,q*pitch,lod)
        for j in (1,7):pavilion(f,centres[j],pitch,lod)
        for q in (-2.5,2.5):
            f.box(q*pitch,15.90,.63,12.76,.61,.11,"carved pale stone","end pilasters of central order")
        # Balustraded galleries before five central openings, with a solid rail and separate balusters.
        for x in centres[2:7]:
            f.box(x,9.95,pitch*.60,.15,.32,.33,"carved pale stone","gallery handrail")
            for k in range(5 if lod else 10):
                n=5 if lod else 10
                u=x+((k+.5)/n-.5)*pitch*.59
                f.box(u,9.71,.095,.40,.16,.33,"carved pale stone","gallery balusters")
    else:
        for s in [-1,1]:shaft(f,s*f.length*.31,lod,slender=True)
    for z,h,d in [(22.33,.23,.44),(22.72,.39,.53),(23.51,.25,.73),(23.86,.37,.90),(24.15,.23,1.06)]:
        band(f,z,h,d,"projecting classical entablature")
    n=max(4,round(f.length/(.86 if lod else .52)))
    for j in range(n):
        x=((j+.5)/n-.5)*f.length
        f.box(x,23.37,.19,.24,.61,.30,"carved pale stone","cornice dentils")


def attic(f, xs, pitch, lod, front=True):
    hs=[opening(x,z,pitch*ratio,height) for x in xs for z,ratio,height in [(24.73,.55,1.58),(27.77,.56,1.98)]]
    f.wall(24.16,31.63,hs,material="attic stone")
    for i,hole in enumerate(hs):
        f.window(hole,2 if lod else 3,1,trim=False,label="upper addition sashes")
        if i%2:
            x=xs[i//2]
            for d in [-1,1]:f.box(x+d*pitch*.36,28.84,.31,3.7,.22,.045,"attic stone","attic piers")
    for z,h,d in [(26.62,.25,.28),(27.12,.24,.33),(31.19,.19,.35),(31.61,.18,.45)]:
        band(f,z,h,d,"later attic bands")
    if front:
        for j in (1,7):
            x=xs[j]
            for z,w,h in [(26.69,1.03,.20),(30.85,1.12,.19),(31.69,1.14,.24)]:
                f.box(x,z,pitch*w,h,.67,.18,"carved pale stone","upper projecting end bays")


def crown(f,lod):
    # Current straight stepped attic screen. The old domed ornaments are visible only in the period photograph.
    plan=[(-8.8,31.54),(-8.2,31.99),(-7.86,32.60),(-7.6,33.0),(-7.6,34.87),(-3.3,34.87),
          (-3.3,35.77),(3.3,35.77),(3.3,34.87),(7.6,34.87),(7.6,33.0),(7.86,32.60),(8.2,31.99),(8.8,31.54)]
    f.prism(Polygon(plan),-.70,-.08,"attic stone","central stepped parapet")
    for x,w,z in [(-5.5,4.45,34.88),(5.5,4.45,34.88),(0,6.86,35.78)]:
        f.box(x,z+.04,w,.19,.83,-.32,"carved pale stone","parapet coping")
    for s in [-1,1]:
        x=s*5.49
        panel=opening(x,32.19,3.40,1.80)
        f.prism(panel.buffer(.12,join_style=2).difference(panel),-.10,.045,"carved pale stone","screen panel moulding")
        f.box(s*2.73,33.93,.37,2.72,.27,.01,"carved pale stone","central screen brackets")
    if not lod:
        for u in np.linspace(-2.3,2.3,18):
            f.box(u,35.46,.13,.13,.15,.055,"carved pale stone","attic dentils")


def assemble(b,lod):
    a,north,back_north,back_south,south=PLAN[4],PLAN[0],PLAN[1],PLAN[2],PLAN[3]
    # Each facade runs counterclockwise around the outward-facing evidence strip.
    front=Facade(b,south,a,"Riverfront")
    chamfer=Facade(b,a,north,"Northeast chamfer")
    length=front.length; pitch=length/9
    xs=[(k-4)*pitch for k in range(9)]
    rusticated_arcade(front,xs,pitch*.565,lod)
    # The central arch contains paired doors. The other eight ground bays have shopfront glazing.
    for sign in [-1,1]:
        front.box(sign*.60,1.57,1.17,2.67,.11,-.13,"bronze window frame","central paired door")
        front.box(sign*.60,1.81,.97,1.99,.07,-.042,"recessed glass","door leaf glass")
        front.box(sign*.15,1.37,.05,.50,.11,.01,"aged brass","door pulls")
        u=sign*pitch*.40
        front.line((u,4.06,.14),(u,4.38,.58),.055,"bronze window frame",6,"entrance lantern support")
        front.box(u,4.08,.30,.48,.27,.58,"lantern glass","paired entrance lamps")
        for z in [3.83,4.34]:
            front.box(u,z,.36,.064,.34,.58,"bronze window frame","lantern caps")
    middle(front,xs,pitch,lod)
    attic(front,xs,pitch,lod)
    crown(front,lod)
    # The post is visible in both modern front elevations; removable flags are excluded.
    flag=front.point(0,35.50,-.44)
    b.tube([flag,flag+[0,0,4.94]],.064,"bronze window frame",6 if lod else 10,"Attic/flagpole")
    # One real street-level north-east entrance on the diagonal and the paired colossal columns above.
    door=opening(0,.18,2.42,3.38)
    light=opening(0,4.22,2.60,3.64,1.28,14 if lod else 24)
    chamfer.wall(.12,9.43,[door,light],material="granite base")
    chamfer.window(door,2,1,trim=False,label="corner doorway")
    chamfer.window(light,2,2,trim=False,label="arched corner transom")
    for j in range(14):
        row=box(-chamfer.length/2,.18+j*.64,chamfer.length/2,.73+j*.64).difference(unary_union([door.buffer(.32),light.buffer(.26)]))
        chamfer.prism(row,-.04,.105,"granite courses","corner courses")
    middle(chamfer,[0],5.35,lod,False);attic(chamfer,[0],6.85,lod,False)
    for f in [Facade(b,north,back_north,"Beijing Road short return"),Facade(b,back_south,south,"South section return")]:
        f.wall(.12,9.43,[],material="granite base")
        f.wall(9.43,24.16,[],material="limestone")
        f.wall(24.16,31.64,[],material="attic stone")
        for z in [9.36,22.67,23.84,24.15,26.63,31.61]:
            band(f,z,.18,.32,"return to section")
    p=Polygon(PLAN)
    b.plan_prism(p,0,.17,"granite base","Section/footprint slab")
    b.plan_prism(p,31.35,31.58,"roof zinc","Section/upper covering")
    rear=Facade(b,back_north,back_south,"West section")
    rear.wall(.09,31.57,[],thickness=.16,material="section")


if __name__=="__main__":
    from final_preview import finish
    build(HERE,META,PALETTE,assemble)
    finish()
