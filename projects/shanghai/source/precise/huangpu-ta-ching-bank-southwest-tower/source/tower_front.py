"""Exterior faces of the restored low southwest corner of the Ta-Ching Government Bank."""
from math import pi, sin, cos, sqrt
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade, opening

BRICK='restored red facing brick'
STONE='carved pale stone'
BASE='reddish rusticated base'
GLASS='recessed dark glazing'
FRAME='dark timber sashes'
COPPER='oxidised copper'
SEAM='dark patinated seams'
ROOF='neutral roof closure'
PALETTE={BRICK:{'color':[1,1,1],'roughness':.9,'texture':str(Path(__file__).with_name('bond.png'))},
         STONE:{'color':[.76,.71,.62],'roughness':.82},BASE:{'color':[.49,.245,.157],'roughness':.89},
         GLASS:{'color':[.175,.225,.235],'roughness':.26},FRAME:{'color':[.22,.132,.09],'roughness':.65},
         COPPER:{'color':[.32,.49,.40],'metallic':.38,'roughness':.62},SEAM:{'color':[.19,.33,.28],'metallic':.38,'roughness':.66},
         ROOF:{'color':[.33,.31,.28],'roughness':.83}}
# The southwest chamfer measures 5.3243 m in the frozen source polygon.
APOTHEM=2.66215
HALF_FACE=APOTHEM*(sqrt(2)-1)
CENTRE_Y=HALF_FACE
WEST_DIR=np.array([-.5275,.84955])
EAST_DIR=np.array([.84201,.53946])
LEFT=np.array([-APOTHEM,0.])
RIGHT=np.array([APOTHEM,0.])
PATH=[LEFT+WEST_DIR*3.65,LEFT,np.array([-HALF_FACE,CENTRE_Y-APOTHEM]),np.array([HALF_FACE,CENTRE_Y-APOTHEM]),RIGHT,RIGHT+EAST_DIR*3.65]
NAMES=['West return','West facet','Central facet','East facet','South return']


def brick_uv(x,y,z):
    point=np.array([x,y]);travel=0.;best=(float('inf'),0.)
    for a,b in zip(PATH,PATH[1:]):
        segment=b-a;length=np.linalg.norm(segment);t=max(0.,min(1.,np.dot(point-a,segment)/length**2))
        distance=np.linalg.norm(point-(a+t*segment))
        if distance<best[0]:best=(distance,travel+t*length)
        travel+=length
    return best[1]/1.92,-z/.52


def pane(front, hole, tier, lod):
    front.window(hole,columns=2,rows=2 if lod else 3,frame=FRAME,glass=GLASS,trim=False,label=tier)
    x0,z0,x1,z1=hole.bounds
    outside=hole.buffer(.10,join_style=2).difference(hole)
    front.prism(outside,-.025,.09,STONE,tier+' facing')
    if tier=='Lower upper sash':
        e=x1+.20
        pediment=Polygon([(-e,z1+.14),(0,z1+.62),(e,z1+.14)])
        inner=Polygon([(-e+.20,z1+.23),(0,z1+.51),(e-.20,z1+.23)])
        front.prism(pediment,-.02,.115,STONE,'Triangular pediment backing')
        front.prism(pediment.difference(inner),.115,.235,STONE,'Raised pediment edges')
        front.box(0,z1+.12,2*e+.13,.12,.57,.13,STONE,'Pediment cornice')
    elif tier=='Middle sash':
        front.box(0,z1+.105,x1-x0+.24,.14,.34,.06,STONE,'Plain middle window head')


def facade_face(builder, i, lod):
    side=Facade(builder,PATH[i],PATH[i+1],NAMES[i]);facet=0<i<4
    hw=side.length/2
    holes=[]
    width = 1.21 if facet else 1.65
    if i in (1,3):
        bottom=box(-width/2,.29,width/2,3.75)
    else:
        bottom=opening(0,.29,width,3.74,.64 if facet else .73,16 if lod else 30)
    holes.append(bottom);pane(side,bottom,'Ground opening',lod)
    side.wall(0,4.67,[bottom],.50,BASE)
    for z in np.arange(.50,4.54,.335):
        joint=box(-hw,z,hw,z+.026).difference(bottom.buffer(.065))
        side.prism(joint,.005,.016,FRAME,'Ground masonry joints')
    widths=(1.15,1.08,1.20) if facet else (1.54,1.50,1.40)
    holes=[]
    for (z0,z1,tier),width in zip([(5.28,8.10,'Lower upper sash'),(9.54,12.15,'Middle sash'),(13.46,15.83,'Attic window')],widths):
        cut=box(-width*.5,z0,width*.5,z1);holes.append(cut);pane(side,cut,tier,lod)
    side.wall(4.67,16.55,holes,.50,BRICK)
    side.box(0,.19,side.length,.38,.49,-.10,STONE,'Street plinth')
    for z,height,depth in [(4.64,.20,.55),(4.85,.12,.45),(8.78,.145,.29),(12.74,.15,.48),(12.94,.105,.58),(16.15,.23,.46),(16.44,.17,.69)]:
        side.box(0,z,side.length+.045,height,depth,.055,STONE,'Floor and cornice bands')
    if facet:
        for x in np.linspace(-hw+.13,hw-.13,9):
            side.box(x,16.30,.105,.135,.37,.15,STONE,'Dentils below the dome')
        for x in (-hw+.22,hw-.22):
            side.box(x,8.25,.22,.21,.31,.105,STONE,'Lower window console caps')
        side.box(0,12.56,side.length,.19,.29,.055,STONE,'Continuous dentil bed')
        for x in np.linspace(-hw+.14,hw-.14,7):
            side.box(x,12.58,.105,.17,.30,.15,STONE,'Individual dentils')
        # Short second-floor colonnettes flank the three pedimented sashes.
        for x in (-.72,.72):
            p=side.point(x,0,.14)
            builder.lathe(tuple(p[:2]),[(5.08,.105),(5.15,.128),(5.22,.091),(7.98,.081),(8.04,.111),(8.10,.124)],STONE,12 if lod else 20,'Lower paired colonnettes')
        # The taller facade edges are light quoins along the first two window tiers.
        for x in (-hw+.063,hw-.063):
            side.box(x,8.70,.13,7.52,.22,.055,STONE,'Narrow tower edge bands')
    else:
        side.box(0,15.94,side.length+.04,.215,.52,.15,STONE,'First bay projecting head')
        for x in (-hw+.19,hw-.19):
            side.box(x,10.41,.31,11.20,.34,.06,BRICK,'Return wall piers')
            if (i==0 and x>0) or (i==4 and x<0):
                for z in np.arange(5.16,12.47,.64):
                    side.box(x,z,.36,.082,.35,.071,STONE,'Alternating return pier bands')


def top(builder,lod):
    sides=48 if lod else 80;cy=CENTRE_Y
    # A radius of 2.88 m encloses the octagonal upper body.
    radius=APOTHEM/cos(pi/8)
    octagon=Polygon([(radius*cos(pi/8+i*pi/4),cy+radius*sin(pi/8+i*pi/4))for i in range(8)])
    # The other five sides make a plain, closed return to the retained height.
    # Only the three photographed street sides receive openings and ornament.
    vertices=list(octagon.exterior.coords)
    for i,(a,b) in enumerate(zip(vertices,vertices[1:])):
        if (a[1]+b[1])/2 < .05:continue
        rear=Facade(builder,a,b,'Plain drum return');rear.wall(12.66,16.56,thickness=.3,material=ROOF)
    builder.plan_prism(octagon.buffer(.18,join_style=2),16.48,16.66,STONE,'Octagonal upper cornice')
    builder.plan_prism(octagon.buffer(.08,join_style=2),16.66,16.94,STONE,'Low octagonal drum')
    for point in PATH[1:-1]:
        x,y=point
        builder.lathe((x,y),[(13.03,.17),(13.12,.21),(13.22,.152)],STONE,14 if lod else 24,'Pale feet of upper brick supports')
        builder.lathe((x,y),[(13.215,.147),(15.80,.135)],BRICK,14 if lod else 24,'Upper exposed brick shafts')
        builder.lathe((x,y),[(15.79,.137),(15.87,.149),(15.94,.19),(16.03,.205)],STONE,14 if lod else 24,'Upper stone capitals')
    builder.lathe((0,cy),[(16.89,2.65),(17.00,2.73),(17.11,2.72),(17.23,2.65)],STONE,sides,'Circular cap bed')
    rise=.97;base=17.20;bulge=2.72;steps=9 if lod else 17
    def surface(t):return base+rise*sin(t),max(.012,bulge*cos(t))
    builder.lathe((0,cy),[surface(k*pi/(2*steps))for k in range(steps+1)],COPPER,sides,'Low copper dome')
    for j in range(16 if lod else 24):
        a=2*pi*j/(16 if lod else 24);pts=[]
        for k in range(steps+1):
            z,r=surface(k*1.45/steps);pts.append((r*cos(a),cy+r*sin(a),z+.012))
        builder.tube(pts,.022,SEAM,5 if lod else 8,'Copper standing seams')
    builder.lathe((0,cy),[(18.14,.084),(18.27,.08),(18.31,.028),(19.35,.024)],SEAM,12,'Slender crown rod')
    # The top of the cut-off street returns closes at the former cornice.
    for idx in (0,4):
        a,b=PATH[idx:idx+2];d=b-a;normal=np.array([-d[1],d[0]])/np.linalg.norm(d)
        roof=Polygon([a,b,b+.65*normal,a+.65*normal]);builder.plan_prism(roof,16.48,16.57,ROOF,'Return roof cap')


def add_building(builder,lod):
    from repeat import repeat_only_texture
    repeat_only_texture(builder,'bond.png')
    for i in range(5):facade_face(builder,i,lod)
    top(builder,lod)
    for part in builder.parts:
        if part['material']==BRICK:part['texcoords']=[brick_uv(*v)for v in part['vertices']]
