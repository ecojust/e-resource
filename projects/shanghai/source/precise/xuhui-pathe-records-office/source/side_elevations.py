"""Side elevations of the Pathé house, based on paired eastern and western return photographs."""
import math
import sys

from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles
from shapely.geometry.polygon import orient

from garden_elevation import arched, fenestration, BRICK, STONE, WHITE, FRAME, GLASS, TILE, EAVES, IRON


def _window_trims(wall, hole, kind, label, lod):
    x0,z0,x1,z1=hole.bounds
    if kind=='arch':
        surround=hole.buffer(.105).difference(hole)
        wall.prism(surround,-.01,.075,STONE,label+' round moulding')
        return
    width=x1-x0
    wall.box((x0+x1)*.5,z0-.051,width+.21,.102,.167,.018,STONE,label+' stone sill')
    wall.box((x0+x1)*.5,z1+.098,width+.245,.196,.14,.025,STONE,label+' keyed lintel')
    if kind=='keyed':
        for side in (-1,1):
            position=x0 if side==-1 else x1
            for i in range(5):
                h=(z1-z0)/5
                w=.095 if i%2 else .155
                wall.box(position+side*w/2,z0+h*(i+.5),w,h-.012,.09,.020,
                         STONE,f'{label} jamb stone {side} {i}')
        if not lod:
            keystone=Polygon([((x0+x1)/2-.083,z1+.2),((x0+x1)/2+.083,z1+.2),
                              ((x0+x1)/2+.058,z1-.035),((x0+x1)/2-.058,z1-.035)])
            wall.prism(keystone,.088,.112,STONE,label+' keystone')


def _wall_with_cuts(wall,surface,items,lod,label):
    holes=[]
    for name,hole,style,columns,rails in items:
        holes.append(hole)
    body=surface.difference(unary_union(holes))
    wall.prism(body,-.23,0,BRICK,label+' brick and integral reveals')
    for name,hole,style,columns,rails in items:
        fenestration(wall,hole,0,columns,rails,name)
        _window_trims(wall,hole,style,name,lod)


def _rect(axis,sill,width,height):
    return box(axis-width/2,sill,axis+width/2,sill+height)


def _clip(points, value):
    """Clip a counter-clockwise planar face to the side where value is nonpositive."""
    result=[]
    for p,q in zip(points,points[1:]+points[:1]):
        vp,vq=value(*p),value(*q)
        if vp<=1.e-9:result.append(p)
        if (vp<0<vq) or (vq<0<vp):
            t=vp/(vp-vq)
            result.append((p[0]+(q[0]-p[0])*t,p[1]+(q[1]-p[1])*t))
    return result


def _wing_roof(b,plan,xouter,ynorth,ysouth,base,lod):
    """Clay lean-to with hipped end planes and a continuous dark soffit."""
    plan=plan.buffer(.19,join_style=2)
    b.plan_prism(plan,base-.115,base,TILE,'West wing thin tile drip and soffit')
    ext=plan.bounds
    extent=[(ext[0]-1,ext[1]-1),(ext[2]+1,ext[1]-1),
            (ext[2]+1,ext[3]+1),(ext[0]-1,ext[3]+1)]
    planes=[(-.28,0,.28*(xouter+.19)),(0,.28,-.28*(ynorth-.19)),
            (0,-.28,.28*(ysouth+.19)),(0,0,.53)]
    for i,(a,c,k)in enumerate(planes):
        region=extent
        for j,(a2,c2,k2) in enumerate(planes):
            if i!=j and region:
                region=_clip(region,lambda x,y:(a-a2)*x+(c-c2)*y+k-k2)
        if len(region)<3:continue
        section=plan.intersection(Polygon(region))
        polygons=[section] if section.geom_type=='Polygon' else list(getattr(section,'geoms',[]))
        for patch in polygons:
            if patch.area<.001:continue
            vertices=[];faces=[]
            for tri in constrained_delaunay_triangles(patch).geoms:
                coords=list(orient(tri,sign=1).exterior.coords)[:3]
                idx=len(vertices)
                vertices.extend((x,y,base+a*x+c*y+k+.007)for x,y in coords)
                faces.append((idx,idx+1,idx+2))
            b.add(vertices,faces,TILE,f'Northwest wing sloped roof field {i+1}')
    line=list(plan.exterior.coords)
    for k,(p,q) in enumerate(zip(line,line[1:])):
        if math.dist(p,q)<.012:continue
        b.tube([(*p,base-.072),(*q,base-.072)],.035,EAVES,
               5 if lod else 8,f'Northwest wing eave roll {k+1}')


def build_sides(b,D,lod):
    """North is y=0. East is negative x in the house builder's local frame."""
    facade=getattr(sys.modules[type(b).__module__],'Facade',None)
    if facade is None:
        from photo_architecture import Facade as facade
    width=D['width']
    length=D['wall_depth']
    height=D['wall_eave']
    xe,xw=-width/2,width/2
    east=facade(b,(xe,length),(xe,0),'East side')
    west=facade(b,(xw,0),(xw,length),'West side')
    f=lambda fraction:(fraction-.5)*length
    # Four second-floor windows and three ground-floor windows read in two directions.
    east_axes=(.298,.535,.706,.891)
    upper=D.get('east_upper_sill',4.61)
    lower=D.get('east_lower_sill',1.26)
    eastholes=[]
    for i,(t,w,style) in enumerate(zip(east_axes,(.86,.35,1.04,1.04),('plain','plain','keyed','keyed')),1):
        eastholes.append((f'East upper {i}',_rect(f(t),upper,w,1.67),style,
                          1 if w<.45 else 2,(.28,.57,.80)))
    arch=arched(f(east_axes[0]),1.0,2.24,2.21,.46,12 if lod else 26)
    eastholes.append(('East lower garden-end arch',arch,'arch',3,(.46,.67,.81)))
    for i,t in enumerate(east_axes[2:],1):
        eastholes.append((f'East lower north pair {i}',_rect(f(t),lower,1.04,1.65),
                          'keyed',2,(.28,.57,.80)))
    _wall_with_cuts(east,box(-length/2,0,length/2,height),eastholes,lod,'Eastern elevation')
    # On the southern first-floor arch a low, white parapet returns under the flower box.
    u=f(east_axes[0])
    for x in (u-1.22,u+1.22):
        east.box(x,.88,.19,.65,.44,.20,WHITE,'East flower parapet end')
    east.box(u,.69,2.52,.32,.16,.40,STONE,'East low flower parapet')
    east.box(u,.88,2.58,.085,.19,.41,WHITE,'East flower parapet coping')
    east.box((f(.59)+length/2)/2,3.61,length*(1-.59),.056,.081,.016,STONE,
             'East thin horizontal string course north section')

    # The western ground floor is covered by an attached low brick range.
    # Its hidden interface has no invented glazing. The upper western wall has
    # a broader northward opening and a narrow slit, separated by exposed brick.
    ynorth=D.get('west_annex_north',-.70)
    projection=D.get('west_annex_projection',2.30)
    ysouth=min(length-.65,ynorth+D.get('west_annex_length',.82*length))
    xout=xw+projection
    north_width=D.get('west_annex_north_width',4.02)
    xinner=xout-north_width
    wing_eave=D.get('west_annex_eave',3.82)
    west_upper=D.get('west_upper_sill',4.34)
    wh=[('West upper broad opening',_rect(f(.269),west_upper,1.00,1.78),'keyed',2,(.25,.52,.77)),
        ('West upper narrow opening',_rect(f(.536),west_upper,.35,1.78),'plain',1,(.30,.60,.84))]
    _wall_with_cuts(west,box(-length/2,0,length/2,height),wh,lod,'Western elevation')
    wn=facade(b,(xinner,ynorth),(xout,ynorth),'Wing N')
    ww=facade(b,(xout,ynorth),(xout,ysouth),'West wing')
    ws=facade(b,(xout,ysouth),(xw,ysouth),'South return of west wing')
    we=facade(b,(xinner,0),(xinner,ynorth),'Inner north wing return')
    wnwin=_rect(wn.length*.021,1.31,.42,1.48)
    _wall_with_cuts(wn,box(-wn.length/2,0,wn.length/2,wing_eave),
                    [('West wing north slit',wnwin,'plain',1,(.26,.54,.78))],lod,'Western wing north')
    wlen=ww.length
    outer=[]
    openings=[(.105,.88,.34,2.50,'north door'),(.384,1.00,1.92,1.15,'first paired window'),
              (.565,1.00,1.92,1.15,'second paired window'),(.825,.82,.62,2.28,'south door')]
    for frac,w,sill,h,role in openings:
        outer.append(('West wing '+role,_rect((frac-.5)*wlen,sill,w,h),
                      'plain' if 'door' in role else 'keyed',2,(.26,.54,.78)))
    _wall_with_cuts(ww,box(-wlen/2,0,wlen/2,wing_eave),outer,lod,'Outer west elevation')
    ws.wall(0,wing_eave,(),.22,BRICK)
    if we.length>.02:we.wall(0,wing_eave,(),.22,BRICK)
    for sub in (wn,ww,ws,we):
        if sub.length<.02:continue
        cuts=[h for _,h,_,_,_ in (outer if sub is ww else [])]
        skirt=box(-sub.length/2,0,sub.length/2,.71).difference(unary_union(cuts))
        sub.prism(skirt,-.018,.033,STONE,'West wing visible pale plinth')
        sub.prism(box(-sub.length/2,.70,sub.length/2,.77).difference(unary_union(cuts)),
                  -.012,.077,STONE,'West wing plinth cap')
    for i,(frac,_,sill,_,name) in enumerate((openings[0],openings[-1])):
        axis=(frac-.5)*wlen
        count=2 if i==0 else 4
        for k in range(count):
            run=(count-k)*.25+.04
            ww.box(axis,sill*(k+.5)/count,1.12 if i==0 else 1.31,
                   sill/count,run,run/2,STONE,'West door stair '+name+' '+str(k+1))
    # Retain the measured field of the west facade behind the attachment.
    outline=Polygon([(xinner,ynorth),(xout,ynorth),(xout,ysouth),(xw,ysouth),(xw,0),(xinner,0)])
    _wing_roof(b,outline,xout,ynorth,ysouth,wing_eave,lod)
    for n in range(math.ceil(wing_eave/.27)):
        z=.135+.27*n
        if z+.13>wing_eave:break
        w=.20 if n%2==0 else .31
        wn.box(wn.length/2-w/2,z,w,.256,.054,.016,STONE,'West wing outer north quoins')
        ww.box(-ww.length/2+w/2,z,w,.256,.054,.016,STONE,'West wing outer west quoins')
    return dict(east_lower_openings=3,east_upper_openings=4,west_upper_openings=2,
                west_wing_north_openings=1,west_wing_outer_openings=4,
                west_wing_outer_x=xout,west_wing_north_y=ynorth,west_wing_south_y=ysouth,
                west_wing_eave=wing_eave)
