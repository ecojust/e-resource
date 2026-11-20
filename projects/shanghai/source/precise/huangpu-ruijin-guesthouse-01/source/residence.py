"""Court-facing north façade and plan-bound core of Morris Residence No. 1, in metres."""
from math import ceil
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade, opening
from roofscape import BRICK, FRIEZE, GLASS, RIDGE, ROOF, STONE, WINDOW, add_roofs, plate

PALETTE={
    BRICK:{'color':[.42,.17,.11],'roughness':.91},
    'brick joint':{'color':[.31,.19,.15],'roughness':.91},
    STONE:{'color':[.54,.51,.44],'roughness':.82},
    'darkened stone':{'color':[.38,.38,.33],'roughness':.87},
    FRIEZE:{'color':[.25,.23,.18],'roughness':.82},
    GLASS:{'color':[.15,.21,.21],'metallic':.14,'roughness':.34},
    WINDOW:{'color':[.72,.68,.58],'roughness':.70},
    ROOF:{'color':[.43,.23,.16],'roughness':.89},
    RIDGE:{'color':[.49,.27,.19],'roughness':.85},
    'entrance oak':{'color':[.16,.12,.09],'roughness':.69},
    'chimney shadow':{'color':[.13,.12,.10],'roughness':.88},
    'number plaque':{'color':[.15,.15,.13],'roughness':.71},
    'garden threshold':{'color':[.48,.46,.40],'roughness':.87},
}
FOOTPRINT=[(-16.05,.06),(-16.67,5.74),(-18.80,8.28),(-18.34,13.55),(-15.76,15.22),
           (-15.69,20.48),(-8.78,20.60),(-6.96,21.91),(-.05,21.67),(2.48,20.51),
           (13.71,20.48),(13.71,.05)]


def panel(f,x,z,w,h,back,front,mat,name):
    f.box(x,z,w,h,front-back,(back+front)/2,mat,name)


def sash(f,x,z,w,h,lod,label):
    shape=opening(x,z,w,h)
    f.prism(shape.buffer(.012,join_style=2),-.400,-.377,GLASS,label+' recessed glass')
    inset=shape.buffer(-.065,join_style=2)
    cross=[box(x-.032,z,x+.032,z+h),box(x-w/2,z+h*.69-.037,x+w/2,z+h*.69+.037)]
    if not lod:
        cross.extend([box(x+u-.020,z+h*.69,x+u+.020,z+h)for u in [-w/4,w/4]])
    f.prism(shape.buffer(-.012,join_style=2).difference(inset.difference(unary_union(cross))),
            -.350,-.247,WINDOW,label+' ivory sash')
    outline=shape.buffer(.115,join_style=2).difference(shape)
    f.prism(outline,-.03,.083,STONE,label+' shallow stone lining')
    panel(f,x,z-.070,w+.27,.14,-.035,.17,STONE,label+' sill')
    panel(f,x,z+h+.098,w+.31,.12,-.025,.132,STONE,label+' lintel')
    return shape


def quoin(f,x,sgn,bottom,top,lod):
    n=round((top-bottom)/.39)
    for i in range(n):
        width=.47 if i%2 else .67
        panel(f,x+sgn*width/2,bottom+(i+.5)*(top-bottom)/n,width,(top-bottom)/n-.024,
              -.015,.096,STONE,'alternating stone quoins')


def coursing(f,wall,lod):
    # Fine mortar lines across the continuous visible brick bay; the openings
    # and stone jambs cut these lines too. Distant mesh keeps the larger bands.
    if lod:return
    for i in range(1,64):
        z=.14+i*.13
        strip=wall.intersection(box(-f.length/2,z-.006,f.length/2,z+.006))
        if strip.area>.005:
            f.prism(strip,.001,.012,'brick joint','fine horizontal mortar')
    for i in range(1,20):
        z=.17+i*.39
        for j in range(ceil(f.length/.72)):
            x=-f.length/2+.14+j*.72+(i%2)*.34
            stroke=wall.intersection(box(x-.009,z,x+.009,z+.115))
            if stroke.area>.0002:f.prism(stroke,.003,.013,'brick joint','broken brick joints')


def fascia(f,width,height,lod):
    for z,h,front,mat in [(height-.33,.13,.205,STONE),(height-.16,.16,.26,FRIEZE),(height,.15,.37,FRIEZE)]:
        panel(f,0,z,width,h,-.09,front,mat,'moulded eave')
    for i in range(round(width/(.66 if lod else .46))):
        count=round(width/(.66 if lod else .46))
        x=(i+.5)*width/count-width/2
        panel(f,x,height-.236,.11,.19,.06,.26,FRIEZE,'eave brackets')


def courtyard(b,lod):
    for label,x0,x1,y,eave,lower,upper in [
        ('East pavilion',-16.05,-5.18,.05,8.49,[-14.71,-8.86,-6.87],[-14.71,-8.86,-6.87]),
        ('Recessed entrance',-5.18,3.92,.37,8.00,[],[-3.58,-.25,2.66]),
        ('West pavilion',3.92,13.71,.05,8.45,[5.04,6.90,8.76,10.62,12.48],[5.04,6.90,8.76,10.62,12.48])]:
        f=Facade(b,(x0,y),(x1,y),label);mid=(x0+x1)/2;holes=[]
        for zs,positions in [(.98,lower),(4.87,upper)]:
            for j,worldx in enumerate(positions):
                w=.77 if worldx==-14.71 else 1.04 if label=='West pavilion' else 1.34 if worldx==-6.87 else 1.13
                holes.append(sash(f,worldx-mid,zs,w,2.48 if zs<2 else 2.31,lod,'courtyard windows'))
        if label=='Recessed entrance':
            cut=opening(-mid,.16,2.57,3.16)
            holes.append(cut)
            f.prism(cut.buffer(.012,join_style=2),-1.00,-.972,'entrance oak','paired oak doors')
            shape=cut.buffer(-.06,join_style=2)
            for sx in [-.60,.60]:
                pane=box(sx-mid-.39,1.40,sx-mid+.39,2.70)
                f.prism(pane,-.97,-.934,GLASS,'door lights')
                f.prism(pane.buffer(.065,join_style=2).difference(pane),-.946,-.899,FRIEZE,'door panel linings')
            panel(f,-mid,1.74,.075,3.1,-.97,-.91,FRIEZE,'door meeting stile')
            f.prism(cut.buffer(.115,join_style=2).difference(cut).intersection(box(-5,.15,5,3.6)),-1.02,-.28,STONE,'deep stone jambs')
        wall=f.wall(0,eave,holes,.44,BRICK)
        coursing(f,wall,lod)
        if label!='Recessed entrance':
            quoin(f,-f.length/2,1,.25,eave-.39,lod)
            quoin(f,f.length/2,-1,.25,eave-.39,lod)
        if label=='Recessed entrance':
            for lo,hi in [(x0,-1.285),(1.285,x1)]:
                panel(f,(lo+hi)/2-mid,.24,hi-lo,.48,-.05,.10,STONE,'stone base')
        else:
            panel(f,0,.24,f.length,.48,-.05,.10,STONE,'stone base')
        fascia(f,f.length,eave,lod)
        if label=='East pavilion':
            # The narrow outer stone bay has one tall light on each floor.
            # Its heavy ashlar courses turn the corner onto the pictured return.
            outer_half=box(x0-mid,.45,x0+2.15-mid,eave-.40)
            for row in range(17):
                low=.49+row*.44
                course=wall.intersection(outer_half).intersection(box(-f.length/2,low,f.length/2,low+.411))
                f.prism(course,.016,.071,STONE,'narrow stone end bay')
            disk=Point(-f.length/2+.31,2.70).buffer(.19,quad_segs=7 if lod else 16)
            f.prism(disk,.104,.139,'number plaque','villa number plaque')
            numeral=Polygon([(-.047,.054),(-.004,.103),(.027,.103),(.027,-.104),(-.003,-.104),(-.003,.061),(-.025,.030)])
            from shapely.affinity import translate
            f.prism(translate(numeral,xoff=-f.length/2+.31,yoff=2.70),.14,.15,WINDOW,'number 1')
        for x in [-.35*f.length] if label!='Recessed entrance' else []:
            b.tube([f.point(x,.31,.13),f.point(x,7.93,.13),f.point(x+.13,8.05,.17)],.053,
                   'darkened stone',6 if lod else 12,label+'/rainwater pipe')
    for x,side in [(-5.18,1),(3.92,-1)]:
        b.box((x,.20,4.13),(.16,.40,8.26),BRICK,label='Connecting masonry/recess returns')


def parapet(f,z,lod):
    w=f.length
    panel(f,0,z+.095,w,.19,-.20,.145,STONE,'balustrade plinth')
    panel(f,0,z+.91,w+.03,.17,-.22,.16,STONE,'balustrade handrail')
    for x in [-w/2+.17,w/2-.17,0]:
        panel(f,x,z+.49,.34,.84,-.18,.13,'darkened stone','stone parapet piers')
        panel(f,x,z+.88,.43,.13,-.22,.16,STONE,'pier caps')
    for xa,xb in [(-w/2+.36,-.22),(.22,w/2-.36)]:
        count=max(2,round((xb-xa)/(.39 if lod else .31)))
        for j in range(count):
            x=xa+(xb-xa)*(j+.5)/count
            profile=[(.18,.069),(.24,.079),(.30,.046),(.48,.086),(.61,.099),(.74,.048),(.85,.072)]
            f.builder.lathe(f.point(x,0,-.023)[:2],[(z+v,r)for v,r in profile],STONE,6 if lod else 12,f.label+'/stone balusters')


def porch(b,lod):
    x0,x1=-2.35,2.14;y0,y1=-4.99,.60
    floor=Polygon([(x0,y0),(x1,y0),(x1,y1),(x0,y1)])
    b.plan_prism(floor,.02,.15,'garden threshold','Portico/walkable stone threshold')
    for side in [-1,1]:
        for pair in [0,.52]:
            x=(-2.10+pair) if side<0 else (1.89-pair)
            for y in [-4.64,-.42]:
                section=[(.15,.29),(.23,.33),(.33,.31),(.42,.252),(.61,.22),
                         (3.49,.205),(3.68,.22),(3.76,.263),(3.84,.29),(3.94,.29)]
                b.lathe((x,y),section,STONE,10 if lod else 28,'Portico/paired Tuscan shafts')
                b.box((x,y,3.97),(.65,.62,.13),STONE,label='Portico/square capital abaci')
    for z,h,dx,mat in [(4.06,.17,.01,STONE),(4.27,.29,.05,'darkened stone'),(4.45,.12,.10,STONE)]:
        b.plan_prism(floor.buffer(dx,join_style=2),z-h/2,z+h/2,mat,'Portico/projecting entablature')
    a=(x0,y0);b0=(x1,y0);c=(x1,.36);d=(x0,.36)
    for start,end,name in [(a,b0,'front'),(b0,c,'west return'),(d,a,'east return')]:
        f=Facade(b,start,end,'Balcony '+name)
        parapet(f,4.51,lod)
        n=max(3,round(f.length/.30))
        for j in range(n):
            u=(j+.5)*f.length/n-f.length/2
            panel(f,u,4.23,.085,.15,.052,.108,STONE,'frieze dentils')


def add_residence(b,lod):
    courtyard(b,lod);porch(b,lod)
    footprint=Polygon(FOOTPRINT)
    b.plan_prism(footprint,.01,.09,'darkened stone','Main block/enclosed floor')
    b.plan_prism(footprint,7.99,8.09,FRIEZE,'Main block/roof support')
    # Back and canted ends follow the attributed site plan. Openings are confined
    # to the pictured east return. The remainder is intentionally unarticulated.
    for j,(a,c) in enumerate(zip(FOOTPRINT,FOOTPRINT[1:])):
        f=Facade(b,c,a,'Core returns')
        h=8.06;holes=[]
        if j==0:
            for z in [.98,4.87]:
                holes.append(sash(f,.48,z,.90,2.23,lod,'east return narrow light'))
        f.wall(0,h,holes,.34,BRICK)
        panel(f,0,.23,f.length,.46,-.05,.08,STONE,'base stonework')
        if j in [0,3,5,8]:
            quoin(f,-f.length/2,1,.25,7.75,lod)
    eastbay=Polygon([(-16.15,5.62),(-16.76,5.74),(-18.95,8.21),(-18.51,13.62),(-15.72,15.36),(-15.66,5.62)])
    for a,c in zip(eastbay.exterior.coords,list(eastbay.exterior.coords)[1:]):
        plate(b,[(*a,8.14),(*c,8.14),(-15.3,10.62,9.45)],ROOF,'East side/canted bay roof')
    add_roofs(b,lod)
