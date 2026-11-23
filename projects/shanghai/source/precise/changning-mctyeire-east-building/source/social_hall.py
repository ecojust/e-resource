"""McTyeire Social Hall's photographed courtyard elevation, locally in metres."""
from math import ceil
import numpy as np
from shapely import union_all
from shapely.geometry import box, Polygon, LineString
from photo_architecture import Facade, opening
from lawn_return import add_lawn_return

PALETTE = {
    'court ashlar': {'color':[.66,.614,.483], 'roughness':.84},
    'cream dressings': {'color':[.77,.704,.553], 'roughness':.79},
    'alternating quoins': {'color':[.56,.514,.388], 'roughness':.81},
    'porch stone': {'color':[.53,.491,.371], 'roughness':.83},
    'horizontal bed joint': {'color':[.39,.368,.294], 'roughness':.9},
    'frieze recess': {'color':[.254,.228,.162], 'roughness':.88},
    'old mahogany': {'color':[.176,.112,.071], 'roughness':.54},
    'amber leaded glass': {'color':[.219,.199,.137], 'roughness':.28, 'metallic':.16},
    'dark lead': {'color':[.082,.086,.077], 'roughness':.61, 'metallic':.27},
    'casement glass': {'color':[.142,.178,.172], 'roughness':.25, 'metallic':.18},
    'dark casement': {'color':[.157,.144,.105], 'roughness':.59},
    'burnt clay tiles': {'color':[.38,.146,.076], 'roughness':.84},
    'sunlit tile lips': {'color':[.417,.174,.095], 'roughness':.76},
    'dormer cheeks': {'color':[.341,.297,.215], 'roughness':.82},
    'gallery paving': {'color':[.378,.365,.302], 'roughness':.88},
    'section stone': {'color':[.47,.454,.389], 'roughness':.92},
}

def solid(b,name,material,x,y,z,w,d,h):
    b.box((x,y,z),(w,d,h),material,label=name)

def tudor(u,z,width,top,rise):
    # The photographed shallow Tudor opening has a short steep spring, rounded
    # shoulders and a straight shallow curve meeting at a small central point.
    half=width/2
    offsets=[(-1,0),(-.99,.18),(-.94,.34),(-.78,.52),(-.42,.73),(0,1),
             (.42,.73),(.78,.52),(.94,.34),(.99,.18),(1,0)]
    crown=[(u+dx*half,top-rise+dz*rise) for dx,dz in offsets]
    return Polygon([(u-half,z),(u+half,z),*reversed(crown)])

def fenestration(f,u,z,w,h,lights,lod,kind='plain'):
    shape=opening(u,z,w,h)
    leaded=kind=='diamond'
    glass='amber leaded glass' if leaded else 'casement glass'
    f.prism(shape.buffer(.012,join_style=2),-.36,-.33,glass,'recessed glass')
    inner=shape.buffer(-.09,join_style=2)
    bars=[box(u-w/2+w*i/lights-.062,z-.02,u-w/2+w*i/lights+.062,z+h+.02) for i in range(1,lights)]
    transom=z+h*(.52 if leaded else .70)
    bars.append(box(u-w/2-.02,transom-.065,u+w/2+.02,transom+.065))
    frame=shape.buffer(-.035,join_style=2).difference(inner.difference(union_all(bars)))
    f.prism(frame,-.295,-.13,'cream dressings' if lights>1 else 'dark casement','casement and transom')
    if leaded:
        # Diagonal lead is clipped to the individual leaded lights and is a
        # single solid at each intersection, in front of the recessed glass.
        pane=inner.difference(union_all(bars))
        lines=[]
        step=.72 if lod else .48
        for dx in np.arange(-w/2-h,w/2+h,step):
            for slope in (-.53,.53):
                lines.append(LineString([(u+dx,z),(u+dx+slope*h,z+h)]))
        lattice=union_all(lines).buffer(.016 if lod else .013,cap_style='flat').intersection(pane)
        f.prism(lattice,-.32,-.301,'dark lead','diamond lead cames')
    if not lod:
        # The stone mullions return to darker frames around each separate pane.
        pane=inner.difference(union_all(bars))
        lining=pane.difference(pane.buffer(-.048,join_style=2))
        f.prism(lining,-.297,-.246,'dark casement','rebated pane borders')
    border=shape.buffer(.14,join_style=2).difference(shape)
    f.prism(border,-.01,.069,'cream dressings','individual window surround')
    if not lod:
        hood=shape.buffer(.19,join_style=2).difference(shape.buffer(.14,join_style=2))
        f.prism(hood,-.021,.024,'alternating quoins','outer casing rebate')
    f.box(u,z-.058,w+.34,.116,.26,.04,'alternating quoins','projecting sill')
    return shape

def tile_roof(b,name,x0,x1,front,eave,back,rise_rate,lod):
    depth=back-front
    # A closed longitudinal slice of the continuous tiled front slope.
    f=Facade(b,(x0,back),(x0,front),name+'/nearer gable')
    profile=Polygon([(-depth/2,eave+rise_rate*depth),(depth/2,eave),(depth/2,eave-.24),(-depth/2,eave-.24)])
    f.prism(profile,-(x1-x0),0,'burnt clay tiles','sloped clay field')
    steps=ceil(depth/(.73 if lod else .38))
    for i in range(steps):
        y=front+(i+.18)*depth/steps
        z=eave+rise_rate*(y-front)
        solid(b,name+'/clay course noses','sunlit tile lips',(x0+x1)/2,y,z+.028,x1-x0,.085,.070)
    solid(b,name+'/shadow eave','dormer cheeks',(x0+x1)/2,front+.055,eave-.15,x1-x0,.21,.19)

def limestone_gable(f,width,base,rise,tip,distance):
    peak=Polygon([(-width/2,base),(width/2,base),(0,base+rise)])
    f.prism(peak,-.27,.041,'court ashlar','gable wall')
    path=LineString([(-width/2,base),(0,base+rise),(width/2,base)])
    f.prism(path.buffer(tip,cap_style='flat',join_style='mitre'),-.31,distance,'cream dressings','sloping stone coping')
    return peak

def dormer(b,x,y,eave,slope,lod,label):
    # Roof recedes into the existing plane, so there is no floating rear wall.
    width=1.88
    depth=1.43/slope
    z=eave-.07
    face=Facade(b,(x-width/2,y),(x+width/2,y),label+'/dormer')
    hole=opening(0,z+.13,1.24,1.13)
    face.wall(z,z+1.47,[hole],.18,'cream dressings')
    fenestration(face,0,z+.13,1.24,1.13,2,lod)
    for s in (-1,1):
        pos=x+s*width/2
        side=Facade(b,(pos,y+depth),(pos,y),label+'/roof cheek') if s<0 else Facade(b,(pos,y),(pos,y+depth),label+'/roof cheek')
        verts=[(-depth/2,z),(-depth/2,z+1.47),(depth/2,z+1.47),(depth/2,z+slope*depth-.22)] if s>0 else [(-depth/2,z+slope*depth-.22),(-depth/2,z+1.47),(depth/2,z+1.47),(depth/2,z)]
        side.prism(Polygon(verts),-.11,.02,'dormer cheeks','returned dormer')
    l,r=x-width*.62,x+width*.62;low=z+1.46;hi=z+1.86
    pts=[(l,y-.18,low),(r,y-.18,low),(r,y+depth+.08,low),(l,y+depth+.08,low),
         (x,y+.28,hi),(x,y+depth-.16,hi)]
    b.add(pts,[(0,1,4),(1,2,5,4),(2,3,5),(3,0,4,5),(3,2,1,0)],'burnt clay tiles',label+'/hipped dormer cap')

def return_gable(b,x,y0,y1,ridge,eave,peak,label):
    f=Facade(b,(x,y1),(x,y0),label) if x<0 else Facade(b,(x,y0),(x,y1),label)
    front=f.point(0,0)[1]
    u=lambda y:(front-y) if x<0 else (y-front)
    pts=[(u(y0),eave),(u(ridge),peak),(u(y1),peak-(y1-ridge)*.80),(u(y1),0),(u(y0),0)]
    shape=Polygon(pts)
    holes=[]
    for lower in (5.9,10.25):
        for d in (1.04,2.55):
            holes.append(fenestration(f,u(y0+d),lower,.88,2.27,1,False))
    f.wall(0,peak,holes,.30,'court ashlar',shape)
    arr=[(u(y0),eave),(u(ridge),peak),(u(y1),peak-(y1-ridge)*.80)]
    f.prism(LineString(arr).buffer(.13,cap_style='flat'),-.29,.11,'cream dressings','gable verge')
    for z in np.arange(1.05,peak,.99):
        strip=shape.intersection(box(-64,z-.012,64,z+.012)).difference(union_all(holes))
        if strip.area>.0001:f.prism(strip,.001,.019,'horizontal bed joint','stone courses')

def wing(b,x0,x1,y,lod,label):
    w=x1-x0;mid=(x0+x1)/2
    f=Facade(b,(x0,y),(x1,y),label+'/upper walls')
    windows=[]
    for level in (5.92,10.12):
        for i in range(8):
            windows.append(fenestration(f,(i-3.5)*w/8,level,1.72,2.31,2,lod))
    f.wall(4.80,13.41,windows,.42,'court ashlar')
    for z in (8.84,13.26):f.beam(z,.11,.16,'cream dressings',width=w,label='string course')
    y_arcade=y-1.83
    gallery=Facade(b,(x0,y_arcade),(x1,y_arcade),label+'/six Tudor bays')
    spacing=w/6
    arches=[tudor((i-2.5)*spacing,-.03,spacing-.57,3.49,.71) for i in range(6)]
    gallery.wall(0,4.89,arches,.61,'court ashlar')
    for a in arches:
        ring=a.buffer(.13,join_style=2).difference(a).intersection(box(-w/2,.18,w/2,4.10))
        gallery.prism(ring,-.015,.087,'cream dressings','Tudor arch voussoir border')
        if not lod:
            u=(a.bounds[0]+a.bounds[2])/2
            for q in (-.81,-.48,0,.48,.81):
                k=u+q*(spacing-.57)/2
                joint=LineString([(k-.038*q,2.65),(k+.12*q,3.73)]).buffer(.017,cap_style='flat').intersection(ring)
                if joint.area>.0001:gallery.prism(joint,.087,.101,'horizontal bed joint','voussoir joints')
    gallery.beam(4.82,.18,.24,'cream dressings',width=w,label='terrace parapet top')
    gallery.beam(3.76,.13,.29,'alternating quoins',width=w,label='arcade horizontal band')
    for i in range(1,6):
        u=(i-3)*spacing
        gallery.box(u,.48,.66,.93,.69,-.24,'porch stone','pier foot')
    solid(b,label+'/arcade gallery floor','gallery paving',mid,y_arcade+1.71,.085,w,3.40,.17)
    solid(b,label+'/terrace slab','cream dressings',mid,y_arcade+.99,4.02,w,1.95,.19)
    far=Facade(b,(x0,y_arcade+3.19),(x1,y_arcade+3.19),label+'/gallery inner wall')
    bg=[]
    for i in range(6):
        a=(i-2.5)*spacing
        bg.append(fenestration(far,a,.72,1.48,2.31,2,lod))
    far.wall(.16,4.90,bg,.33,'porch stone')
    tile_roof(b,label+'/clay roof',x0,x1,y-.30,13.57,11.65,.46,lod)
    for i in range(4):
        yy=y+1.51;dormer(b,mid+(i-1.5)*w/4,yy,13.57+.46*(yy-y+.30),.46,lod,label)
    # The back face is simply the section through the long school building.
    zh=13.57+.46*(11.65-y+.30)
    solid(b,label+'/roof section','section stone',mid,11.59,zh/2,w,.12,zh)
    # At each end the retained U-wing continues at coarse height. Close
    # the taller exposed model section at that original wall junction.
    x=x0 if x0<0 else x1
    a,c=(x,11.65),(x,y-.30)
    if x>0:a,c=c,a
    end=Facade(b,a,c,label+'/outer section')
    ua,uc=-end.length/2,end.length/2
    za,zc=(zh,13.57) if x<0 else (13.57,zh)
    end.prism(Polygon([(ua,.17),(uc,.17),(uc,zc),(ua,za)]),-.12,0,'section stone','closed joint')


def portal(b,lod):
    width=5.83;depth=3.21;front=-3.51;top=6.36
    f=Facade(b,(-width/2,front),(width/2,front),'carved central porch')
    hole=tudor(0,-.02,4.58,4.60,.97)
    f.wall(0,top,[hole],.64,'porch stone')
    ring=hole.buffer(.14,join_style=2).difference(hole).intersection(box(-width/2,.18,width/2,5.01))
    f.prism(ring,0,.068,'cream dressings','low pointed front lintel')
    for s in (-1,1):
        x=s*width/2
        side=Facade(b,(x,front+depth),(x,front),'porch side arc') if s<0 else Facade(b,(x,front),(x,front+depth),'porch side arc')
        side.wall(0,top,[tudor(0,-.03,2.13,4.59,1.24)],.40,'porch stone')
    f.beam(top,.16,.17,'cream dressings',width=width+.20,label='carved porch cornice')
    for i in range(10):
        u=(i-4.5)*.50; z=5.82
        p=Polygon([(u-.20,z),(u,z+.26),(u+.20,z),(u,z-.19)])
        f.prism(p,.006,.029,'frieze recess','diamond frieze recesses')
        f.prism(p.buffer(.044,join_style=2).difference(p),.016,.105,'cream dressings','diamond carved frames')
    for s in (-1,1):
        for yy in (front+.28,front+depth-.26):
            x=s*2.61
            solid(b,'porch corner feet','alternating quoins',x,yy,.24,.65,.65,.48)
    solid(b,'porch ceiling','cream dressings',0,front+depth/2,5.15,width,depth,.22)
    solid(b,'porch roof','porch stone',0,front+depth/2,6.08,width,depth,.18)

def centre(b,lod):
    half=10.16;project=3.73; cheek=(half-project);front=.43
    for s in (-1,1):
        x=s*(half+project)/2
        f=Facade(b,(x-cheek/2,front),(x+cheek/2,front),'central stone cheeks')
        holes=[fenestration(f,0,.72,4.56,4.31,4,lod,'diamond')]
        for z,h in ((6.47,2.71),(10.62,2.05)):holes.append(fenestration(f,0,z,3.29,h,3,lod))
        f.wall(0,14.00,holes,.45,'court ashlar')
        for i,z in enumerate(np.arange(.29,13.99,.61)):
            u=s*(cheek/2-.21-(.10 if i%2 else 0))
            f.box(u,z,.42+(.20 if i%2 else 0),.585,.14,.015,'alternating quoins','alternating corner quoins')
    for s in (-1,1):
        return_gable(b,s*half,front,11.65,7.18,13.89,19.48,'central cross gable')
    tile_roof(b,'central high clay roof',-half+.14,half-.14,front-.05,13.96,7.18,.805,lod)
    # Rear downslope closes above the measured slice.
    f=Facade(b,(-half,11.64),(-half,7.15),'central ridge rear')
    f.prism(Polygon([(-2.245,15.94),(2.245,19.54),(2.245,13.43),(-2.245,13.43)]),-20.32,0,'burnt clay tiles','rear slope')
    solid(b,'central rear section','section stone',0,11.60,7.96,half*2,.13,15.92)
    for x in (-6.34,6.34):dormer(b,x,1.86,15.11,.805,lod,'central flanking attic')
    f=Facade(b,(-project,-.36),(project,-.36),'narrow central front gable')
    holes=[]
    for z,h in ((6.45,2.76),(10.61,2.08)):holes.append(fenestration(f,0,z,4.70,h,5,lod))
    holes.append(fenestration(f,0,15.05,.80,1.59,1,lod))
    door=tudor(0,0,2.64,3.29,.43);holes.append(door)
    f.prism(door.buffer(.016,join_style=2).intersection(box(-3,0,3,4)),-.63,-.60,'old mahogany','recessed timber entrance')
    for u in (-.64,.64):
        for z in (.84,2.13):
            p=box(u-.46,z-.45,u+.46,z+.45);f.prism(p.buffer(.055,join_style=2).difference(p),-.60,-.53,'dark casement','door field mouldings')
    outline=Polygon([(-project,0),(project,0),(project,14.08),(0,18.11),(-project,14.08)])
    f.wall(0,18.11,holes,.40,'court ashlar',outline)
    cap=LineString([(-project,14.08),(0,18.11),(project,14.08)])
    f.prism(cap.buffer(.117,cap_style='flat',join_style='mitre'),-.38,.095,'cream dressings','front gable coping')
    for z in np.arange(.40,18,.96):
        joint=outline.intersection(box(-project,z-.013,project,z+.013)).difference(union_all(holes))
        if joint.area>.0001:f.prism(joint,.002,.024,'horizontal bed joint','horizontal gable coursing')
    for s in (-1,1):
        xx=s*project
        solid(b,'central projecting gable returns','cream dressings',xx,.15,6.97,.24,1.02,13.94)
        # Each sloping apron runs to the intersection with the main roof.
        r=[(0,-.31,18.05),(xx,-.31,14.03),(xx,.52,14.03),(0,5.51,18.05)]
        b.add(r+[(x,y,z-.13)for x,y,z in r],[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],'burnt clay tiles','central gable clay apron')
    portal(b,lod)

def building(b,lod):
    wing(b,-34.20,-10.16,4.00,lod,'NW gallery')
    wing(b,10.16,36.49,3.76,lod,'SE gallery')
    centre(b,lod)
    add_lawn_return(b,lod)
