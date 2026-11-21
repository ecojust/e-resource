"""Two tiled roof slopes with hipped ends and separate front dormers."""
import math
from shapely.geometry import Polygon,box
from photo_architecture import Facade,pieces
from shapely import constrained_delaunay_triangles
from shapely.geometry.polygon import orient
from arcade import BUFF,GREY,WOOD,DARK,grid_sash
TILE='Dark rust clay tile';SUN_TILE='Muted clay tile';EAVE='Dark roof edge'


def roof_solid(b,plan,z,base,top,mat,label):
    if plan.is_empty:return
    b.prism(plan,base,top,lambda x,y,h:(x,y,z(x,y)+h),mat,label)


def rolled_tile(builder,cut,z,x0,x1,y0,length,lod,material,label):
    """Build one corrugated pan tile with a continuous skin at clipped roof edges."""
    count=2 if lod else 4
    vertices=[];ids={};surface=[];boundary={}
    def vertex(x,y):
        key=(round(x,9),round(y,9))
        if key not in ids:
            ids[key]=len(vertices)
            roll=.035*math.sin(math.pi*(x-x0)/(x1-x0))**2
            vertices.append((x,y,z(x,y)+.031*(1-(y-y0)/length)+roll+.041))
        return ids[key]
    for k in range(count):
        a=x0+(x1-x0)*k/count;b=x0+(x1-x0)*(k+1)/count
        strip=cut.intersection(box(a,y0-.1,b,y0+length+.1))
        for poly in pieces(strip):
            for tri in constrained_delaunay_triangles(poly).geoms:
                face=tuple(vertex(x,y) for x,y in list(orient(tri,sign=1).exterior.coords)[:3])
                if len(set(face))!=3:continue
                surface.append(face)
                for u,v in zip(face,face[1:]+face[:1]):
                    if (v,u) in boundary:boundary.pop((v,u))
                    else:boundary[u,v]=1
    if not surface:return
    n=len(vertices);faces=list(surface)
    faces.extend(tuple(u+n for u in reversed(t))for t in surface)
    faces.extend((u,u+n,v+n,v)for u,v in boundary)
    builder.add(vertices+[(x,y,h-.032)for x,y,h in vertices],faces,material,label)


def skin(b,plan,z,lod,label,dormers=()):
    openings=plan
    for hole in dormers:openings=openings.difference(hole)
    roof_solid(b,openings,z,-.105,0,EAVE,label+'/boarding')
    xmin,ymin,xmax,ymax=openings.bounds
    length=.57 if lod else .38;width=.41 if lod else .255
    rows=math.ceil((ymax-ymin)/length);cols=math.ceil((xmax-xmin)/width)+2
    for j in range(rows):
        y=ymin+j*length;offset=.5*width if j%2 else 0
        for i in range(-1,cols):
            x=xmin+i*width+offset
            tile=box(x+.007,y+.003,x+width-.007,y+length+.017).intersection(openings)
            for cut in pieces(tile):
                if cut.area<.0006:continue
                # The exposed toe sits higher than the head. Adjacent rows overlap.
                rolled_tile(b,cut,z,x+.007,x+width-.007,y,length,lod,SUN_TILE if (i+5*j)%13==2 else TILE,label+'/overlapping tiles')


def dormer(b,cx,front_y,width,base,apex,lod,label):
    face=Facade(b,(cx-.5,front_y),(cx+.5,front_y),label);soffit=apex-.44
    shape=Polygon([(-width/2,base),(width/2,base),(width/2,soffit),(.24*width,apex-.12),(-.24*width,apex-.12),(-width/2,soffit)])
    sill=base+.22;head=soffit-.15;sashw=width*.68
    hole=box(-sashw/2,sill,sashw/2,head)
    face.prism(shape.difference(hole),-.156,0,BUFF,'roughcast face')
    face.prism(hole,-.157,-.151,DARK,'dark reveal')
    grid_sash(face,0,sill,sashw,head,2,[sill+(head-sill)*.63],lod,'dormer sash',-.080)
    face.box(0,sill-.042,sashw+.11,.080,.129,.024,GREY,'projecting sill')
    length=1.67
    outer=width/2+.145;front=front_y-.185;rear=front_y+length+.10
    plateau=.10*width;ridge=apex-.012;drop=.49
    for side in (-1,1):
        xx=cx+side*width/2
        along=Facade(b,(xx,front_y+length),(xx,front_y)) if side<0 else Facade(b,(xx,front_y),(xx,front_y+length))
        a,bb=-length/2,length/2
        rise0,rise1=(1.18,0.) if side<0 else (0.,1.18)
        cheek=Polygon([(a,base+rise0),(bb,base+rise1),(bb,soffit),(a,soffit)])
        along.prism(cheek,-.08,0,'Dark dormer cheeks','cheek above tiles')
        lo,hi=sorted((side*outer,side*plateau))
        plan=box(cx+lo,front,cx+hi,rear)
        roof_solid(b,plan,lambda x,y:ridge-drop*(abs(x-cx)-plateau)/(outer-plateau),-.065,.012,EAVE,label+'/sloping dormer roof')
    roof_solid(b,box(cx-plateau,front,cx+plateau,rear),lambda x,y:ridge,-.065,.012,EAVE,label+'/truncated ridge')
    face.prism(Polygon([(-outer,soffit-.033),(-plateau,ridge-.070),(plateau,ridge-.070),(outer,soffit-.033),
                        (outer,soffit+.005),(plateau,ridge-.024),(-plateau,ridge-.024),(-outer,soffit+.005)]),.097,.143,GREY,'front verge')


def roof(b,d,lod):
    width=d['cornice_width'];depth=d['section_depth'];eave=d['cornice_z']+.115
    y0=-.11;span=depth-y0;rise=3.22
    slope=lambda x,y:eave+rise*(y-y0)/span
    for i,(l,r,cx) in enumerate([(0,d['middle_left']+.03,d['dormer_axes'][0]),(d['middle_right']-.03,width,d['dormer_axes'][1])]):
        label='Southwest roof' if i==0 else 'Northeast roof'
        side=0 if i==0 else width
        inset=2.19
        quad=[(l-.08,y0),(r+.08,y0),(r+.08 if i==0 else r-inset,depth),(l+inset if i==0 else l-.08,depth)]
        front=Polygon(quad);fy=.83;ww=1.91;foot=box(cx-ww/2,fy,cx+ww/2,fy+1.68)
        skin(b,front,slope,lod,label,[foot])
        side_plan=Polygon([(side+(-.08 if i==0 else .08),y0),(side+(inset if i==0 else -inset),depth),(side+(-.08 if i==0 else .08),depth)])
        # Hip and street slope meet at equal elevations along their shared edge.
        side_rise=(lambda x,y:eave+rise*(x+.08)/(inset+.08)) if i==0 else (lambda x,y:eave+rise*(width+.08-x)/(inset+.08))
        skin(b,side_plan,side_rise,lod,label+' hip')
        dormer(b,cx,fy,ww,slope(cx,fy)-.040,d['dormer_z'],lod,'Roof dormer '+str(i+1))
        b.tube([(side+(-.08 if i==0 else .08),y0,eave+.10),(side+(inset if i==0 else -inset),depth,eave+rise+.10)],.058,TILE,8 if lod else 12,label+'/hip ridge')
