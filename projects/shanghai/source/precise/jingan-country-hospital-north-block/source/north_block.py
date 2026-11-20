"""Metric reconstruction of the north block and clinic spine, pre-2021 appearance.

X runs towards the viewer's right (west). Y runs inward (towards the south).
The north entrance projection is centred on X=0. Hidden elevations and roof
surfaces take the documented plan and dated aerial outline only.
"""
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

from photo_architecture import Facade, opening
from plaque import add_plaque_text


PALETTE = {
    'cream render': {'color': [.69,.59,.41], 'roughness': .86},
    'ivory trim': {'color': [.80,.73,.55], 'roughness': .75},
    'ochre trim': {'color': [.46,.36,.21], 'roughness': .76},
    'hospital sash': {'color': [.32,.30,.24], 'roughness': .58},
    'old glazing': {'color': [.12,.17,.19], 'roughness': .30, 'metallic': .18},
    'roof surface': {'color': [.32,.32,.29], 'roughness': .92},
    'section render': {'color': [.55,.52,.44], 'roughness': .91},
    'entry recess': {'color': [.09,.08,.06], 'roughness': .9},
    'lantern amber': {'color': [.66,.46,.22], 'roughness': .32},
}

BAR_WIDTH, BAR_DEPTH = 35.4, 14.6
STEM_WIDTH, STEM_LENGTH = 10.5, 18.0
PORTAL_WIDTH, PORTAL_DEPTH = 6.2, 1.9
ROOF = 17.25
RENDER, IVORY, OCHRE = 'cream render', 'ivory trim', 'ochre trim'


def course(face, z, height, projection, mat=IVORY, name='cornice'):
    face.box(0,z,face.length,height,projection+.21,projection/2-.105,mat,name)


def sash(face, shape, lod, tag, columns=2):
    left,bottom,right,top=shape.bounds
    face.prism(shape.buffer(.012,join_style='mitre'),-.34,-.32,'old glazing',tag+' glass')
    inner=shape.buffer(-.075,join_style='mitre')
    grid=[]
    if not lod:
        for i in range(1,columns):
            u=left+(right-left)*i/columns
            grid.append(box(u-.023,bottom,u+.023,top))
        for j in (1,2):
            z=bottom+(top-bottom)*j/3
            grid.append(box(left,z-.021,right,z+.021))
    panes=inner.difference(unary_union(grid)) if grid else inner
    frame=shape.buffer(-.022,join_style='mitre').difference(panes)
    face.prism(frame,-.26,-.19,'hospital sash',tag+' sash')
    face.box((left+right)/2,bottom-.037,right-left+.09,.075,.20,.02,IVORY,tag+' sill')


def glazed(face, u, bottom, width, height, lod, tag, *, columns=2):
    hole = opening(u,bottom,width,height)
    sash(face,hole,lod,tag,columns)
    return hole


def triangular_hood(face, u, z, w, h, lod):
    points=[(u-w/2,z),(u,z+h),(u+w/2,z)]
    face.prism(Polygon(points),-.015,.13,IVORY,'triangular hood')
    ridge=LineString(points).buffer(.078,join_style='mitre',cap_style='flat')
    face.prism(ridge,.12,.27,OCHRE,'hood cap')
    if not lod:
        face.box(u,z-.04,w+.09,.12,.36,.07,IVORY,'hood sill')


def balustrade(face, groups, lod):
    course(face,ROOF+.12,.24,.13)
    course(face,ROOF+1.23,.15,.19)
    pitch=face.length/groups
    for i in range(groups):
        left=-face.length/2+i*pitch
        face.box(left+.22,ROOF+.69,.44,1.06,.36,-.03,RENDER,'parapet pier')
        count=max(3,round(pitch/.50))
        for j in range(1,count+1):
            u=left+.44+(pitch-.48)*j/(count+1)
            if lod:
                face.box(u,ROOF+.69,.12,.96,.17,0,IVORY,'parapet balusters')
            else:
                profile=[(ROOF+.21,.14),(ROOF+.31,.15),(ROOF+.38,.08),
                         (ROOF+.54,.115),(ROOF+.67,.14),(ROOF+.79,.107),
                         (ROOF+.97,.073),(ROOF+1.04,.12),(ROOF+1.13,.14)]
                c=face.point(u,0,-.02)
                face.builder.lathe(c[:2],profile,IVORY,10,face.label+'/turned balusters')
    face.box(face.length/2-.14,ROOF+.69,.28,1.06,.36,-.03,RENDER,'end pier')


def north_window_wall(b, x1, x2, label, lod):
    face=Facade(b,(x1,0),(x2,0),label)
    lower=[-face.length*.35,-face.length*.18,0,face.length*.18,face.length*.35]
    holes=[]
    # The modern view includes paired glass units in the two outer panels,
    # while the 1930s view reads as separate vertical axes.
    for i,u in enumerate(lower):
        arch=opening(u,.52,1.44,2.53,.67,8 if lod else 16)
        sash(face,arch,lod,'base arch')
        holes.append(arch)
        for z in (4.58,8.16):
            holes.append(glazed(face,u,z,1.45,2.34,lod,'lower window'))
    for u,w in [(-face.length*.29,3.6),(0,1.46),(face.length*.29,3.6)]:
        holes.append(glazed(face,u,11.78,w,2.05,lod,'gallery glazing',columns=4 if w>2 else 2))
    for u in lower:
        holes.append(glazed(face,u,15.33,1.47,1.12,lod,'short attic sash'))
    face.wall(.0,ROOF,holes,.37,RENDER)
    for z,h,p in [(3.82,.19,.18),(14.19,.18,.25),(14.47,.23,.44),(16.98,.25,.28)]:
        course(face,z,h,p)
    for i in range(17):
        u=(i-8)*face.length/18
        face.box(u,14.16,.17,.21,.36,.045,OCHRE,'cornice modillion')
    balustrade(face,4,lod)


def east_return(b,lod):
    # From the near NE corner, the image shows three axes and a central high window.
    face=Facade(b,(-BAR_WIDTH/2,BAR_DEPTH),(-BAR_WIDTH/2,.37),'East end')
    holes=[]
    for u in (-3.58,0,3.58):
        arch=opening(u,.53,1.72,2.59,.82,8 if lod else 22)
        sash(face,arch,lod,'ground roundhead')
        holes.append(arch)
        holes.append(glazed(face,u,4.55,1.58,2.43,lod,'hooded sash'))
        holes.append(glazed(face,u,8.16,1.58,2.37,lod,'middle sash'))
        triangular_hood(face,u,7.13,2.1,.62,lod)
    holes.append(glazed(face,0,11.79,1.75,2.07,lod,'upper central sash'))
    holes.append(glazed(face,0,15.29,1.86,1.16,lod,'attic sash'))
    face.wall(0,ROOF,holes,.36,RENDER)
    for u in (-5.4,-1.76,1.76,5.4):
        face.box(u,8.92,.27,10.0,.24,.06,IVORY,'pilaster')
    for z,h,p in [(3.82,.19,.18),(14.19,.18,.25),(14.47,.23,.44),(16.98,.25,.28)]:
        course(face,z,h,p)
    balustrade(face,3,lod)


def lantern(b, x, lod):
    b.box((x,-2.11,2.94),(.18,.45,.16),'aged brass',label='Entrance/lantern bracket')
    b.lathe((x,-2.36),[(2.60,.055),(2.79,.105),(2.91,.19),(2.97,.20)],
            'aged brass',8,'Entrance/lantern base')
    b.lathe((x,-2.36),[(2.97,.18),(3.47,.245)],'lantern amber',6,'Entrance/lantern glass')
    b.lathe((x,-2.36),[(3.44,.26),(3.54,.27),(3.71,.09),(3.76,.045)],
            'aged brass',6,'Entrance/lantern crown')
    if not lod:
        from math import cos, sin, tau
        for j in range(6):
            a=j*tau/6
            b.tube([(x+.18*cos(a),-2.36+.18*sin(a),2.97),
                    (x+.245*cos(a),-2.36+.245*sin(a),3.47)],
                   .015,'aged brass',6,'Entrance/lantern brass ribs')


def north_entry(b,lod):
    half=PORTAL_WIDTH/2
    f=Facade(b,(-half,-PORTAL_DEPTH),(half,-PORTAL_DEPTH),'North entrance')
    arch=opening(0,.10,2.45,4.39,1.16,10 if lod else 30)
    holes=[arch]
    for z,h in [(7.05,1.85),(10.02,2.19),(13.17,2.16),(16.68,1.43)]:
        for u in (-1.89,0,1.89):
            holes.append(glazed(f,u,z,1.19,h,lod,'three vertical sashes'))
    f.wall(0,18.52,holes,.44,RENDER)
    # The open entry leads only to a short, shadowed vestibule in this model.
    f.prism(arch,-1.13,-1.10,'entry recess','door recess backstop')
    lining=arch.buffer(.12,join_style='mitre').difference(arch).intersection(box(-2,0,2,5))
    f.prism(lining,-1.12,-.41,IVORY,'portal reveal')
    f.prism(arch.buffer(.21,join_style='mitre').difference(arch).intersection(box(-2,0,2,5)),
            0,.18,IVORY,'portal jamb and archivolt')
    f.box(0,4.49,.28,.37,.32,.17,OCHRE,'arch keystone')
    for u in (-2.49,2.49):
        f.box(u,2.48,.40,4.84,.25,.09,IVORY,'entry pier')
        lantern(b,u,lod)
    course(f,4.99,.23,.32)
    course(f,6.82,.20,.24)
    f.box(0,5.98,3.54,1.11,.04,.03,IVORY,'inset stone plaque')
    ring=box(-1.83,5.38,1.83,6.58).difference(box(-1.72,5.48,1.72,6.48))
    f.prism(ring,.043,.11,'aged brass','narrow plaque moulding')
    add_plaque_text(b)
    for u in [-2.83,-.96,.96,2.83]:
        f.box(u,11.37,.16,8.80,.17,.035,IVORY,'vertical pier strip')
    for z,h,p in [(15.8,.21,.23),(16.13,.24,.41),(18.42,.20,.26)]:
        course(f,z,h,p)
    # Side returns and plane above the central raised bay only.
    for x in [-half,half]:
        b.box((x,-PORTAL_DEPTH/2,9.26),(.19,PORTAL_DEPTH,18.52),RENDER,label='Entrance/return')
    b.box((0,-PORTAL_DEPTH/2,18.49),(PORTAL_WIDTH,PORTAL_DEPTH,.12),
          'roof surface',label='Entrance/raised roof cap')


def roof_and_spine(b):
    half=BAR_WIDTH/2
    polygon=box(-half,0,half,BAR_DEPTH)
    b.plan_prism(polygon,16.99,ROOF,'roof surface','North block/flat roof')
    b.plan_prism(polygon,.0,.10,'granite base','North block/base')
    # West and inward-facing skins have no verified modern fenestration.
    b.box((half-.14,(BAR_DEPTH+.37)/2,ROOF/2),(.28,BAR_DEPTH-.37,ROOF),'section render',label='West end/estimated plain closure')
    for sign in [-1,1]:
        w=half-STEM_WIDTH/2
        b.box((sign*(half-w/2),BAR_DEPTH-.13,ROOF/2),(w,.26,ROOF),
              'section render',label='North block/court return')
    # Leave the documented middle link continuous with the bar. The lower roof
    # height is estimated from shadows and the 1930s oblique photo.
    short=Facade(b,(half,.37),(half,BAR_DEPTH),'West end')
    course(short,16.98,.25,.23)
    b.box((half,BAR_DEPTH/2,17.76),(.26,BAR_DEPTH,1.08),RENDER,label='West end/plain parapet')
    b.box((0,BAR_DEPTH-.09,17.72),(BAR_WIDTH,.20,.97),RENDER,label='North block/rear parapet')
    front_y=BAR_DEPTH+STEM_LENGTH
    stem=box(-STEM_WIDTH/2,BAR_DEPTH,STEM_WIDTH/2,front_y)
    b.plan_prism(stem,0,.10,'granite base','Clinic/base')
    b.plan_prism(stem,16.12,16.43,'roof surface','Clinic/lower roof')
    for sign in [-1,1]:
        b.box((sign*STEM_WIDTH/2,BAR_DEPTH+STEM_LENGTH/2,8.43),
              (.28,STEM_LENGTH,16.86),'section render',label='Clinic/court faces')
        b.box((sign*STEM_WIDTH/2,BAR_DEPTH+STEM_LENGTH/2,16.86),
              (.35,STEM_LENGTH,.14),IVORY,label='Clinic/parapet cap')
    b.box((0,front_y-.11,8.42),(STEM_WIDTH,.22,16.84),
          'section render',label='Clinic/southern cut at ward')
    b.box((0,BAR_DEPTH-.12,16.91),(STEM_WIDTH,.24,.96),
          'section render',label='North block/junction roof step')


def add_north_block(builder,lod):
    """Append an original pre-lift exterior reconstruction in physical metres."""
    north_window_wall(builder,-BAR_WIDTH/2,-PORTAL_WIDTH/2,'North façade east wing',lod)
    north_window_wall(builder,PORTAL_WIDTH/2,BAR_WIDTH/2,'North façade west wing',lod)
    north_entry(builder,lod)
    east_return(builder,lod)
    roof_and_spine(builder)
