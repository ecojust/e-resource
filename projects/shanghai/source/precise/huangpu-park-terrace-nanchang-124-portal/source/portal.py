"""Editable street piers, ironwork and recessed half-round entrance at 124 Nanchang Road."""
from math import sin,cos,pi,hypot
from pathlib import Path
from shapely.geometry import Polygon,box,Point
from shapely.ops import unary_union

PALETTE={
    'wash sandstone':{'color':[.52,.48,.39],'roughness':.91},
    'cream moulding':{'color':[.65,.61,.50],'roughness':.89},
    'sheltered plaster':{'color':[.41,.365,.29],'roughness':.94},
    'pale grey pier stripe':{'color':[.425,.47,.46],'roughness':.89},
    'grey weathering':{'color':[.35,.36,.32],'roughness':.90},
    'stone relief':{'color':[.51,.54,.48],'roughness':.82},
    'dressed base':{'color':[.38,.385,.35],'roughness':.89},
    'painted iron':{'color':[.057,.062,.060],'roughness':.65,'metallic':.23},
    'worn iron edge':{'color':[.104,.116,.108],'roughness':.63,'metallic':.30},
    'dark wooden transom':{'color':[.087,.076,.060],'roughness':.79},
    'shadowed window':{'color':[.126,.163,.166],'roughness':.35,'metallic':.12},
    'enamel green':{'color':[.021,.166,.112],'roughness':.42,'metallic':.11},
    'enamel white':{'color':[.86,.87,.77],'roughness':.57},
}
def slab(b,x,y,z,w,d,h,mat,label):
    b.box((x,y,z),(w,d,h),mat,label=label)

def front(b,polygon,y_outer,y_inner,mat,label):
    b.prism(polygon,-y_inner,-y_outer,lambda x,z,d:(x,-d,z),mat,label)

def tiers(b,x,y,levels,mat,label):
    v=[];f=[(3,2,1,0)]
    for i,(w,d,z) in enumerate(levels):
        v.extend((x+dx*w/2,y+dy*d/2,z) for dx,dy in [(-1,-1),(1,-1),(1,1),(-1,1)])
        if i:
            k=4*(i-1)
            f.extend((k+j,k+(j+1)%4,k+(j+1)%4+4,k+j+4) for j in range(4))
    k=len(v)-4;f.append((k,k+1,k+2,k+3));b.add(v,f,mat,label)

def half_ring(b,profile,lod,label,mat):
    """Rotate the measured moulding section around the front arch axis."""
    count=22 if lod else 64;v=[];faces=[]
    for i in range(count+1):
        a=i*pi/count
        v.extend((r*cos(a),y,3.28+r*sin(a)) for r,y in profile)
    n=len(profile)
    # The profile runs from the inner front edge to outer front, then along the back.
    for i in range(count):
        for j in range(n):
            k=i*n+j;j2=i*n+(j+1)%n
            faces.append((k,j2,j2+n,k+n))
    faces.extend([tuple(range(n-1,-1,-1)),tuple(count*n+j for j in range(n))])
    b.add(v,faces,mat,label)

def front_pier(b,x,y,top,lod,east):
    name='numbered pier' if east else 'shared west pier'
    zc=top/2.55
    tiers(b,x,y,[(.52,.55,0),(.52,.55,.30*zc),(.48,.50,.36*zc)],'dressed base',name+' plinth')
    for i,(lo,hi) in enumerate([(.36,.70),(.714,1.13),(1.145,1.57),(1.585,1.98),(1.994,2.20)]):
        slab(b,x,y,(lo+hi)*zc/2,.47,.48,(hi-lo)*zc,'wash sandstone',name+' course '+str(i+1))
        # The cool grey stripe follows each stone course and leaves the bed joints recessed.
        slab(b,x,y-.2423,(lo+hi)*zc/2,.126,.006,(hi-lo)*zc,'pale grey pier stripe',name+' painted stripe')
    slab(b,x,y,1.27*zc,.428,.43,1.89*zc,'sheltered plaster',name+' joint reveals')
    tiers(b,x,y,[(.47,.48,2.19*zc),(.52,.53,2.218*zc),(.55,.56,2.245*zc),(.55,.56,2.286*zc),
                 (.63,.62,2.303*zc),(.63,.62,2.363*zc),(.55,.54,2.38*zc)],'stone relief',name+' projecting cornice')
    tiers(b,x,y,[(.51,.51,2.38*zc),(.49,.48,2.422*zc),(.36,.36,2.45*zc),
                 (.33,.34,2.495*zc),(.25,.25,2.505*zc),(.23,.24,top)],'cream moulding',name+' stepped crown')
    # The relief is visible at both ends of the 2014 street photograph.
    circle=Point(x,2.06*zc).buffer(.083,resolution=12 if lod else 30)
    front(b,circle,y-.247,y-.235,'grey weathering',name+' roundel shadow')
    front(b,circle.buffer(-.009),y-.255,y-.246,'stone relief',name+' circular relief')
    if east:
        z=1.77
        front(b,box(x-.135,z-.136,x+.135,z+.136),y-.267,y-.247,'enamel green','house number plaque')
        from sign_lettering import lettering_shapes
        from shapely import affinity
        for text,h,width,center in [('124',.125,.224,z+.037),('南昌路',.039,.184,z-.067)]:
            for i,(char,glyph) in enumerate(lettering_shapes(text,width,h,font=Path(__file__).with_name('fonts')/'HouseNumber124.otf')):
                shape=affinity.translate(glyph.simplify(.00045 if lod else .00017,preserve_topology=True),xoff=x,yoff=center)
                front(b,shape,y-.2705,y-.268,'enamel white','plaque '+text+' '+str(i))

def add_portal(b,lod=False):
    # The inner arch has a true vertical reveal, with a separate projecting exterior bead.
    spring=3.28;R=.60;outer=.74;steps=26 if lod else 72
    opening=Polygon([(-R,.045),(R,.045),*[(R*cos(i*pi/steps),spring+R*sin(i*pi/steps))for i in range(steps+1)]])
    edge=Polygon([(-.91,.02),(.91,.02),(.91,spring+.12),(.82,spring+.12),
                  *[(outer*cos(i*pi/steps),spring+outer*sin(i*pi/steps))for i in range(steps+1)],
                  (-.82,spring+.12),(-.91,spring+.12)])
    front(b,edge.difference(opening),.015,.40,'wash sandstone','front arch jambs and vaulted soffit')
    half_ring(b,[(.60,.014),(.605,-.039),(.627,-.055),(.646,-.052),(.65,-.029),(.686,-.029),
                 (.70,-.063),(.72,-.066),(.74,-.036),(.74,.014)],lod,'concentric arch moulding','cream moulding')
    for sign in [-1,1]:
        x=sign*.757
        slab(b,x,.04,1.66,.256,.132,3.04,'wash sandstone','portal pilaster')
        slab(b,x,-.033,1.66,.158,.026,2.78,'cream moulding','smooth pilaster front')
        tiers(b,x,.014,[(.255,.137,3.135),(.283,.155,3.16),(.31,.173,3.19),(.31,.173,3.23),
                        (.366,.215,3.249),(.366,.215,3.295)],'cream moulding','pilaster impost')
        slab(b,x,.02,.12,.30,.21,.22,'dressed base','pilaster foot')
    # Rectangular door and multi-pane ventilation transom behind the shaded arched soffit.
    front(b,opening,.397,.423,'sheltered plaster','recessed portal back')
    slab(b,0,.386,1.22,1.11,.045,2.36,'painted iron','dark inner door')
    slab(b,0,.37,2.695,1.11,.06,.51,'dark wooden transom','transom casing')
    for i in range(4):
        for j in range(2):
            slab(b,-.405+i*.27,.333,2.59+j*.208,.233,.016,.17,'shadowed window','transom light '+str(i*2+j))
    for i in range(2 if lod else 6):
        x=-.46+i*.92/(1 if lod else 5)
        slab(b,x,.354,1.21,.014,.025,2.27,'worn iron edge','inner door vertical rail')
    for side in ['west','east']:
        east=side=='east';front_pier(b,1.79 if east else -.35,-.90 if east else -.68,2.59 if east else 2.50,lod,east)
    # The plain dark outward face is closed in 2014, 2020 and 2023. No hinge swing is inferred.
    l,r=-.106,1.545
    slope=(-.90+.68)/(1.79+.35)
    def gate(x,z,d):return x,-.68+slope*(x+.35)-d,z
    b.prism(box(l,.063,r,2.12),-.045,0,gate,'painted iron','closed outer sheet gate')
    for x in [l+.027,r-.027]:
        b.prism(box(x-.017,.066,x+.017,2.12),.001,.022,gate,'worn iron edge','gate edge rail')
    for z in [.127,2.09]:
        b.prism(box(l+.035,z-.014,r-.035,z+.014),.001,.023,gate,'worn iron edge','gate horizontal rail')
