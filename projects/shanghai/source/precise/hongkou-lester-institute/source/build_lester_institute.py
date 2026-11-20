"""Build the garden elevation and roof of the former Lester Institute, 505 East Changzhi Road."""
import json
import math
import sys
from pathlib import Path

import numpy as np
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / 'tools'))
from package_architectural_model import build
from photo_architecture import Facade, opening

P = json.loads((HERE / 'parameters.json').read_bytes())
LEVELS = P['levels_m']
PLANS = P['plans_m']
META = {
    'id': P['id'], 'name': '雷氏德工学院（东长治路505号主楼）',
    'status': 'photo-informed-building-exterior',
    'scope': 'The restored main academic building, its two angled garden wings, pointed arcade, central fluted dome and north roof.',
    'model_scope_zh': '以1934年立面、平面和2022年修缮影像重构园侧七孔尖券、两翼分组钢窗、中央塔穹、后方折形采光屋面及可辨识的外壳。背面窗距、穹肋断面、屋面标高按图估计。南侧公共花园和校园附属未建。',
    'viewer_page': 'lester-institute.html', 'audit_directory': 'data/audit/lester-institute-v1/',
    'coordinate_convention': 'Local glTF X runs along the garden front toward 108.25 degrees true, Y is up and Z faces the garden at 198.25 degrees true.',
    'source_register': 'source/precise/hongkou-lester-institute/reference-review.json',
    'map_reference_license': 'OpenStreetMap and Overture Maps, ODbL-1.0.', 'interiors_modeled': False,
}
MATERIALS = {
    'warm rough brick': ([.64,.58,.48],.92,.0), 'bush hammered stone': ([.67,.625,.535],.88,.0),
    'granite trim': ([.76,.712,.613],.87,.0), 'gray plinth': ([.44,.423,.384],.94,.0),
    'green steel': ([.12,.169,.141],.53,.27), 'reflective panes': ([.235,.291,.283],.29,.20),
    'roof tile': ([.37,.287,.227],.87,.0), 'flat mineral roof': ([.416,.410,.37],.93,.0),
    'rooflight glazing': ([.48,.535,.521],.41,.13), 'lantern recess': ([.19,.205,.192],.79,.09),
    'dark oak': ([.266,.151,.096],.71,.0), 'bronze doorwork': ([.40,.295,.17],.49,.63),
    'bronze shadow': ([.211,.175,.111],.62,.39), 'plaster soffit': ([.782,.747,.669],.90,.0),
    'mortar shadow': ([.457,.423,.359],.96,.0),'paving': ([.50,.49,.448],.95,.0),
}
PALETTE = {k:{'color':c,'roughness':r,'metallic':m} for k,(c,r,m) in MATERIALS.items()}


def pointed(u, bottom, width, spring, rise, samples):
    """Two circle arcs meeting at one pointed crown. The spring and crown are explicit."""
    radius = (rise**2 + (width/2)**2)/width
    offset = radius - width/2
    end = math.atan2(rise, offset)
    # Right jamb is at +width/2; the right arc is centred on the left.
    right = [(u-offset+radius*math.cos(t), spring+radius*math.sin(t))
             for t in np.linspace(0, end, samples)]
    left = [(2*u-x,z) for x,z in reversed(right[:-1])]
    return Polygon([(u-width/2,bottom),(u+width/2,bottom),*right,*left])


def trim(face, shape, width, back, front, material, label):
    rim = shape.difference(shape.buffer(-width,join_style='mitre'))
    face.prism(rim,back,front,material,label)


def sash(face,shape,cols,rows,lod=False):
    x0,z0,x1,z1=shape.bounds
    face.prism(shape.buffer(.012,join_style='mitre'),-.345,-.326,'reflective panes','recessed glass')
    clear=shape.buffer(-.074,join_style='mitre')
    bars=[]
    for k in range(1,cols):
        x=x0+(x1-x0)*k/cols
        bars.append(box(x-.024,z0,x+.024,z1))
    for k in range(1,rows):
        z=z0+(z1-z0)*k/rows
        bars.append(box(x0,z-.022,x1,z+.022))
    frame=shape.buffer(-.019,join_style='mitre').difference(clear.difference(unary_union(bars)))
    face.prism(frame,-.268,-.177,'green steel','restored steel sash')
    if not lod:
        face.box((x0+x1)/2,z0-.055,x1-x0+.17,.11,.28,-.028,'granite trim','sloped sill')


def roof_plate(builder,points,z,material,label,thickness=.16):
    builder.plan_prism(Polygon(points),z-thickness,z,material,label)


def piers_and_coping(face, centers, spacing, lod):
    top=LEVELS['wing_parapet']
    for x in centers:
        zs=[(x-spacing*.49,top-.46),(x-spacing*.37,top-.49),(x-spacing*.13,top-.23),
            (x,top-.17),(x+spacing*.16,top-.23),(x+spacing*.38,top-.49),(x+spacing*.49,top-.46)]
        crown=Polygon([(x-spacing*.49,top-.88),(x+spacing*.49,top-.88),*reversed(zs)])
        face.prism(crown,-.37,.06,'granite trim','shallow broken parapet')
        dy=.70
        badge=Polygon([(x-.28,top-dy),(x+.28,top-dy),(x+.24,top-dy-.43),
                       (x,top-dy-.57),(x-.24,top-dy-.43)])
        face.prism(badge,.008,.065,'bush hammered stone','window bay shield')
    for x in np.linspace(-face.length/2+.17, face.length/2-.17,6):
        face.box(x,(top-.30)/2,.32,top-.30,.41,.065,'bush hammered stone','vertical buttresses')
        cap=Polygon([(x-.21,top-.62),(x+.21,top-.62),(x+.17,top+.22),(x,top+.61),(x-.17,top+.22)])
        face.prism(cap,-.23,.31,'granite trim','tapered pier finial')
        if not lod:
            face.box(x,top*.72,.085,top*.52,.085,.309,'granite trim','buttress fillet')


def garden_wing(builder,side,lod):
    points=PLANS[side]
    face=Facade(builder,points[0],points[1],side+' wing garden')
    spacing=face.length/5
    centers=[(-2+i)*spacing for i in range(5)]
    holes=[]
    for c in centers:
        for shift in [-.255,0,.255]:
            for z,h in zip(LEVELS['wing_main_window_bottoms'],LEVELS['wing_main_window_heights']):
                holes.append(opening(c+spacing*shift,z,spacing*.185,h))
    face.wall(.17,LEVELS['wing_parapet']-.83,holes,.39,'warm rough brick')
    for hole in holes:
        sash(face,hole,2,2 if lod else 3,lod)
    face.beam(.54,.60,.12,'gray plinth',face.length,'stone plinth')
    piers_and_coping(face,centers,spacing,lod)
    # The two ends face different streets; the hidden inner edge meets the central block.
    outer=3 if side=='west' else 1
    for edge in (outer,2):
        rear=Facade(builder,points[edge],points[(edge+1)%4],side+(' return' if edge==outer else ' rear'))
        count=3 if edge==outer else 8
        step=rear.length/(count+.4)
        parts=[opening((i-(count-1)/2)*step,z,step*.57,3.25)
               for i in range(count) for z in [1.58,6.79,12.08]]
        rear.wall(.17,18.80,parts,.39,'warm rough brick')
        for aperture in parts:sash(rear,aperture,2,2 if lod else 3,lod)
        rear.beam(18.80,.22,.10,'granite trim',rear.length,'return coping')
        rear.beam(.54,.60,.09,'gray plinth',rear.length,'plinth')
    roof_plate(builder,points,LEVELS['wing_roof'],'roof tile',side+' wing/flat roof')
    roof_plate(builder,points,.19,'gray plinth',side+' wing/base',.19)
    # The axial access cleft is a shallow raised strip visible in the oblique aerial.
    a,b=np.array(points[3]),np.array(points[2])
    c,d=np.array(points[0]),np.array(points[1])
    strip=[a*.84+c*.16,b*.84+d*.16,b*.66+d*.34,a*.66+c*.34]
    roof_plate(builder,strip,18.84,'flat mineral roof',side+' wing/roof access',.32)


def portal_badge(face,x,kind,lod):
    shield=Polygon([(x-.34,8.17),(x+.34,8.17),(x+.32,7.63),(x+.22,7.50),(x,7.39),
                    (x-.22,7.50),(x-.32,7.63)])
    face.prism(shield,.045,.12,'granite trim','shield carving')
    trim(face,shield,.043,.119,.147,'bush hammered stone','shield bead')
    # Three confirmed classes from the conservation survey, with representative relief strokes.
    if kind==0:
        paths=[[(-.18,7.59),(0,8.01),(.17,7.59)],[(-.13,7.76),(.10,7.74),(.19,7.84)]]
    elif kind==1:
        paths=[[(-.19,7.91),(.18,7.98)],[(-.12,7.66),(.03,7.91),(.14,7.66)],[(-.17,7.63),(.18,7.63)]]
    else:
        paths=[]
        for u,z,r in [(-.105,7.79,.103),(.09,7.86,.122)]:
            paths.append([(u+r*math.cos(t),z+r*math.sin(t))for t in np.linspace(0,math.tau,10 if lod else 16)])
    for points in paths:
        face.builder.tube([face.point(x+u,z,.153)for u,z in points],.022,'bush hammered stone',5,'Arcade/relief motif')


def bronze_doors(face,lod):
    opening_shape=opening(0,.22,4.26,6.22)
    transom=opening(0,3.45,3.64,2.57)
    face.prism(opening_shape,-.42,-.36,'plaster soffit','portal reveal back')
    sash(face,transom,5,3,lod)
    # The timber/bronze leaves and the tall side lights sit within a second frame.
    for x in [-.765,.765]:
        leaf=box(x-.74,.22,x+.74,3.26)
        face.prism(leaf,-.324,-.257,'dark oak','paired wood leaves')
        for z,h in [(.79,.72),(2.18,1.61)]:
            panel=box(x-.56,z-h/2,x+.56,z+h/2)
            trim(face,panel,.07,-.258,-.174,'bronze shadow','bronze panel borders')
        for dx in [-.18,.18]:
            xx=x+dx
            # The copied museum door ornament includes laboratory glassware and scales.
            line=[(xx-.039,2.69),(xx-.039,2.51),(xx-.13,2.31),(xx+.13,2.31),(xx+.04,2.51),(xx+.04,2.69)]
            face.builder.tube([face.point(i,z,-.151)for i,z in line],.021,'bronze doorwork',5,'Door/laboratory flask')
        if not lod:
            for a,b in [[(x-.33,1.60),(x+.33,1.60)],[(x,1.40),(x,1.85)],[(x-.28,1.59),(x-.37,1.41)],[(x+.28,1.59),(x+.37,1.41)]]:
                face.line((*a,-.145),(*b,-.145),.023,'bronze doorwork',5,'balance relief')
        face.box(x+(.47 if x<0 else -.47),1.36,.047,.48,.12,-.13,'bronze doorwork','handle')
    face.box(0,1.745,.060,3.02,.074,-.209,'bronze shadow','door astragal')
    for x in [-1.79,1.79]:
        sash(face,opening(x,.29,.47,3.00),1,3,lod)


def garden_arcade(builder,lod):
    points=PLANS['porch']
    front=Facade(builder,points[0],points[1],'Arcade front')
    samples=7 if lod else 13
    span=front.length/(7+.15)
    cuts=[pointed((i-3)*span,.10,span*.806,2.81,2.65,samples)for i in range(7)]
    front.wall(.10,7.39,cuts,.64,'bush hammered stone')
    for aperture in cuts:
        surround=aperture.buffer(.104,join_style='mitre').difference(aperture).intersection(box(-front.length/2,.15,front.length/2,7.30))
        front.prism(surround,-.05,.048,'granite trim','arch arrises')
    # Each end of the cross passage is actually pierced, visible in the restored corridor photograph.
    for idx in (1,3):
        side=Facade(builder,points[idx],points[(idx+1)%4],'Arcade end')
        side.wall(.10,7.39,[pointed(0,.10,side.length*.80,2.80,2.64,samples)],.45,'bush hammered stone')
    for n in range(6):
        x=(n-2.5)*span
        front.box(x,7.89,.86,1.12,.17,.027,'granite trim','shield field')
        portal_badge(front,x,n%3,lod)
    front.beam(7.30,.24,.28,'granite trim',front.length+.15,'arcade fascia')
    front.beam(8.22,.20,.09,'granite trim',front.length+.11,'terrace coping')
    front.box(0,7.79,front.length,.73,.30,-.18,'bush hammered stone','terrace parapet')
    roof_plate(builder,points,7.10,'plaster soffit','Arcade/ceiling',.25)
    roof_plate(builder,points,7.34,'flat mineral roof','Arcade/terrace roof',.25)
    roof_plate(builder,points,.19,'paving','Arcade/porch floor',.19)
    for x in [-8,-4,0,4,8]:
        builder.lathe((x,-10.30),[(6.23,.07),(6.23,.18),(6.42,.21),(6.52,.07),(6.79,.043)],
                      'bronze shadow',8 if lod else 12,'Arcade/pendant light')


def central_block(builder,lod):
    pts=PLANS['center']
    face=Facade(builder,pts[1],pts[2],'Central garden bays')
    cheek_x=[-14.12,-11.92,-9.58,-7.34,7.34,9.58,11.92,14.12]
    holes=[opening(x,z,1.39,h)for x in cheek_x for z,h in [(8.69,3.23),(13.32,3.25),(17.96,3.26)]]
    entrance=opening(0,.22,4.26,6.22)
    lights=[opening(x,1.27,1.42,3.75) for x in [-8.50,8.50]]
    face.wall(.17,22.28,[entrance,*holes,*lights],.42,'warm rough brick')
    for aperture in holes+lights:sash(face,aperture,2,2 if lod else 3,lod)
    bronze_doors(face,lod)
    for x in [-15.09,-10.74,-6.21,6.21,10.74,15.09]:
        face.box(x,15.22,.36,14.46,.46,.08,'bush hammered stone','central masonry piers')
        face.box(x,22.56,.43,.34,.53,.07,'granite trim','pier cap')
    face.beam(22.31,.19,.13,'granite trim',face.length,'coping')
    for i in (0,2,3,4,5,6,7):
        edge=Facade(builder,pts[i],pts[(i+1)%len(pts)],'Central lower returns')
        count=1 if edge.length<6 else 4
        panes=[opening((j-(count-1)/2)*(edge.length/(count+.4)),z,min(1.30,edge.length/(count+1)*.63),2.86)
               for j in range(count) for z in [9.09,13.48]]
        edge.wall(.17,18.44,panes,.40,'warm rough brick')
        for pane in panes:sash(edge,pane,2,2,lod)
        edge.beam(18.47,.15,.07,'granite trim',edge.length,'lower coping')
    roof_plate(builder,pts,.19,'gray plinth','Center/base',.19)
    roof_plate(builder,pts,18.50,'flat mineral roof','Center/lower connecting roof')
    upper=PLANS['upper_center']
    for i in range(1,len(upper)):
        side=Facade(builder,upper[i],upper[(i+1)%len(upper)],'Central upper shoulders')
        count=2 if side.length<10 else 4
        step=side.length/(count+.4)
        windows=[opening((j-(count-1)/2)*step,19.14,min(1.37,step*.50),2.52)for j in range(count)]
        side.wall(18.43,22.31,windows,.37,'warm rough brick')
        for aperture in windows:sash(side,aperture,2,2,lod)
        side.beam(22.32,.19,.095,'granite trim',side.length,'upper coping')
    roof_plate(builder,upper,LEVELS['center_sides_roof'],'flat mineral roof','Center/stepped shoulders')


def domed_tower(builder,lod):
    cx,cy=0.,-5.98
    radius=6.19
    points=[(cx+radius*math.cos(a),cy+radius*math.sin(a))
            for a in np.linspace(-5*math.pi/8,11*math.pi/8,9)[:-1]]
    for i,start in enumerate(points):
        f=Facade(builder,start,points[(i+1)%8],'Tower '+str(i+1))
        visible_down=i in (7,0,1)
        low=7.28 if visible_down else LEVELS['center_sides_roof']-.17
        lancet=pointed(0,23.00,2.45,24.19,1.31,7 if lod else 13)
        windows=[lancet]
        if visible_down:windows += [opening(0,z,2.31,3.19) for z in (8.73,13.32,17.91)]
        f.wall(low,26.60,windows,.38,'bush hammered stone')
        for aperture in windows:sash(f,aperture,2,2 if lod else 3,lod)
        rim=lancet.buffer(.105,join_style='mitre').difference(lancet)
        f.prism(rim,-.024,.082,'granite trim','upper lancet moulding')
        for offset in [-.54,.54]:
            inner=pointed(offset,23.01,1.03,24.26,.78,6 if lod else 10)
            trace=inner.difference(inner.buffer(-.070,join_style='mitre')).intersection(box(-1.22,24.19,1.22,25.48))
            f.prism(trace,-.165,-.072,'granite trim','paired lancet tracery')
        f.box(-f.length/2+.16,(low+26.74)/2,.29,26.74-low,.42,.05,'granite trim','tower corner fin')
    builder.plan_prism(Polygon(points),26.38,26.62,'granite trim','Tower/top collar')
    # A solid dark backing is visible in the tall recesses between the radial masonry fins.
    profile=[(26.54,4.23),(27.80,4.12),(29.03,3.87),(30.22,3.36),(31.08,2.67),
             (31.67,1.87),(32.06,1.18)]
    builder.lathe((cx,cy),profile,'lantern recess',32 if lod else 64,'Crown/recessed dome')
    for i in range(16):
        a=math.tau*i/16
        vertices=[]
        for j,(h,r) in enumerate(profile):
            half_width=(.089 if j<4 else .074)
            for radius,angle in [(r-.028,a-half_width),(r+.215,a-half_width),(r+.215,a+half_width),(r-.028,a+half_width)]:
                vertices.append((cx+radius*math.cos(angle),cy+radius*math.sin(angle),h))
        faces=[(3,2,1,0),tuple(range(len(vertices)-4,len(vertices)))]
        for j in range(len(profile)-1):
            for k in range(4):
                v=4*j+k;next_v=4*j+(k+1)%4
                faces.append((v,next_v,next_v+4,v+4))
        builder.add(vertices,faces,'granite trim','Crown/radial masonry ribs')
    # The flue is centred inside the dome. Its low cap and ring are externally visible.
    builder.lathe((cx,cy),[(32.00,1.22),(32.13,1.16),(32.18,.83),(32.29,.80),
                           (LEVELS['dome_top'],.55)],'bush hammered stone',24 if lod else 40,'Crown/flue coping')
    builder.lathe((cx,cy),[(32.315,.54),(32.333,.53)],'lantern recess',24,'Crown/vent centre')


def north_hall(builder,lod):
    pts=PLANS['rear']
    for i in (1,2,3):
        f=Facade(builder,pts[i],pts[(i+1)%4],'North hall')
        count=5 if i!=2 else 4
        widths=f.length/(count+1)
        apertures=[opening((j-(count-1)/2)*widths,z,widths*.57,h)for j in range(count)
                   for z,h in ((1.55,3.27),(7.03,3.68))]
        f.wall(.17,13.90,apertures,.42,'warm rough brick')
        for aperture in apertures:sash(f,aperture,2,2,lod)
        f.beam(13.90,.23,.09,'granite trim',f.length,'hall coping')
    roof_plate(builder,pts,.19,'gray plinth','North hall/base',.19)
    roof_plate(builder,pts,13.91,'flat mineral roof','North hall/roof')
    # The light banks lie along the junction of the main block and the northern hall.
    # The steep glazed faces look toward the northeast. Two roof panels are visible abreast.
    extension=[[-9.20,6.64],[9.20,6.64],[9.20,17.85],[-9.20,17.85]]
    for k in range(4):
        end=Facade(builder,extension[k],extension[(k+1)%4],'Drawing studio upper return')
        strips=[opening((j-1)*(end.length/3.7),19.21,end.length/6.6,2.20)for j in range(3)]
        end.wall(13.84,22.43,strips,.30,'warm rough brick')
        for aperture in strips:sash(end,aperture,2,2,lod)
    roof_plate(builder,extension,22.43,'flat mineral roof','Drawing studio/upper roof')
    strips=3
    for j in range(strips):
        front_y=6.65+j*3.73
        back_y=front_y+3.73
        for left,right in [(-9.20,-.22),(.22,9.20)]:
            floor=22.43 if j<2 else 22.36
            section=Polygon([(front_y,floor),(back_y,floor),(back_y-.39,floor+1.66),(front_y,floor+.13)])
            def cross(y,z,x):
                return (x,y,z)
            builder.prism(section,left,right,cross,'flat mineral roof','Rooflights/sawtooth slope')
            # Glazing is finite and attached to the steep NE-facing plane, with metal jambs at each end.
            y0,y1=back_y+.009,back_y-.39+.009
            z0,z1=floor+.055,floor+1.58
            quad=[(left+.13,y0,z0),(left+.13,y1,z1),(right-.13,y1,z1),(right-.13,y0,z0)]
            normal=np.array([0.,.036,.008])
            builder.add([*quad,*[tuple(np.array(v)+normal) for v in quad]],
                        [(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],
                        'rooflight glazing','Rooflights/northeast panes')
            for x in np.linspace(left+.14,right-.14,4 if lod else 7):
                builder.tube([(x,y0+.065,z0),(x,y1+.065,z1)],.042,'green steel',5,'Rooflights/steel rafters')
    # The portion north of the lantern is lower and flat; heights are approximate.
    raised=[[-7.40,22.00],[7.38,22.00],[7.38,33.54],[-7.40,33.54]]
    roof_plate(builder,raised,14.33,'flat mineral roof','North hall/raised deck',.41)


def assemble(builder,lod):
    garden_wing(builder,'west',lod)
    garden_wing(builder,'east',lod)
    central_block(builder,lod)
    garden_arcade(builder,lod)
    domed_tower(builder,lod)
    north_hall(builder,lod)


if __name__=='__main__':
    from final_preview import package
    package(build,HERE,META,PALETTE,assemble)
