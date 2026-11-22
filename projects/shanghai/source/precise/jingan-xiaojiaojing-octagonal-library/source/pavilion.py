"""Octagonal courtyard library at 1321 Xinzha Road. All surfaces are original."""
from math import cos, sin, pi, sqrt, atan2
import os
import sys
from pathlib import Path
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
SOURCE=Path(__file__).resolve().parent
PROJECT=Path(os.environ.get('SHANGHAI_PROJECT_ROOT', SOURCE.parents[3]))
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
from photo_architecture import Facade
from render_finish import ATLAS, plaster_uv

PLASTER='ochre lime render'
TRIM='pale green window surround'
GLAZE='deep green glazed roof tiles'
SHADOW='dark space below eaves'
WOOD='painted dark timber'
GLASS='recessed blue grey glass'
CLAY='aged buff ridge joint'
TILE='patinated green tile drip'
STONE='grey stone threshold'
OCHRE='muted light ochre panel'
DOOR='weathered blue green door'
PALETTE={key:{'color':list(color),'roughness':rough,'metallic':0} for key,color,rough in [
 (PLASTER,(.76,.666,.493),.92),(TRIM,(.57,.631,.488),.84),(GLAZE,(.182,.294,.241),.48),
 (SHADOW,(.157,.161,.137),.88),(WOOD,(.239,.226,.179),.84),(GLASS,(.28,.352,.365),.30),
 (CLAY,(.62,.575,.409),.75),(TILE,(.247,.401,.323),.41),(STONE,(.51,.50,.443),.9),
 (OCHRE,(.68,.602,.434),.89),(DOOR,(.254,.366,.318),.80)]}
PALETTE[PLASTER].update(color=[1.,1.,1.],texture=str(ATLAS))

# 214 square metres on two floors; an octagon of this apothem has 107 square metres.
APOTHEM=5.68244
WALL_R=APOTHEM/cos(pi/8)
UPPER_R=7.374
LOWER_R=7.28

def ring(radius):
    return [(radius*cos(-5*pi/8+i*pi/4),radius*sin(-5*pi/8+i*pi/4)) for i in range(8)]

def mul(a,s):return tuple(v*s for v in a)
def point(a,b,t):return tuple(x+(y-x)*t for x,y in zip(a,b))

def roof_height(radius, apex_radius, rim_radius, apex, rim, fraction):
    # The ridge tips rise above the middle of each eave, especially on the skirt.
    r=(radius-apex_radius)/(rim_radius-apex_radius)
    sag=.26 if apex_radius<1 else .13
    lift=.15 if apex_radius<1 else .31
    return apex+(rim-apex)*r-sag*4*r*(1-r)+lift*(abs(2*fraction-1)**3)*r*r

def facet_point(a,b,f,r,r_outer,z):
    xy=mul(point(a,b,f),r/r_outer)
    return (*xy,z)

def roof(builder,upper,lod):
    outer=UPPER_R if upper else LOWER_R
    inner=.13 if upper else WALL_R-.08
    apex=10.97 if upper else 4.63
    edge=8.21 if upper else 3.70
    parts=ring(outer);rows=5 if lod else 9
    cylinders=13 if lod else 23
    prefix='upper' if upper else 'lower'
    def height(r,f):return roof_height(r,inner,outer,apex,edge,f)
    for i,(a,b) in enumerate(zip(parts,parts[1:]+parts[:1])):
        label=f'{prefix}.{i+1}'
        def sample(r,f,offset=0):
            return facet_point(a,b,f,r,outer,height(r,f)+offset)
        # Continuous, faceted backing and lip have an underside at each free edge.
        verts=[];faces=[]
        lanes=8
        for k in range(rows+1):
            r=inner+(outer-inner)*k/rows
            for j in range(lanes+1):verts.append(sample(r,j/lanes))
        for k in range(rows):
            for j in range(lanes):
                q=k*(lanes+1)+j
                faces.append((q,q+lanes+1,q+lanes+2,q+1))
        builder.add(verts,faces,GLAZE,label+'.cover')
        edge_vertices=[];quads=[]
        for j in range(lanes+1):
            f=j/lanes
            edge_vertices.extend([sample(outer,f),sample(outer,f,-.16),sample(outer-.78,f,-.19)])
        for j in range(lanes):
            k=j*3;quads.extend([(k,k+1,k+4,k+3),(k+1,k+2,k+5,k+4)])
        builder.add(edge_vertices,quads,WOOD,label+'.eave.and.soffit')
        # Raised convex tile channels taper inwards on this pitched plane. Alternate
        # curved cap tiles and flat pan troughs are visible in the eave detail photograph.
        verts=[];faces=[];sections=4 if lod else 6
        for j in range(cylinders):
            f=(j+.5)/cylinders
            off=.295/cylinders
            origin=len(verts)
            for k in range(rows+1):
                r=inner+(outer-inner)*k/rows
                for v in range(sections+1):
                    ang=pi*v/sections
                    verts.append(sample(r,f-cos(ang)*off,.009+sin(ang)*(.015+.067*r/outer)))
            for k in range(rows):
                for v in range(sections):
                    q=origin+k*(sections+1)+v
                    faces.append((q,q+sections+1,q+sections+2,q+1))
        builder.add(verts,faces,GLAZE,label+'.cap.tile.rows')
        # Hip crest follows the flown tip. The profile is broad at its foot.
        ridge=[sample(inner+(outer-inner)*k/rows,0,.103) for k in range(rows+1)]
        builder.tube(ridge,.094 if upper else .085,TILE,6 if lod else 10,label+'.hip')
        fdim=Facade(builder,a,b,label+'.terminals')
        for j in range(cylinders):
            f=(j+.5)/cylinders;u=fdim.length*(f-.5);z=height(outer,f)
            pitch=fdim.length/cylinders
            # A round green face caps the convex tile; the pointed drip belongs
            # to the intervening trough. They alternate in the published close-up.
            half=min(pitch*.39,.108)
            outline=[(u+half*cos(2*pi*t/12),z+.002+half*sin(2*pi*t/12)) for t in range(12)]
            fdim.prism(Polygon(outline),.012,.052,TILE,'round.terminal')
            if not lod:
                for side in (-1,1):
                    fdim.box(u+side*half*.4,z+.016,half*.27,.025,.023,.056,GLAZE,'mask.eyes')
                fdim.box(u,z-.013,half*.5,.03,.035,.067,CLAY,'mask.snout')
            mid=u+pitch*.49
            nose=[(mid-pitch*.24,z-.015),(mid+pitch*.24,z-.015),(mid+pitch*.20,z-.079),
                  (mid,z-.159),(mid-pitch*.20,z-.079)]
            fdim.prism(Polygon(nose),.010,.042,TILE,'leaf.drip')
        if not upper:
            # Stepped bracket arms between vertical posts and the lower overhang.
            wall=ring(WALL_R);front=Facade(builder,wall[i],wall[(i+1)%8],label+'.dougong')
            for station in (-.38,-.18,0,.18,.38):
                u=station*front.length
                front.box(u,3.20,.18,.17,.31,.10,WOOD,'bearing.block')
                front.box(u,3.35,.34,.12,.46,.18,WOOD,'crossarm')
                front.box(u,3.47,.51,.105,.65,.255,WOOD,'upper.arm')
                front.box(u,3.56,.18,.10,.71,.30,SHADOW,'rafter.seat')

def cloud_panel(face,z,w,lod):
    # Only a generalized ruyi outline is recoverable under the rail and vegetation.
    steps=7 if lod else 12
    def arc(center,rad,start,end):
        return [(center[0]+rad*cos(start+(end-start)*i/steps),center[1]+rad*sin(start+(end-start)*i/steps),.027) for i in range(steps+1)]
    for sign in (-1,1):
        points=arc((sign*w*.27,z),w*.087,0,pi)
        face.builder.tube([face.point(x,y,d)for x,y,d in points],.017,TRIM,6,face.label+'/ruyi.band')
    face.line((-.38*w,z,.024),(-.185*w,z,.024),.014,TRIM,6,'pattern.stem')
    face.line((.185*w,z,.024),(.38*w,z,.024),.014,TRIM,6,'pattern.stem')

def sash(face,z,w,h,cols,rows,name,lod):
    opening=box(-w/2,z,w/2,z+h)
    face.prism(opening,-.183,-.17,GLASS,name+'.glass')
    frame=opening.difference(opening.buffer(-.058,join_style=2))
    bars=[]
    for j in range(1,cols):
        x=-w/2+w*j/cols;bars.append(box(x-.018,z,x+.018,z+h))
    for j in range(1,rows):
        hbar=z+h*j/rows;bars.append(box(-w/2,hbar-.019,w/2,hbar+.019))
    face.prism(unary_union([frame,*bars]),-.131,-.082,WOOD,name+'.timber.sash')
    face.prism(opening.buffer(.061,join_style=2).difference(opening),-.014,.041,TRIM,name+'.border')
    return opening

def wall(builder,lod):
    corners=ring(WALL_R)
    builder.plan_prism(Polygon(corners),0,.31,STONE,'pavilion.plinth')
    for i,(a,b) in enumerate(zip(corners,corners[1:]+corners[:1])):
        f=Facade(builder,a,b,'side.'+str(i+1));holes=[]
        for z,w,h,rows in [(5.05,1.79,1.94,3),(7.32,1.73,.65,1)]:
            holes.append(sash(f,z,w,h,3,rows,'upper.casement' if rows>1 else 'transom',lod))
        f.box(0,4.98,2.01,.09,.16,.032,TRIM,'window.sill')
        cloud_panel(f,7.135,1.83,lod)
        if i==0:
            width,base,top=2.57,.44,3.33
            portal=box(-width/2,base,width/2,top)
            holes.append(portal)
            f.prism(portal.buffer(.12,join_style=2).difference(portal),-.02,.065,TRIM,'stone.door.surround')
            half=width*.5
            for j,material in enumerate((DOOR,OCHRE)):
                u=(j-.5)*half
                f.box(u,1.50,half-.035,2.11,.09,-.12,material,'courtyard.door')
                for v in (.94,1.8):
                    f.box(u,v,half-.24,.51,.045,-.059,material,'door.panel')
            top_light=box(-width/2,2.59,width/2,top)
            f.prism(top_light,-.16,-.12,GLASS,'door.transom.glass')
            for q in (-width/4,0,width/4):f.box(q,2.96,.039,.74,.08,-.08,WOOD,'door.transom.bar')
            f.box(0,2.59,width,.07,.09,-.08,WOOD,'door.lintel')
            for j in range(4):
                rise=(j+1)*.11
                f.box(0,rise/2,2.72,rise,.29,.99-j*.26,STONE,'courtyard.step')
        else:
            # Visible casements occupy the two adjacent facets; dense vegetation
            # screens the far ground storey in both photographs.
            if i in (1,7):holes.append(sash(f,1.22,1.29,1.28,2,2,'garden.casement',lod))
        f.wall(.31,8.23,holes,thickness=.29,material=PLASTER)
        f.box(0,.38,f.length,.14,.14,.02,STONE,'stone.base.course')

def add_geometry(builder,lod):
    wall(builder,lod)
    roof(builder,False,lod)
    roof(builder,True,lod)
    builder.lathe((0,0),[(10.90,.13),(11.0,.15),(11.08,.105),(11.17,.132),(11.28,.105),(11.37,.035),(11.42,.014)],TILE,12 if lod else 20,'small.glazed.finial')

    for part in builder.parts:
        if part['material']==PLASTER:
            part['texcoords']=[(u,1-v) for u,v in (plaster_uv(*point) for point in part['vertices'])]
