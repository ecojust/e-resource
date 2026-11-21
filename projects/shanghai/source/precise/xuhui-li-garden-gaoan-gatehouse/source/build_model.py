"""Both elevations and the open carriage passage of the Li garden gatehouse."""
import argparse
import json
import math
import os
import sys
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

SOURCE = Path(__file__).resolve().parent
PROJECT = next(p for p in SOURCE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0, str(PROJECT/'tools'))
import package_architectural_model as package
sys.path.insert(0, str(PROJECT/'source/precise/huangpu-somekh-building-street-corner/source'))
from aggregate_mesh import AggregateBuilder
from photo_architecture import Facade, opening
from roughcast import PLASTER, texture_coordinates
from brick_arch import ARCH_PALETTE, build_arch

ID = 'xuhui-li-garden-gaoan-gatehouse'
META = dict(id=ID, name='励家花园高安路街门与双面砖券过道',
            viewer_page='li-garden-gaoan-gatehouse.html', heritage_group='4D039',
            heritage_address='高安路63号', status='photographic-gatehouse-study',
            scope='门屋临街和面院的双面砖券、上层山墙窗、过道与大门。')
D = json.loads((SOURCE.parent/'measurements/building-dimensions.json').read_bytes())['model_parameters_m']
STONE = 'Dressed grey sandstone'
PAVE = 'Charcoal paving'
PAVE_LIGHT = 'Weathered paving'
LIME = 'Warm lime plaster'
PALE = 'Ivory moulded cement'
GLASS = 'Smoke blue window glass'
FRAME = 'Grey green steel window'
IRON = 'Black green wrought iron'
PIPE = 'Green rainwater fittings'
ROOF = 'Weathered clay roof'
COVER = 'Russet clay cover tile'
BASEBRICK = 'Deep red plinth brick'
GROUT = 'Grey lime joints'
SOFFIT = 'Light passage ceiling'
SIGN = 'Green enamel number plate'
LETTER = 'White enamel lettering'

def tone(rgb, roughness=.82, metallic=0.):
    a=np.array(rgb,dtype=float)/255.
    rgb=np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4)
    return dict(color=rgb.tolist(),roughness=roughness,metallic=metallic)

PALETTE={**ARCH_PALETTE,
         PLASTER:dict(color=[1.,1.,1.],roughness=.94,texture=str(SOURCE/'ivory-roughcast.png')),
         STONE:tone((154,149,138)), PAVE:tone((97,99,95)), PAVE_LIGHT:tone((112,111,102)),
         LIME:tone((214,211,196)), PALE:tone((224,218,201)), GLASS:tone((106,133,146),.25,.17),
         FRAME:tone((89,108,99),.52,.23), IRON:tone((44,52,47),.65,.36), PIPE:tone((65,87,75),.56,.32),
         ROOF:tone((114,74,58)), COVER:tone((148,91,68)), BASEBRICK:tone((143,68,53)), GROUT:tone((148,139,124)),
         SIGN:tone((52,133,106),.48,.22), LETTER:tone((236,233,212),.7),
         SOFFIT:tone((217,211,191)), 'Recessed light':tone((116,112,92),.57,.1)}

def upper_window(face,lod):
    width=D['upper_window_width']
    sill=D['upper_sill']
    head=D['upper_window_height']
    rise=width*.5
    hole=opening(0,sill,width,head,rise,24 if lod else 40)
    inner=hole.buffer(-.055,join_style=1)
    spring=sill+head-rise
    sections=unary_union([box(-.035,sill,.035,spring),box(-width/2,spring-.036,width/2,spring+.036)])
    # The fanlight has no radial tracery. The two tall opening lights end at its transom.
    ring=hole.difference(inner.difference(sections))
    face.prism(ring,-.125,-.067,FRAME,'arched steel sash and transom')
    face.prism(inner,-.168,-.146,GLASS,'fanlight and paired panes')
    face.prism(hole.buffer(.059,join_style=1).difference(hole),-.038,.012,PALE,'fine reveal around arched window')
    face.box(0,sill-.044,width+.25,.085,.26,.034,STONE,'projecting window sill')
    return hole

def gable(b,y,out,lod):
    half=D['half_width'];eave=D['eave'];ridge=D['ridge']
    ends=((-half,y),(half,y)) if out<0 else ((half,y),(-half,y))
    face=Facade(b,*ends,'Street gable' if out<0 else 'Court gable')
    halfspan=D['clear_width']/2;h=D['spring']+D['arch_rise']
    aperture=opening(0,-.05,2*halfspan,h+.05,D['arch_rise'],60 if lod else 120)
    win=upper_window(face,lod)
    # A square vent and two courses of corbelling are visible below the apex on both sides.
    vent=box(-.066,ridge-.64,.066,ridge-.49)
    wall=Polygon([(-half,0),(half,0),(half,eave),(0,ridge),(-half,eave)])
    face.prism(wall.difference(unary_union([aperture,win,vent])),-D['wall_thickness'],0,PLASTER,'gable around through arch and window')
    face.prism(vent,-.21,-.18,IRON,'shadow of square air vent')
    for hand in (-1,1):
        slope=(ridge-eave)/half
        for band,gap in ((.063,.0),(.045,.13)):
            line=Polygon([(0,ridge-gap),(hand*half,eave-gap),(hand*half,eave-gap-band),(0,ridge-gap-band)])
            face.prism(line,-.03,.102,PALE,'inclined gable coping')
        for i in range(22):
            x=hand*(i+.54)*half/22
            z=ridge-abs(x)*slope-.273
            face.box(x,z,.1,.105,.135,.03,PALE,'upper stepped gable dentils')
            shifted=x+hand*half/44
            face.box(shifted,ridge-abs(shifted)*slope-.345,.082,.081,.10,.018,PALE,'lower staggered gable dentils')
    if out<0:
        street_details(face)
    build_arch(b,lod,y,out,'Street' if out<0 else 'Court')
    interior_arch(b,y,out,lod)
    return face

def interior_arch(b,y,out,lod):
    """The reveals and the simple brick ring seen through the opposite door."""
    inner=D['clear_width']/2
    spring=D['spring']
    wall=D['wall_thickness']
    y_inner=y-out*wall
    # This face points into the passage, opposite to the elaborate exterior brick mouldings.
    ends=((inner,y_inner),(-inner,y_inner)) if out<0 else ((-inner,y_inner),(inner,y_inner))
    face=Facade(b,*ends,'Street inside' if out<0 else 'Court inside')
    def sector(a,b,r0,r1,steps=2):
        t=np.linspace(a,b,steps+1)
        return Polygon([(r1*math.cos(c),spring+r1*math.sin(c)) for c in t]+
                       [(r0*math.cos(c),spring+r0*math.sin(c)) for c in reversed(t)])
    whole=sector(0,math.pi,inner-.003,inner+.32,90)
    face.prism(whole,.003,.012,GROUT,'mortar bed on internal brick arch')
    # A restrained soldier course follows the hall head under the pale ceiling.
    for i in range(76):
        a=i*math.pi/76+.0019
        c=(i+1)*math.pi/76-.0019
        face.prism(sector(a,c,inner,inner+.32),.010,.027,BASEBRICK,'radial bricks facing passage')
        # The dark bricks wrap the curved soffit through the thickness of the doorway.
        face.prism(sector(a,c,inner-.012,inner+.022),-wall+.008,.015,BASEBRICK,'inner curve of through opening')
    for sign in (-1,1):
        x=sign*(inner+.16)
        face.box(x,spring/2,.32,spring,.012,.010,GROUT,'inner jamb mortar')
        for j in range(15):
            z=(j+.5)*spring/15
            face.box(x,z,.312,spring/15-.010,.021,.017,BASEBRICK,'brick courses by opening')
            face.box(sign*(inner+.007),z,.021,spring/15-.010,wall-.022,-wall/2,BASEBRICK,'brick return inside jamb')

def street_details(face):
    # Thin brick keys protrude in pairs from the lime wall around the street portal.
    # The rear courtyard elevation is plain at these levels.
    for side in (-1,1):
        for row,z in enumerate((1.01,1.17,2.16,2.32,3.43,3.59,5.36,5.52)):
            width=.64 if row%2==0 else .46
            n=3 if row%2==0 else 2
            for col in range(n):
                x=side*(D['half_width']-width+(col+.5)*width/n)
                face.box(x,z,width/n-.014,.105,.028,.011,BASEBRICK,'keyed brick accents in stucco')
    cx,cz=3.055,3.02
    panel=box(cx-.151,cz-.124,cx+.151,cz+.124).buffer(.009,join_style=1)
    face.prism(panel,0,.030,SIGN,'green enamel 63 address plate')
    face.prism(panel.difference(panel.buffer(-.005,join_style=1)),.030,.033,LETTER,'thin outline on address plate')
    # Centre-line tracings give the 63 address numerals their physical thickness.
    digits=[(-.068,[(.036,.053),(.019,.067),(-.003,.066),(-.026,.051),(-.039,.027),(-.040,-.007),(-.031,-.035),(-.014,-.048),(.013,-.046),(.029,-.032),(.034,-.011),(.027,.006),(.008,.018),(-.011,.018),(-.031,.006)]),
            (.061,[(-.032,.051),(-.015,.067),(.009,.067),(.030,.057),(.035,.040),(.029,.023),(.017,.013),(-.001,.008),(.015,.007),(.032,-.005),(.037,-.022),(.030,-.038),(.012,-.048),(-.012,-.048),(-.034,-.032)])]
    from shapely.geometry import LineString
    for off,points in digits:
        stroke=LineString([(cx+off+x,cz+.014+z) for x,z in points]).buffer(.009,cap_style=1,join_style=1)
        face.prism(stroke,.031,.035,LETTER,'address number 63')
    for x in (cx-.128,cx+.128):
        face.box(x,cz-.084,.012,.012,.005,.034,FRAME,'address plate fixing')

def iron_gates(b,depth,lod):
    span=D['clear_width']/2
    for side in (-1,1):
        pivot=(side*(span-.045),.35)
        length=span-.065
        # The leaves open down the side walls and preserve the full view through the gateway.
        a=math.radians(82)
        tip=(pivot[0]-side*length*math.cos(a),pivot[1]+length*math.sin(a))
        face=Facade(b,pivot,tip,'Iron leaf '+('left' if side<0 else 'right'))
        half=face.length/2;top=2.73
        for hand in (-1,1):
            face.box(hand*(half-.031),top/2,.062,top,.075,0,IRON,'hinge and latch stiles')
        for z in (.085,.47,.90,2.08,2.64):
            face.box(0,z,2*half,.052,.065,0,IRON,'rails')
        for col in range(11):
            u=-half+.115+(2*half-.23)*col/10
            face.box(u,1.38,.022,2.59,.027,0,IRON,'vertical pickets')
            if col%2==0:
                for z in (.67,1.54):
                    for hand in (-1,1):
                        path=[]
                        for t in np.linspace(0,1,12 if lod else 22):
                            theta=3.7-5.0*t;r=.097*(1-.81*t)
                            path.append(face.point(u+hand*(.05+r*math.cos(theta)),z+r*math.sin(theta),.018))
                        b.tube(path,.012,IRON,5 if lod else 8,'Gate / paired scrolls')

def passage(b,lod):
    span=D['passage_half_width'];depth=D['tunnel_length'];half=D['half_width']
    b.box((0,depth/2,.004),(span*2+.17,depth+.29,.072),GROUT,label='Passage / paving bed')
    for row in range(math.ceil(depth/.72)):
        y0=row*.72-.045;y1=min(depth+.06,y0+.72)
        for col in range(-4,5):
            x0=max(-span-.055,col*.62+(row%2)*.31);x1=min(span+.055,(col+1)*.62+(row%2)*.31)
            if x1-x0>.05 and y1-y0>.02:
                b.box(((x0+x1)/2,(y0+y1)/2,.046),(x1-x0-.009,y1-y0-.009,.023),
                      PAVE_LIGHT if (3*row+col)%7==0 else PAVE,label='Passage / individual paving slabs')
    for side in (-1,1):
        b.box((side*(span+.14),depth/2,1.98),(.28,depth-.12,3.96),LIME,label='Passage / side wall')
        b.box((side*(span+.003),depth/2,.355),(.019,depth-.13,.64),GROUT,label='Passage / backing behind base bricks')
        for course in range(7):
            for n in range(-1,math.ceil(depth/.34)+1):
                y0=max(.063,(n+(course%2)*.5)*.34);y1=min(depth-.063,(n+1+(course%2)*.5)*.34)
                if y1-y0>.015:
                    b.box((side*(span-.012),(y0+y1)/2,.099+course*.083),(.026,y1-y0-.009,.074),BASEBRICK,label='Passage / staggered brick skirting')
        # Parts of the gatehouse's side walls adjoin the estate boundary wings.
        b.box((side*(half-.13),depth/2,D['eave']/2),(.26,depth-.40,D['eave']),PLASTER,label='Gatehouse / side wall')
    ceiling=3.715
    b.box((0,depth/2,ceiling+.055),(2*span+.06,depth-.1,.11),SOFFIT,label='Passage / level soffit')
    for x in (-1.10,1.10):
        for frac in (.20,.50,.80):
            b.lathe((x,depth*frac),[(ceiling-.006,.092),(ceiling+.003,.097)],'Recessed light',10 if lod else 20,'Passage / recessed ceiling lights')
    iron_gates(b,depth,lod)

def sloping_roof(b,lod):
    half=D['half_width'];depth=D['tunnel_length'];eave=D['eave'];ridge=D['ridge'];pitch=(ridge-eave)/half
    # The short overhang lies between both raised gable copings.
    edge=half+.14;lo=.075;hi=depth-.075
    for side in (-1,1):
        profile=Polygon([(0,ridge-.14),(side*edge,ridge-edge*pitch-.14),(side*edge,ridge-edge*pitch-.23),(0,ridge-.23)])
        b.prism(profile,-hi,-lo,lambda x,z,d:(x,-d,z),ROOF,'Gatehouse / pitched tile bed')
        spacing=.185;n=round((hi-lo)/spacing)
        for i in range(n):
            cy=lo+(i+.5)*(hi-lo)/n
            verts=[];faces=[]
            for x in (0.,edge):
                for a in np.linspace(0,math.pi,5 if lod else 9):
                    verts.append((side*x,cy+.067*math.cos(a),ridge-x*pitch-.134+.044*math.sin(a)))
            count=len(verts)//2
            for j in range(count-1):
                faces.extend([(j,j+1,j+count),(j+1,j+1+count,j+count)])
            b.add(verts,faces,COVER,'Pitched roof / channel cover tiles')
        for i in range(1,11):
            x=edge*i/11;z=ridge-x*pitch-.147
            b.tube([(side*x,lo,z),(side*x,hi,z)],.011,ROOF,5,'Pitched roof / shingle course shadow')
        b.tube([(side*edge,lo,eave-.232),(side*edge,hi,eave-.232)],.049,PIPE,8 if lod else 14,'Side eaves / green gutter')
        for y in (.12,depth-.12):
            b.tube([(side*(half+.04),y,.14),(side*(half+.02),y,eave-.61),(side*(half+.13),y,eave-.43),(side*edge,y,eave-.24)],.044,PIPE,8 if lod else 14,'Gable ends / green downpipe')
    for j in range(math.ceil(depth/.38)):
        a=max(lo,j*.38);c=min(hi,(j+1)*.38+.01)
        if c>a:
            b.tube([(0,a,ridge-.096),(0,c,ridge-.096)],.075,COVER,8 if lod else 14,'Roof ridge / rounded clay pieces')

def add_building(b,lod):
    gable(b,0,-1,lod)
    gable(b,D['tunnel_length'],1,lod)
    passage(b,lod)
    sloping_roof(b,lod)
    # The radial and linear geometry shares one scale from the street triangulation.
    scale=D['model_scale']
    for part in b.parts:
        part['vertices']=(np.asarray(part['vertices'])*scale).tolist()
    texture_coordinates(b)

if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    opts,args=parser.parse_known_args()
    os.environ['LI_GARDEN_BLENDER']=opts.blender
    sys.argv[1:]=[*args,'--blender',str(SOURCE/'native_blender.py')]
    package.Builder=AggregateBuilder
    package.build(SOURCE,META,PALETTE,add_building)
