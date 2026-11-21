"""Seven-storey Arnhold street frontage, including the west numbered door and the south stone arch."""
from math import ceil,cos,pi,sin
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,box,LineString,Point
from shapely.ops import unary_union
from photo_architecture import Facade
from brick_mapping import ARC_CENTER,ARC_FIRST,ARC_LENGTH,BRICK,CORNER_RADIUS,EDGES,brick_uv

MORTAR='Rusticated red joints'
BELT='Pale cement stringcourses'
GLASS='Smoky street glazing'
FRAME='Dark sash joinery'
REVEAL='Dark window recess'
SILL='Weathered grey sill stone'
PLINTH='Street-level ashlar'
LIGHT='Cool-grey plaster architrave'
BLUE='Blue metal street fascia'
HOOD='Blue-green window hood'
GOLD='Old gold building letters'
IRON='Black drainpipes and roof iron'
GALV='Weathered condenser steel'
LEAD='Dark roof flashing'
PALETTE={
    BRICK:{'color':[1.,1.,1.],'roughness':.92,'texture':str(Path(__file__).with_name('arnhold-red-brick.png'))},
    MORTAR:{'color':[.43,.258,.218],'roughness':.89},BELT:{'color':[.78,.752,.69],'roughness':.87},
    GLASS:{'color':[.173,.209,.224],'metallic':.21,'roughness':.31},FRAME:{'color':[.175,.168,.15],'roughness':.61},
    REVEAL:{'color':[.124,.123,.112],'roughness':.76},SILL:{'color':[.49,.454,.396],'roughness':.88},
    PLINTH:{'color':[.642,.610,.540],'roughness':.88},LIGHT:{'color':[.646,.676,.665],'roughness':.82},
    BLUE:{'color':[.110,.375,.538],'metallic':.39,'roughness':.38},HOOD:{'color':[.135,.435,.467],'metallic':.19,'roughness':.64},
    GOLD:{'color':[.677,.53,.292],'metallic':.56,'roughness':.47},IRON:{'color':[.165,.170,.162],'metallic':.34,'roughness':.60},
    GALV:{'color':[.56,.561,.532],'metallic':.30,'roughness':.59},LEAD:{'color':[.351,.355,.329],'roughness':.82},
}
SASHES=((4.99,7.42),(8.79,11.34),(12.72,15.22),(16.71,18.73),(20.16,21.92),(23.71,25.39))
COURSES=((4.55,4.80),(7.89,8.21),(11.99,12.32),(15.95,16.25),(19.33,19.64))
ROOF=26.59


class RoundCorner:
    """A single street abscissa across the curved corner; normals follow the masonry."""
    def __init__(self,builder,lod):
        self.builder=builder
        self.length=ARC_LENGTH
        self.label='Corner'
        self.divisions=8 if lod else 16

    def point(self,u,z,d=0):
        ang=ARC_FIRST+(u+self.length/2)/CORNER_RADIUS
        return np.array([ARC_CENTER[0]+(CORNER_RADIUS+d)*cos(ang),ARC_CENTER[1]+(CORNER_RADIUS+d)*sin(ang),z])

    def prism(self,poly,back,front,material=BRICK,label='Wall'):
        if poly.is_empty:return
        a,x0,c,x1=poly.bounds
        strips=ceil(max(1,(c-a)*self.divisions/self.length))
        for n in range(strips):
            u=a+(c-a)*n/strips;v=a+(c-a)*(n+1)/strips
            part=poly.intersection(box(u,x0-.001,v,x1+.001))
            if part.area>1e-7:self.builder.prism(part,back,front,self.point,material,self.label+'/'+label)

    def box(self,u,z,w,h,depth=.3,d=0,material=BRICK,label='Wall'):
        self.prism(box(u-w/2,z-h/2,u+w/2,z+h/2),d-depth/2,d+depth/2,material,label)


def arch(cx,width,bottom,shoulder,rise,segments=24):
    apex=[(cx+width*.5*cos(pi*i/segments),shoulder+rise*sin(pi*i/segments))for i in range(segments+1)]
    return Polygon([(cx-width/2,bottom),(cx+width/2,bottom),*apex])


def window(face,x,span,z0,z1,arched,lod,hood=False):
    shoulder=z1-.37 if arched else z1
    opening=(arch(x,span,z0,shoulder,z1-shoulder)if arched else box(x-span/2,z0,x+span/2,z1))
    frame=opening.difference(opening.buffer(-.068,join_style='mitre'))
    inner=opening.buffer(-.054,join_style='mitre')
    mullions=[box(x-.032,z0,x+.032,z1)]
    if span>2.0:
        for offset in (-span/4,span/4):mullions.append(box(x+offset-.023,z0,x+offset+.023,z1))
    hbar=z0+(z1-z0)*.67
    mullions.append(box(x-span/2,hbar-.032,x+span/2,hbar+.032))
    if not lod and span>1.35:
        mullions.append(box(x-span/2,z0+(z1-z0)*.30-.014,x+span/2,z0+(z1-z0)*.30+.014))
    face.prism(opening,-.34,-.315,GLASS,'Recessed panes')
    face.prism(unary_union([frame,inner.intersection(unary_union(mullions))]),-.290,-.220,FRAME,'Sash rails')
    face.box(x,z0-.076,span+.19,.142,.237,.04,SILL,'Projecting sill')
    if arched:
        outer=arch(x,span+.36,shoulder-.012,shoulder,z1-shoulder+.19)
        inn=arch(x,span-.015,shoulder-.08,shoulder,z1-shoulder)
        face.prism(outer.difference(inn),.015,.107,MORTAR,'Segmental brick arches')
    if hood:
        # Individual hoods survive above the surveyed windows. Their front edge drops.
        face.box(x,z1+.067,span+.19,.067,.39,.15,HOOD,'Awning plate')
        face.box(x,z1+.020,span+.18,.096,.045,.323,HOOD,'Awning edge')
    return opening


def portal_west(face,x,lod):
    opening=arch(x,1.79,.070,2.23,.805)
    upr=box(x-1.59,.035,x+1.59,3.83)
    face.prism(upr.difference(opening),-.30,.105,LIGHT,'Painted portal surround')
    archtrim=arch(x,1.99,.060,2.23,.920).difference(opening)
    face.prism(archtrim,-.01,.142,SILL,'Dark arch reveal')
    face.prism(opening,-.450,-.421,GLASS,'Paired door glazing')
    rails=[box(x-.043,.085,x+.043,2.24),box(x-1.,2.195,x+1.,2.275)]
    for dx in [-.59,-.287,.287,.59]:rails.append(box(x+dx-.016,.159,x+dx+.016,2.19))
    for h in [.42,.88,1.32,1.77]:rails.append(box(x-.88,h-.015,x+.88,h+.015))
    for dx in [-.60,.00,.60]:
        face.builder.tube([face.point(x,2.24,-.30),face.point(x+dx,2.25+.75*(1-(dx/.88)**2)**.5,-.30)],.019,FRAME,5,face.label+'/Fanlight bars')
    face.prism(opening.intersection(unary_union(rails)),-.325,-.276,FRAME,'Entrance glazing bars')
    face.box(x,.037,1.94,.074,.49,-.12,SILL,'Door threshold')
    for dx in (-1.40,1.40):
        face.box(x+dx,1.82,.23,3.54,.235,.136,BELT,'Portal piers')
        face.box(x+dx,.43,.34,.69,.263,.145,LIGHT,'Pier feet')
        face.box(x+dx,3.46,.37,.30,.339,.148,BELT,'Pier capitals')
        face.box(x+dx,.48,.13,.14,.025,.28,SILL,'Pier inset medallions')
    for z,w,h,d in [(3.79,3.61,.15,.51),(3.66,3.37,.10,.36),(3.08,2.47,.088,.212)]:
        face.box(x,z,w,h,d,.10,SILL if z>3.7 else BELT,'Door head mouldings')
    for dx in (-.90,-.66,.66,.90):
        face.box(x+dx,3.25,.114,.13,.044,.133,SILL,'Lintel relief')
    face.box(x+1.65,1.60,.34,.247,.038,.12,PLINTH,'Municipal protection plaque')
    from shapely import set_precision
    from shapely.affinity import translate
    from sign_lettering import lettering_shapes
    font=Path(__file__).with_name('arnhold-sign.otf')
    for _,sign in lettering_shapes('安利大楼',1.70,.285,font=font):
        glyph=set_precision(translate(sign.simplify(.0022 if lod else .0009),xoff=x,yoff=3.435),.0003)
        face.prism(glyph,.125,.157,GOLD,'Four building-name characters')
    return upr


def portal_south(face,x,lod):
    opening=arch(x,1.94,.06,2.21,.968)
    face.prism(opening,-.705,-.682,REVEAL,'South arch recess')
    ring=arch(x,2.57,.00,2.21,1.285).difference(opening)
    face.prism(ring,-.37,.123,PLINTH,'South rusticated arch')
    for j in range(1,12):
        a=pi*j/12
        points=[face.point(x+r*cos(a),2.21+r*sin(a),.13)for r in [.98,1.27]]
        face.builder.tube(points,.013,SILL,4,face.label+'/Voussoir joints')
    for sign in [-1.,1.]:
        for z in (.47,.92,1.37,1.82,2.20):face.box(x+sign*1.13,z,.31,.022,.026,.13,SILL,'Arch pier bedding')
    keystone=Polygon([(x-.125,3.21),(x+.125,3.21),(x+.217,3.62),(x-.217,3.62)])
    face.prism(keystone,.134,.216,BELT,'Crown stone')
    return opening


def shop_opening(face,x,span,door,lod):
    low=.072 if door else .62
    rect=box(x-span/2,low,x+span/2,3.01)
    face.prism(rect,-.418,-.397,GLASS if not door else REVEAL,'Dark shop openings')
    rim=rect.difference(rect.buffer(-.077,join_style='mitre'))
    face.prism(rim,-.34,-.283,FRAME,'Shop frame')
    if not door:
        for frac in [-.25,0,.25]:face.box(x+span*frac,(3.0+low)/2,.035,3.0-low,.045,-.32,FRAME,'Shop sash')
    return rect


def condenser(face,x,z,lod):
    face.box(x,z,.74,.55,.40,.26,GALV,'Condenser case')
    fan=[(x+.02+.215*cos(2*pi*i/16),z+.215*sin(2*pi*i/16))for i in range(16)]
    face.prism(Polygon(fan),.465,.471,FRAME,'Condenser intake')
    if not lod:
        for rad in [.086,.147,.195]:
            pts=[face.point(x+.02+rad*cos(2*pi*i/20),z+rad*sin(2*pi*i/20),.484)for i in range(21)]
            face.builder.tube(pts,.011,GALV,4,face.label+'/Fan guards')
        for dx in [-.247,.241]:
            face.builder.tube([face.point(x+dx,z-.30,.002),face.point(x+dx,z-.30,.39)],.023,IRON,5,face.label+'/Unit brackets')


def sashes(face,side,lod):
    h=face.length/2
    if side=='Sichuan':
        axes=[(-h+1.78,2.35),(-h+5.83,2.39),(-h+9.94,2.29)]
    elif side=='Jiujiang':
        axes=[(-h+2.02,2.49),(-h+5.95,2.54),(-h+9.73,2.51),(-h+13.24,2.49),(-h+16.76,2.06)]
    else:axes=[(-face.length*.242,1.34),(face.length*.242,1.34)]
    cuts=[]
    for i,(x,span) in enumerate(axes):
        for f,(z0,z1) in enumerate(SASHES):
            width=span*(.85 if f>=4 and side!='Corner' else 1.)
            arched=side=='Jiujiang' and i in (3,4) and f==3
            has_hood=(side=='Corner' and f==3) or (side=='Jiujiang' and f in [0,1,2,3] and i in [2,4]) or (side=='Sichuan' and f==3 and i in [0,1,2])
            cuts.append(window(face,x,width,z0,z1,arched,lod,has_hood))
    return axes,unary_union(cuts)


def layered_cornice(face,lod):
    half=face.length/2
    for a,b in COURSES:
        face.prism(box(-half,a,half,b),.006,.057,BELT,'Pale storey bands')
    for bottom,top,off,depth in [(22.31,22.43,.038,.105),(22.44,22.52,.074,.15),
                                 (22.64,22.76,.15,.30),(22.78,22.86,.215,.43),
                                 (22.86,23.02,.264,.54),(23.02,23.10,.295,.60),
                                 (26.12,26.25,.085,.185),(26.25,26.36,.137,.29),
                                 (26.36,26.52,.168,.35),(26.52,26.59,.20,.41)]:
        face.box(0,(bottom+top)/2,face.length,top-bottom,depth,off,BELT if bottom>23 else SILL,'Built-up cornices')
    count=max(3,round(face.length/.48))
    for i in range(count):
        x=-half+face.length*(i+.5)/count
        face.box(x,22.581,.228,.225,.261,.088,SILL,'Cornice modillions')
        if not lod:face.box(x,22.535,.154,.104,.229,.159,BELT,'Modillion lower lip')
    count=ceil(face.length/.52)
    for i in range(count+1):
        if i==count and face.label!='Jiujiang':continue
        x=-half+face.length*i/count
        face.builder.tube([face.point(x,ROOF,-.123),face.point(x,27.30,-.123)],.021,IRON,5,face.label+'/Rooftop guard uprights')
    for z in [26.86,27.30]:
        n=18 if face.label=='Corner' else 1
        face.builder.tube([face.point(-half+face.length*i/n,z,-.123)for i in range(n+1)],.025,IRON,6,face.label+'/Rooftop guard rails')


def masonry(face,side,upper_holes,lod):
    half=face.length/2
    shape=box(-half,4.20,half,26.39)
    face.prism(shape.difference(upper_holes),-.35,-.005,BRICK,'Red window wall')
    # The 2020 and 2023 close views show narrow raised courses around the
    # rounded corner; the broad straight street panels remain in running bond.
    if side=='Corner':
        relief_zone=shape.intersection(box(-half,4.8,half,19.53)).difference(upper_holes.buffer(.075,join_style='mitre'))
        for i in range(36):
            z=4.83+i*.418
            band=box(-half,z,half,z+.032).intersection(relief_zone)
            face.prism(band,.006,.019,MORTAR,'Corner rustication')
    elif side=='Jiujiang':
        zone=shape.intersection(box(-half+14.95,4.8,half,19.81)).difference(upper_holes.buffer(.065,join_style='mitre'))
        for i in range(35):
            z=4.85+i*.413
            face.prism(zone.intersection(box(-half,z,half,z+.024)),.005,.020,MORTAR,'East bay brick courses')
    layered_cornice(face,lod)


def street_level(face,side,lod):
    h=face.length/2;cuts=[]
    if side=='Sichuan':
        door=h-(10.33-3.43)
        cuts.append(portal_west(face,door,lod))
        for u,width in [(-h+1.68,2.27),(h-2.08,2.42)]:cuts.append(shop_opening(face,u,width,False,lod))
        fascia=(h-4.38,h)
    elif side=='Corner':
        for sign in (-1,1):cuts.append(shop_opening(face,sign*face.length*.24,1.47,True,lod))
        fascia=(-h,h)
    else:
        for dx,width in [(2.02,2.51),(5.95,2.27),(9.73,2.54),(13.24,1.98)]:
            cuts.append(shop_opening(face,-h+dx,width,False,lod))
        south_arch=-h+16.55
        cuts.append(portal_south(face,south_arch,lod))
        fascia=(-h,-h+13.44)
    all_cuts=unary_union(cuts)
    stone=box(-h,0,h,4.41).difference(all_cuts)
    face.prism(stone,-.418,-.036,PLINTH,'Ground-floor ashlar')
    for i in range(1,10):
        z=.46*i
        line=stone.intersection(box(-h,z-.013,h,z+.013))
        face.prism(line,-.034,-.022,SILL,'Horizontal ashlar joints')
    if not lod:
        for i in range(9):
            for j in range(1,ceil(face.length/.98)):
                u=-h+(j+(i%2)*.5)*.98
                segment=stone.intersection(box(u-.007,i*.46,u+.007,(i+1)*.46))
                face.prism(segment,-.033,-.023,SILL,'Staggered stone joints')
    lo,hi=fascia
    face.prism(box(lo,3.19,hi,4.72),.023,.185,BLUE,'Blue fascia')
    for z,alt,d in [(3.148,3.223,.223),(4.707,4.784,.204)]:
        face.prism(box(lo,z,hi,alt),.035,d,LEAD,'Metal fascia edges')


def drains(face,locations,lod):
    for x in locations:
        face.builder.tube([face.point(x,z,.095)for z in [4.76,22.29,22.90,26.24]],.045,IRON,6 if lod else 10,face.label+'/Rainwater pipes')
        if not lod:
            for z in [6.5,10.5,14.4,18.5,21.6,24.7]:
                face.box(x,z,.146,.025,.126,.054,IRON,'Drain brackets')


def roof_lip(builder,faces):
    west,corner,south=faces
    line=[tuple(west.point(-west.length/2,0,0)[:2]),tuple(west.point(west.length/2,0,0)[:2])]
    for i in range(1,21):line.append(tuple(corner.point(-corner.length/2+corner.length*i/20,0,0)[:2]))
    line.append(tuple(south.point(south.length/2,0,0)[:2]))
    top=LineString(line).buffer(3.36,single_sided=True,join_style='mitre',cap_style='flat')
    builder.plan_prism(top,ROOF-.36,ROOF-.12,LEAD,'Street roof ribbon')
    points=list(top.exterior.coords)
    for a,b in zip(points,points[1:]):
        center=((a[0]+b[0])/2,(a[1]+b[1])/2)
        if LineString(line).distance(Point(center))<.18:continue
        rear=Facade(builder,a,b,'Inner return')
        rear.prism(box(-rear.length/2,22.38,rear.length/2,ROOF-.12),-.13,0,LEAD,'Unadorned roof connection')


def add_building(builder,lod=False):
    faces=[Facade(builder,*EDGES['Sichuan'],'Sichuan'),RoundCorner(builder,lod),Facade(builder,*EDGES['Jiujiang'],'Jiujiang')]
    for face in faces:
        axes,holes=sashes(face,face.label,lod)
        masonry(face,face.label,holes,lod)
        street_level(face,face.label,lod)
        if face.label=='Corner':
            drains(face,[0.0],lod)
            condenser(face,axes[0][0]+.12,16.56,lod)
        if face.label=='Jiujiang':
            drains(face,[-face.length/2+7.81,-face.length/2+14.91],lod)
            for i,j,delta in [(1,1,.30),(1,2,-.40),(2,0,.51),(2,2,.46),(3,1,-.83),(3,2,.84),(4,3,-.46)]:
                condenser(face,axes[i][0]+delta,SASHES[j][0]-.21,lod)
        if face.label=='Sichuan':
            drains(face,[-face.length/2+4.17],lod)
            for i,z in [(1,12.5),(1,16.57),(0,8.57)]:condenser(face,axes[i][0]+.27,z,lod)
    roof_lip(builder,faces)
    for part in builder.parts:
        if part['material']==BRICK:
            part['texcoords']=[(u,1-v)for u,v in (brick_uv(part['label'],pt)for pt in part['vertices'])]
