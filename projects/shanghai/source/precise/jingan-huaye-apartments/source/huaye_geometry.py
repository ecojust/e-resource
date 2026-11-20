"""H-shaped main house. Dimensions in metres in the photo-right / inward frame."""
from math import cos, sin, radians, pi
import numpy as np
from shapely import affinity
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
from photo_architecture import Facade,opening

PALETTE={
    'ivory stucco':{'color':[.78,.73,.59],'roughness':.87},
    'cream surrounds':{'color':[.89,.81,.64],'roughness':.78},
    'ochre stone':{'color':[.58,.46,.32],'roughness':.79},
    'tile field':{'color':[.40,.139,.064],'roughness':.86},
    'hip mortar':{'color':[.66,.44,.275],'roughness':.87},
    'tile ridges':{'color':[.53,.221,.105],'roughness':.75},
    'old timber':{'color':[.16,.105,.061],'roughness':.56},
    'leaded sash':{'color':[.15,.155,.121],'roughness':.48,'metallic':.24},
    'cool glazing':{'color':[.16,.222,.225],'roughness':.24,'metallic':.20},
    'sunlit glazing':{'color':[.26,.25,.194],'roughness':.29,'metallic':.12},
    'flat roof':{'color':[.345,.35,.319],'roughness':.89},
    'basement stone':{'color':[.43,.386,.32],'roughness':.86},
    'balcony iron':{'color':[.18,.174,.129],'roughness':.51,'metallic':.32},
}
CREAM='ivory stucco';TRIM='cream surrounds';TILES='tile field'
BAR_MIN,BAR_MAX=-11.55,12.35
BAR_HEIGHT=27.15
FLOORS=[.60,4.42,7.77,11.12,14.47,17.82,21.17]


def pane(f,shape,cols,rows,lod,label):
    xmin,zmin,xmax,zmax=shape.bounds
    f.prism(shape.buffer(.015,join_style=2),-.33,-.30,'cool glazing',label+' glass')
    inside=shape.buffer(-.085,join_style=2)
    bars=[]
    for i in range(1,cols):
        x=xmin+(xmax-xmin)*i/cols
        bars.append(box(x-.035,zmin,x+.035,zmax))
    for i in range(1,rows):
        z=zmin+(zmax-zmin)*i/rows
        bars.append(box(xmin,z-.038,xmax,z+.038))
    grid=shape.difference(inside.difference(unary_union(bars)))
    f.prism(grid,-.275,-.20,'leaded sash',label+' frame')
    half=(xmax-xmin)/2;u=(xmin+xmax)/2
    f.box(u,zmin-.055,half*2+.15,.12,.38,-.12,'ochre stone',label+' sill')


def rail(f,u,z,width,height,lod,label):
    for zz in (z+.06,z+height):
        f.box(u,zz,width,.060,.07,.0,'balcony iron',label)
    for i in range(max(3,int(width/(.34 if lod else .23)))):
        x=u-width/2+.13+i*(width-.26)/(max(3,int(width/(.34 if lod else .23)))-1)
        f.box(x,z+height/2,.039,height,.061,0,'balcony iron',label)
        if not lod:
            f.builder.tube([f.point(x-.053,z+.24,0),f.point(x,z+.37,0),f.point(x+.053,z+.24,0),f.point(x,z+.14,0),f.point(x-.053,z+.24,0)],.015,'balcony iron',4,f.label+'/'+label)


def tile_cap(b,foot,low,eave,top,label,lod):
    """A planar hipped roof with an explicit central ridge and scalloped tile ribs."""
    x0,y0,x1,y1=foot.bounds
    w=x1-x0;d=y1-y0;cx=(x0+x1)/2;cy=(y0+y1)/2
    b.plan_prism(foot,low,eave,'ochre stone',label+'/bearing')
    if w>=d:
        p,q=(cx-(w-d)*.42,cy,top),(cx+(w-d)*.42,cy,top)
        slopes=[([(x0,y0,eave),(x1,y0,eave)],[p,q]), ([(x1,y0,eave),(x1,y1,eave)],[q,q]),
                ([(x1,y1,eave),(x0,y1,eave)],[q,p]), ([(x0,y1,eave),(x0,y0,eave)],[p,p])]
    else:
        p,q=(cx,cy-(d-w)*.42,top),(cx,cy+(d-w)*.42,top)
        slopes=[([(x0,y0,eave),(x1,y0,eave)],[p,p]), ([(x1,y0,eave),(x1,y1,eave)],[p,q]),
                ([(x1,y1,eave),(x0,y1,eave)],[q,q]), ([(x0,y1,eave),(x0,y0,eave)],[q,p])]
    for edge,ridge in slopes:
        a,c=map(np.array,edge);i,j=map(np.array,ridge)
        verts=[a,c,j,i] if not np.array_equal(i,j)else[a,c,i]
        b.add(verts,[tuple(range(len(verts)))],TILES,label+'/slopes')
        if not lod:
            count=max(3,int(np.linalg.norm(c-a)/.34))
            for t in np.linspace(.02,.98,count):
                start=a*(1-t)+c*t;end=i*(1-t)+j*t
                b.tube([start+[0,0,.027],end+[0,0,.027]],.035,'tile ridges',6,label+'/tile rolls')


def bowed_balcony(b,x,front,z,width,projection,solid,label,lod,outward=-1):
    radius=width/2;end=front+.035
    pts=[(x-radius,end)]+[(x+radius*cos(i),front-projection*sin(i)) for i in np.linspace(pi,0,9 if lod else 23)]+[(x+radius,end)]
    floor=Polygon(pts)
    def side(p):return affinity.scale(p,xfact=1,yfact=-1,origin=(x,front)) if outward==1 else p
    b.plan_prism(side(floor),z-.12,z+.07,TRIM,label+'/slab')
    inner=affinity.scale(floor,xfact=max(.3,(width-.26)/width),yfact=.77,origin=(x,front))
    parapet=floor.difference(inner).intersection(box(x-radius-.01,front-projection-.01,x+radius+.01,front-.017))
    b.plan_prism(side(parapet),z+.055,z+.90 if solid else z+.40,CREAM,label+'/curved parapet')
    if not solid:
        rr=width*.19
        f=Facade(b,(x+outward*rr,front+outward*projection*.95),(x-outward*rr,front+outward*projection*.95),label)
        rail(f,0,z+.38,rr*2,.52,lod,'central ironwork')
    cap=parapet.buffer(.035,join_style=2).intersection(box(x-radius-.06,front-projection-.08,x+radius+.06,front-.01))
    b.plan_prism(side(cap),z+.87 if solid else z+.37,z+.95 if solid else z+.45,TRIM,label+'/coping')


def medallion(fac,u,z,lod,label):
    disk=Point(u,z).buffer(.42,quad_segs=5 if lod else 12)
    fac.prism(disk,.02,.09,'ochre stone',label)
    for offset in [-1.05,-.73,.73,1.05]:
        shape=affinity.scale(Point(u+offset,z).buffer(.14,quad_segs=4 if lod else 8),xfact=1.35,yfact=.64)
        fac.prism(shape,.015,.07,'ochre stone',label)


def wall_grid(fac,bottom,top,holes,lod):
    fac.wall(bottom,top,[h[0] for h in holes],.42,CREAM)
    for i,(p,cols,rows) in enumerate(holes):
        pane(fac,p,cols,rows if not lod else max(1,rows-1),lod,f'window {i+1}')


def main_bar(b,cx,lod,label):
    x0,x1=cx-6.25,cx+6.25
    where=box(x0,BAR_MIN,x1,BAR_MAX)
    b.plan_prism(where.buffer(-.08),0,.13,'basement stone',label+'/floor')
    front=Facade(b,(x0,BAR_MIN),(x1,BAR_MIN),label+'/southwest')
    holes=[]
    for i,z in enumerate(FLOORS):
        holes.extend([(opening(u,z,1.03,1.94),2,3)for u in (-5.08,5.08)])
        holes.append((opening(0,z,4.46,2.13),4,3))
        if i>0:bowed_balcony(b,cx,BAR_MIN,z-.10,5.12,.69,False,label+f'/balcony {i}',lod)
    wall_grid(front,0,BAR_HEIGHT,holes,lod)
    medallion(front,0,25.50,lod,'plaster medallion')
    for u in (-3.09,3.09):
        front.box(u,13.51,.18,26.82,.17,.034,TRIM,'shallow bay pilasters')
    if not lod:
        for u in np.linspace(-5.72,5.72,19):
            arch=affinity.scale(Point(u,26.72).buffer(.145,quad_segs=5),xfact=.89,yfact=1.35)
            front.prism(arch,.006,.040,'ochre stone','scalloped roof frieze')
    front.box(0,24.50,6.73,.11,.42,-.095,TRIM,'bay cornice')
    # Main masonry side faces. Inside the H, only the flank outside the transverse link is exposed.
    for a,c,side in [((x1,BAR_MIN+.421),(x1,BAR_MAX-.421),'southeast'),((x0,BAR_MAX-.421),(x0,BAR_MIN+.421),'northwest')]:
        f=Facade(b,a,c,label+'/'+side)
        holes=[]
        inner=(cx<0 and side=='southeast') or (cx>0 and side=='northwest')
        for z in FLOORS:
            for u in (-9.15,-6.35,-2.15,2.15,6.35,9.15):
                if inner and abs(u)<6.9:continue
                holes.append((opening(u,z,1.33,1.94),2,2))
        wall_grid(f,0,BAR_HEIGHT,holes,lod)
    rear=Facade(b,(x1,BAR_MAX),(x0,BAR_MAX),label+'/northeast')
    holes=[]
    for i,z in enumerate(FLOORS):
        if i>0:bowed_balcony(b,cx,BAR_MAX,z-.10,4.64,.58,False,label+f'/garden balcony {i}',lod,outward=1)
        holes.extend([(opening(u,z,1.11,1.95),2,2)for u in(-4.96,4.96)])
        holes.append((opening(0,z,3.91,2.08),4,2))
    wall_grid(rear,0,BAR_HEIGHT,holes,lod)
    b.plan_prism(where.buffer(.09,join_style=2),26.78,26.94,TRIM,label+'/cornice')
    b.plan_prism(where.buffer(-.015,join_style=2),26.98,27.19,'flat roof',label+'/terraced roof')
    for y in (BAR_MIN+.57,BAR_MAX-.57):
        tile_cap(b,box(x0+.22,y-.72,x1-.22,y+.72),27.14,27.23,27.69,label+f'/tiled end {y:.0f}',lod)
    # Set-back eighth storey on the court side, with a triple arcade visible in the 2019 photograph.
    block=box(x0+.55,-6.7,x1-.55,8.7)
    upper=Facade(b,(x0+.55,-6.7),(x1-.55,-6.7),label+'/upper loggia')
    arches=[opening(u,27.28,1.60,2.36,.79,10 if lod else 22)for u in (-2.11,0,2.11)]
    upper.wall(27.14,30.96,arches,.45,CREAM)
    for i,p in enumerate(arches):
        pane(upper,p,2,3,lod,f'arched bay {i+1}')
        upper.prism(p.buffer(.12,join_style=2).difference(p),.01,.065,TRIM,'arch trim')
    for a,c,s in [((x1-.55,-6.7+.45),(x1-.55,8.7-.42),'right'),((x1-.55,8.7),(x0+.55,8.7),'rear'),((x0+.55,8.7-.42),(x0+.55,-6.7+.45),'left')]:
        f=Facade(b,a,c,label+'/upper '+s)
        if s=='rear':
            holes=[(opening(u,27.40,1.48,2.23,.69,10 if lod else 22),2,3)for u in (-2.02,0,2.02)]
        else:
            holes=[(opening(u,27.60,1.04,1.80),2,2)for u in (-2.8,0,2.8)]
        wall_grid(f,27.14,30.96,holes,lod)
    b.plan_prism(block.buffer(.10,join_style=2),30.90,31.08,TRIM,label+'/upper coping')
    b.plan_prism(block.buffer(-.04),31.08,31.14,'flat roof',label+'/upper flat roof')
    for face,y in [('court',-6.35),('garden',8.30)]:
        tile_cap(b,box(x0+.29,y-.70,x1-.29,y+.70),30.98,31.15,31.64,label+'/'+face+' upper tile skirt',lod)


def central_spine(b,lod):
    f=Facade(b,(-6.10,-7.74),(6.10,-7.74),'Centre/southwest')
    holes=[]
    for z in FLOORS+[24.52,27.84]:
        holes.extend([(opening(u,z,1.04,1.86),2,3)for u in(-4.42,-2.73,2.73,4.42)])
        holes.append((opening(0,z,2.68,2.29),3,3))
    wall_grid(f,0,31.2,holes,lod)
    for i,z in enumerate(FLOORS[1:]+[24.52,27.84],2):
        bowed_balcony(b,0,-7.74,z-.12,3.31,1.24,True,f'Centre/rounded balcony {i}',lod)
    tile_cap(b,box(-1.92,-9.11,1.92,-7.03),30.27,30.39,31.08,'Centre/top balcony hood',lod)
    rear=Facade(b,(6.10,6.68),(-6.10,6.68),'Centre/northeast')
    holes=[]
    for z in FLOORS[1:]+[24.52,27.84]:
        for u in [-3.6,0,3.6]:
            rise=.61 if z>27 else 0
            holes.append((opening(u,z,1.68,2.01,rise,10 if lod else 22),2,2))
    holes.append((opening(0,.13,2.43,2.70),2,2))
    wall_grid(rear,0,31.2,holes,lod)
    canopy=box(-2.12,6.59,2.12,8.39)
    b.plan_prism(canopy,3.06,3.29,'ochre stone','Centre/entry canopy')
    base=box(-6.10,-7.74,6.10,6.68)
    b.plan_prism(base,0,.16,'basement stone','Centre/ground floor')
    b.plan_prism(base.buffer(-.13,join_style=2),30.93,31.22,'flat roof','Centre/roof')
    # Close the high shoulders where the centre emerges above the lower bar roofs.
    for a,c,s in [((6.10,-7.74+.421),(6.10,6.68-.421),'east'),((-6.10,6.68-.421),(-6.10,-7.74+.421),'west')]:
        Facade(b,a,c,'Centre/'+s).wall(0,31.17,thickness=.38,material=CREAM)
    for x in (-5.01,5.01):
        for side,y in [('court',-5.37),('garden',5.10)]:
            turret=box(x-.75,y-1.48,x+.75,y+1.48)
            label=f'Centre/{side} turret {x:.0f}'
            b.plan_prism(turret,30.9,32.25,CREAM,label+'/body')
            tile_cap(b,turret.buffer(.12,join_style=2),32.24,32.34,32.94,label+'/tile cap',lod)


def lantern(b,lod):
    # An eight-facet tower with three long windows and a scalloped cornice on the photographed front.
    w=5.65;cut=2.46;cy=-.53
    pts=[(-w+cut,cy-w),(w-cut,cy-w),(w,cy-w+cut),(w,cy+w-cut),(w-cut,cy+w),(-w+cut,cy+w),(-w,cy+w-cut),(-w,cy-w+cut)]
    base=Polygon(pts)
    for i,(a,c) in enumerate(zip(pts,pts[1:]+pts[:1])):
        fac=Facade(b,a,c,'Tower/'+str(i+1))
        holes=[]
        if i in(0,4):
            for u in(-1.76,0,1.76):
                holes.append((opening(u,31.59,.76,1.71),2,3))
                holes.append((opening(u,34.30,.78,1.60,.36,10 if lod else 20),2,3))
                med=affinity.scale(Point(u,33.77).buffer(.21,quad_segs=5 if lod else 10),xfact=1.,yfact=1.22)
                fac.prism(med,.005,.055,'ochre stone','recessed motif')
        wall_grid(fac,30.66,36.72,holes,lod)
        count=max(3,int(fac.length/.58))
        for u in np.linspace(-fac.length/2+.23,fac.length/2-.23,count):
            tooth=Polygon([(u-.16,36.63),(u+.16,36.63),(u+.11,36.40),(u,36.33),(u-.11,36.40)])
            fac.prism(tooth,.005,.10,'ochre stone','arcaded cornice')
    b.plan_prism(base.buffer(.18,join_style=2),36.66,36.86,TRIM,'Tower/eaves')
    eaves=list(base.buffer(.25,join_style=2).exterior.coords)[:-1]
    # Shapely buffers are clockwise; reverse before building upwards-facing roof facets.
    if not Polygon(eaves).exterior.is_ccw:eaves.reverse()
    crown=np.array([0.,cy,41.02])
    for i,(a,c) in enumerate(zip(eaves,eaves[1:]+eaves[:1])):
        v0=np.array([*a,36.86]);v1=np.array([*c,36.86])
        b.add([v0,v1,crown],[(0,1,2)],TILES,'Tower/eight tiled roof planes')
        b.tube([v0+[0,0,.035],crown+[0,0,.035]],.105,'hip mortar',6 if lod else 10,'Tower/hip rolls')
        if not lod:
            for t in np.linspace(.075,.925,12):
                v=v0*(1-t)+v1*t
                b.tube([v+[0,0,.025],crown*.95+v*.05+[0,0,.025]],.036,'tile ridges',5,'Tower/roof tiles')
    b.lathe((0,cy),[(40.86,.39),(41.12,.39),(41.16,.29),(41.74,.29),(41.90,.14),(42.1,.055)],TRIM,10 if lod else 20,'Tower/cream finial')
    b.tube([(0,cy,42.07),(0,cy,42.76)],.028,'balcony iron',6,'Tower/finial pin')


def add_apartments(builder,lod):
    main_bar(builder,-10.60,lod,'Northwest bar')
    main_bar(builder,10.60,lod,'Southeast bar')
    central_spine(builder,lod)
    lantern(builder,lod)
