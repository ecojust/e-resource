"""Build the southern pair of entrances and balconies at Nos. 1 and 2 in Li-Bo Terrace."""
from math import cos, pi, sin
from pathlib import Path
import argparse
import json
import os
import sys

import numpy as np
from shapely.geometry import Polygon, box as rectangle

SOURCE = Path(__file__).resolve().parent
PROJECT = next(p for p in SOURCE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0, str(PROJECT/'tools'))
import package_architectural_model as package
sys.path.insert(0, str(PROJECT/'source/precise/huangpu-somekh-building-street-corner/source'))
from aggregate_mesh import AggregateBuilder
from photo_architecture import Facade
from roughcast import STONE, texture_coordinates

MODEL = 'xuhui-libo-terrace-one-two-balconies'
META = dict(id=MODEL, name='丽波花园南排一、二号分户双阳台', viewer_page='libo-terrace-one-two-balconies.html',
            heritage_group='4D027', heritage_address='衡山路300弄1、2号', status='documented-south-terrace-party-wall',
            scope='南排两户的上下双阳台、分户墙、三级窗门、黑铁栏、局部红瓦坡面。')
D = json.loads((SOURCE.parent/'measurements/southern-pair-dimensions.json').read_bytes())['model_parameters_m']
IRON = 'Aged black iron'
EDGE = 'Weathered iron edges'
SLAB = 'Pale cement balcony edges'
CHALK = 'Light rendered hood and door surround'
TIMBER = 'Grey green door frames'
DARK = 'Dark glass in shadow'
SKY = 'Cool reflected window glass'
SHADE = 'Shaded porch wall'
WOOD = 'Umber entrance doors'
CLAY = 'Oxide red clay roof'
TROUGH = 'Umber troughs below roof tiles'
TRIM = 'Brown timber eaves'
CAP = 'Pale caps of fire separation'
GREEN = 'Green awning cloth'
DRAIN = 'Grey metal downpipes'
def pigment(rgb,roughness=.82,metallic=0.):
    def linear(v):
        s=v/255
        return s/12.92 if s<.04045 else ((s+.055)/1.055)**2.4
    return dict(color=[linear(v)for v in rgb],roughness=roughness,metallic=metallic)
PALETTE={STONE:dict(color=[1,1,1],roughness=.96,texture=str(SOURCE/'green-grey-roughcast.png')),
         IRON:pigment((50,54,53),.66,.36),EDGE:pigment((70,71,65),.7,.27),
         SLAB:pigment((166,164,147)),CHALK:pigment((186,182,158)),TIMBER:pigment((93,104,92)),
         DARK:pigment((46,51,49),.35,.15),SKY:pigment((112,127,129),.35,.14),
         SHADE:pigment((107,104,86)),WOOD:pigment((77,70,56)),CLAY:pigment((161,95,73)),
         TROUGH:pigment((130,78,63)),TRIM:pigment((90,82,70)),CAP:pigment((193,191,169)),
         GREEN:pigment((95,137,124),.93),DRAIN:pigment((95,99,88),.63,.20)}


def shoulder(cx,sill,width,height,arched=False):
    left,right=cx-width/2,cx+width/2;top=sill+height
    if arched:
        arc=[(cx+width*.5*cos(i*pi/24),top-.25+.25*sin(i*pi/24))for i in range(25)]
        return Polygon([(left,sill),(right,sill),*arc])
    shoulder_height=min(.17,width*.13)
    return Polygon([(left,sill),(right,sill),(right,top-shoulder_height),(cx+.28*width,top),
                    (cx-.28*width,top),(left,top-shoulder_height)])

def ring(face,shape,width,near,far,material,label):
    outside=shape.buffer(width,join_style=2)
    face.prism(outside.difference(shape),far,near,material,label)

def draw_leaf(b,hinge,z0,w,h,angle,swing,glass,label,lod):
    along=np.array([cos(angle),swing*sin(angle),0.]);out=np.array([swing*sin(angle),-cos(angle),0.]);up=np.array([0.,0.,1.])
    # The two leaves rotate around their actual jambs, leaving a narrow view into the dark recess.
    pivot=np.array([*hinge,z0])
    def block(u,z,span,height,depth,normal,material,part):
        center=pivot+along*u+up*z+out*normal
        b.box(center,(span,depth,height),material,[along,out,up],label+'/'+part)
    block(w/2,h/2,w-.035,h-.045,.019,-.026,glass,'Glass')
    for u in (.019,w-.019):block(u,h/2,.038,h,.049,0,TIMBER,'Stiles')
    for z in (.023,h-.023):block(w/2,z,w-.076,.046,.046,0,TIMBER,'Head and bottom rail')
    block(w/2,h*.60,w-.076,.027,.038,.003,TIMBER,'Meeting glazing bar')

def balcony_door(b,face,cx,sill,height,level,side,lod):
    width=D['opening_width'];opening=shoulder(cx,sill,width,height);label=f'{level}/{side}'
    # The full dark return is one continuous solid from the rear plane to the front frame.
    inner=opening.buffer(-.046,join_style=2)
    face.prism(opening.difference(inner),-.31,-.073,TIMBER,label+'/Door reveal')
    face.prism(opening,-.324,-.309,DARK,label+'/Shaded interior')
    ring(face,opening,.059,.039,-.018,CHALK,label+'/Rendered surround')
    if level=='Upper pair':
        # Two short, inclined returns flank the flat centre of the projecting head.
        top=sill+height
        for reach,drop,back,front in ((width/2+.09,.065,.018,.112),(width/2+.14,.042,.106,.192)):
            middle=width*.27
            crown=[(cx-reach,top-.105),(cx-middle,top+.066),(cx+middle,top+.066),(cx+reach,top-.105)]
            profile=Polygon(crown+[(u,z+drop) for u,z in reversed(crown)])
            face.prism(profile,back,front,CHALK,label+'/Projecting clipped hood')
    head=sill+height;line=head-.39
    transom=inner.intersection(rectangle(cx-width, line, cx+width,head+.1))
    face.prism(transom,-.227,-.210,SKY,label+'/Clipped transom glass')
    face.box(cx,line,width-.085,.056,.073,-.092,TIMBER,label+'/Transom rail')
    face.box(cx,head-.22,.032,.33,.043,-.108,TIMBER,label+'/Transom mullion')
    span=(width-.095)/2;low=sill+.055
    for hand in (-1,1):
        hinge_x=cx+hand*(width/2-.052)
        opens=level=='Upper pair' and ((side<0 and hand>0) or (side>0 and hand<0))
        # In the high view both openings contain one narrow projecting casement.
        theta=pi*(.205 if opens else 0)
        direction=theta if hand<0 else pi-theta
        draw_leaf(b,(hinge_x,-.105),low,span,line-low-.035,direction,-1,
                  DARK if hand==side else SKY,label+('/West leaf' if hand<0 else '/East leaf'),lod)
    face.box(cx,sill+.026,width+.07,.052,.34,-.019,SLAB,label+'/Threshold')

def wire(b,path,r,lod,label,material=IRON):
    b.tube(path,r,material,4 if lod else 7,label)

def oval_band(b,face,left,bottom,width,height,mirrored,lod,label):
    frame_label=label.removeprefix(face.label+'/')
    for edge in (.025,.975):
        face.box(left+edge*width,bottom+height/2,.010,height,.016,.013,IRON,frame_label+'/Band uprights')
    for row in range(1,4):
        face.box(left+width/2,bottom+height*row/4,width,.011,.016,.013,IRON,frame_label+'/Band crossbars')
    for u,v in ((.72,.123),(.21,.365),(.62,.606),(.23,.854)):
        x=left+width*(1-u if mirrored else u);z=bottom+(1-v)*height
        for scale in ((1.,) if lod else (1.,.62)):
            radius=width*.214*scale
            straight=(height*.096-width*.214)*scale
            path=[]
            steps=5 if lod else 9
            for cap in (-1,1):
                for j in range(steps+1):
                    angle=(pi+j*pi/steps) if cap<0 else j*pi/steps
                    path.append(tuple(face.point(x+radius*cos(angle),z+cap*straight+radius*sin(angle),.025)))
            wire(b,path+[path[0]],.0055,lod,label+'/Nested oblongs')


def ornamental_cell(b,face,left,bottom,width,height,lod,label):
    frame_label=label.removeprefix(face.label+'/')
    # The ornament field occupies the space to the right of its narrow oblong band.
    def p(u,v,depth=.013):return tuple(face.point(left+u*width,bottom+(1-v)*height,depth))
    # The framing uprights span the opening and support both rectangular ornament panels.
    for u in (.286,.896):
        face.box(left+u*width,bottom+height/2,.010,height,.016,.013,IRON,frame_label+'/Continuous plaque uprights')
    for v in (0.,.5,1.):
        face.box(left+.5*width,bottom+(1-v)*height,width,.014,.018,.012,IRON,frame_label+'/Horizontal rails')
    for v,c in ((.25,.598),(.742,.594)):
        half_width=.098
        face.box(left+c*width,bottom+(1-v)*height,2*half_width*width,.232*height,.023,.022,IRON,frame_label+'/Square iron plaques')
        sw=.078*width;sh=.096*height
        wire(b,[tuple(face.point(left+c*width+u,bottom+(1-v)*height+z,.037))
                for u,z in ((-sw,-sh),(sw,-sh),(sw,sh),(-sw,sh),(-sw,-sh))],.005,lod,label+'/Raised plaque rims',EDGE)
        frame=[(.286,v-.116),(.896,v-.116),(.896,v+.116),(.286,v+.116),(.286,v-.116)]
        wire(b,[p(u,vert)for u,vert in frame],.0056,lod,label+'/Rectangle around the paired wires')
        for base in (v-.033,v+.030):
            for a,c1 in ((.286,c-half_width),(c+half_width,.896)):
                count=16 if lod else 29
                path=[p(a+(c1-a)*j/count,base+.010*sin((a+(c1-a)*j/count)*pi*29))for j in range(count+1)]
                wire(b,path,.0057,lod,label+'/Paired crimped wires')


def little_balcony(b,cx,floor,level,side,lod):
    width=D['slab_width'];depth=D['balcony_depth'];y=-depth
    label=f'{level}/{side}'
    # The neighbouring slabs end independently at their own party-wall side.
    near=Facade(b,(cx-width/2,y),(cx+width/2,y),label)
    for z,ww,dd,hh in [(floor-.116,width-.07,depth+.03,.15),(floor-.027,width,depth+.06,.063)]:
        b.box((cx,-depth/2,z),(ww,dd,hh),SLAB,label=label+'/Stepped balcony slab')
    top=floor+D['guard_height'];front_x=width-.10;rail_h=top-floor-.085
    band_edges=((0.,.0859),(.4498,.5411),(.906,1.))
    for j,(lo,hi) in enumerate(band_edges):
        left=(lo-.5)*front_x
        band_label=label+'/Ironwork'
        oval_band(b,near,left,floor+.047,(hi-lo)*front_x,rail_h,j==1,lod,band_label)
        if j<2:
            cell_width=(band_edges[j+1][0]-lo)*front_x
            ornamental_cell(b,near,left,floor+.047,cell_width,rail_h,lod,band_label)
    near.box(0,top,front_x+.055,.041,.063,.018,EDGE,'Top handrail')
    near.box(0,floor+.044,front_x+.024,.031,.037,.011,IRON,'Base rail')
    for xx in (-front_x/2,front_x/2):
        near.box(xx,(floor+top)/2,.026,top-floor,.038,.018,IRON,'Balcony posts')
    for hand in (-1,1):
        xx=cx+hand*front_x/2
        sideface=Facade(b,(xx,-depth),(xx,0),label+'/Side')
        sideface.box(0,top,depth+.028,.04,.047,0,EDGE,'Top return')
        for ratio in (.05,.49):sideface.box(0,floor+ratio*(top-floor),depth,.02,.022,0,IRON,'Horizontal return')
        for step in (-1,0,1):sideface.box(step*depth*.39,(floor+top)/2,.019,top-floor,.026,0,IRON,'Side spindles')

def build_ground(b,wall,cx,side):
    width=1.47;h=D['ground_crown'];sill=.11;opening=shoulder(cx,sill,width,h,True)
    ring(wall,opening,.077,.05,-.012,CHALK,'Ground entrance arch')
    jamb=opening.difference(opening.buffer(-.067,join_style=2))
    wall.prism(jamb,-1.20,-.012,SHADE,'Deep entrance reveals')
    wall.prism(opening,-1.235,-1.20,SHADE,'Back wall inside entry')
    wall.box(cx+.09,.96,.87,1.72,.055,-1.16,WOOD,'Simple shaded door')
    wall.box(cx,.105,width+.11,.16,1.34,-.53,SLAB,'Entry steps and landing')

def middle_awning(b,cx):
    # The high courtyard photograph shows two separate green hoods over the middle-storey doors.
    width=D['opening_width']+.39
    h=D['middle_floor']+D['middle_clear_height']+.15
    corners=[(cx-width/2,-.055,h),(cx+width/2,-.055,h),(cx+width/2,-.52,h-.19),(cx-width/2,-.52,h-.19)]
    b.add([(x,y,z-.024)for x,y,z in corners]+corners,
          [(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],GREEN,'Green awnings seen in the courtyard photograph')
    b.box((cx,-.52,h-.21),(width,.027,.04),GREEN,label='Awning valances')
    for ratio in (-.50,-.16,.16,.50):
        x=cx+ratio*width
        b.tube([(x,-.055,h+.007),(x,-.52,h-.183)],.009,DRAIN,6,'Seams in the green awnings')
    for hand in (-1,1):
        x=cx+hand*(width/2-.065)
        b.tube([(x,-.04,h-.52),(x,-.47,h-.19)],.011,IRON,6,'Slender awning stays')


ROOF_X=(-3.19,-2.68,-2.44,-2.18,0.,2.18,2.44,2.68,3.19)
ROOF_Y=(.40,.40,.10,-.31,-.31,-.31,.10,.40,.40)


def roof_height(x,y):
    front=float(np.interp(x,ROOF_X,ROOF_Y))
    return D['roof_eave']+D['roof_slope']*(2.83-.40)*(y-front)/(2.83-front)


def ridge_and_tiles(b,lod):
    # A short slice of the main slope meets the three lower faces of the paired projecting bays.
    eave=D['roof_eave'];depth=2.83;half=3.19
    X,Y=ROOF_X,ROOF_Y
    def surf(x,t):
        front=float(np.interp(x,X,Y));y=front+t*(depth-front)
        return (x,y,roof_height(x,y))
    for i,(a,c)in enumerate(zip(X,X[1:])):
        corners=[surf(a,0),surf(c,0),surf(c,1),surf(a,1)]
        b.add([(x,y,z-.095)for x,y,z in corners]+corners,
              [(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],TROUGH,'Short clay roof sections')
        fa=Facade(b,corners[0][:2],corners[1][:2],'Stepped front eaves')
        fa.box(0,eave-.097,fa.length,.106,.156,0,TRIM,'Dark fascia')
        fa.box(0,eave-.045,fa.length,.043,.17,.004,CLAY,'Clay lip')
    columns=30 if lod else 45;rows=9 if lod else 16
    for j in range(columns):
        x=-half+(j+.5)*(2*half/columns)
        a,c=surf(x,0),surf(x,1)
        wire(b,[(p[0],p[1],p[2]+.019)for p in(a,c)],.020,lod,'Rows of tile rolls',CLAY)
    for i in range(1,rows):
        t=i/rows
        line=[(x,y,z+.014)for x,y,z in (surf(v,t)for v in X)]
        wire(b,line,.012,lod,'Overlapping short tile courses',CLAY)
    # In photo 42 the party wall projects past the front eave and steps up along the common roof.
    points=[(-.385,eave-.64),(-.385,eave+.17),(.50,eave+.59),(1.06,eave+.89),
            (1.39,eave+.91),(2.84,eave+1.70),(2.84,eave+.89)]
    b.prism(Polygon(points),-.082,.082,lambda y,z,x:(x,y,z),STONE,'Raised central party wall')
    ridge=points[1:6]
    for (y,z),(yy,zz)in zip(ridge,ridge[1:]):
        cap=Polygon([(y,z),(yy,zz),(yy,zz+.063),(y,z+.063)])
        b.prism(cap,-.111,.111,lambda y,z,x:(x,y,z),CAP,'Stepped cap of party wall')

def add_building(b,lod):
    half=2.24;wall=Facade(b,(-half,0),(half,0),'South wall')
    openings=[]
    for side in (-1,1):
        cx=side*D['centres']/2
        openings.append(shoulder(cx,.11,1.47,D['ground_crown'],True))
        for level,sill,h in [('Middle pair',D['middle_floor'],D['middle_clear_height']),
                              ('Upper pair',D['upper_floor'],D['upper_left_clear_height'] if side<0 else D['upper_right_clear_height'])]:
            openings.append(shoulder(cx,sill,D['opening_width'],h))
            balcony_door(b,wall,cx,sill,h,level,side,lod)
            little_balcony(b,cx,sill,level,side,lod)
        middle_awning(b,cx)
        build_ground(b,wall,cx,side)
    wall.wall(.035,roof_height(0,0)-.088,openings,.26,STONE)
    outer=3.19;back=D['central_projection']
    for side in (-1,1):
        faces=[((side*half,0),(side*2.58,back)),((side*2.58,back),(side*outer,back)),
               ((side*outer,back),(side*outer,2.83))]
        for a,c in faces:
            if side==-1:a,c=c,a
            face=Facade(b,a,c,'Offset masonry cheeks')
            span=face.length/2
            upper_a=roof_height(*a)-.09;upper_c=roof_height(*c)-.09
            outline=Polygon([(-span,.035),(span,.035),(span,upper_c),(-span,upper_a)])
            face.wall(.035,max(upper_a,upper_c),(),.17,STONE,outline=outline)
        x=side*2.54
        wire(b,[(x,back-.12,.065),(x,back-.12,D['roof_eave']-.16)],.046,lod,'Narrow downpipes',DRAIN)
    rear=Facade(b,(outer,2.83),(-outer,2.83),'Cut rear')
    rear.wall(0,roof_height(0,2.83)-.09,(),.17,STONE)
    b.box((0,1.46,.021),(2*outer,2.92,.042),SLAB,label='Bottom of architectural section')
    ridge_and_tiles(b,lod)
    texture_coordinates(b)

if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--blender',default='blender');args,remaining=parser.parse_known_args()
    os.environ['LIBO_PAIR_BLENDER']=args.blender
    sys.argv[1:]=[*remaining,'--blender',str(SOURCE/'native_blender.py')]
    package.Builder=AggregateBuilder
    package.build(SOURCE,META,PALETTE,add_building)
