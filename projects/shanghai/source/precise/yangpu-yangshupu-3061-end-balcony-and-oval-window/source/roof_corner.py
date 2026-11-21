"""A tiled front roof slope, hip, and the single two-light shed dormer above the corner."""
import math
import numpy as np
from shapely.geometry import box,Polygon
from shapely.ops import unary_union
from photo_architecture import Facade
from window_joinery import glazing

TILE='Dark terracotta tile'
TILE_LIGHT='Sunlit tile'
EAVE='Oxide red fascia'


def surface(builder,plan,level,thickness,material,label):
    if plan.is_empty or plan.area<.000001:return
    from shapely.ops import orient
    ring=list(orient(plan,sign=1).exterior.coords)[:-1]
    n=len(ring);base=[(x,y,level(x,y)-thickness)for x,y in ring];top=[(x,y,level(x,y))for x,y in ring]
    builder.add(base+top,[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n)],material,label)


def roof(builder,d,lod):
    x0=d['left_cut']-.10;x1=d['corner_x']+.16;y0=-.19;y1=d['side_cut'];e=d['eave'];pitch=d['roof_pitch']
    a=Polygon([(x0,y0),(x1,y0),(x1-(y1-y0),y1),(x0,y1)])
    b=Polygon([(x1,y0),(x1,y1),(x1-(y1-y0),y1)])
    front=lambda x,y:e+(y-y0)*pitch;side=lambda x,y:e+(x1-x)*pitch
    surface(builder,a,front,.12,TILE,'Roof/front pitched sheathing');surface(builder,b,side,.12,TILE,'Roof/hip sheathing')
    step=.145 if not lod else .29
    for facet,level,name in [(a,front,'front'),(b,side,'hip')]:
        count=math.ceil((y1-y0)/step)+1;strips=math.ceil((x1-x0)/step)+1
        for j in range(count):
            for i in range(strips):
                if name=='front':
                    x=x0+i*step;y=y0+j*step*1.53
                    cell=box(x+.008,y+.005,x+step-.004,y+1.53*step-.004)
                else:
                    x=x1-i*step*1.53;y=y0+j*step
                    cell=box(x-1.53*step+.004,y+.007,x-.004,y+step-.004)
                piece=cell.intersection(facet)
                if piece.is_empty or piece.area<.00004 or piece.geom_type!='Polygon':continue
                high=lambda xx,yy:level(xx,yy)+.016
                surface(builder,piece,high,.015,TILE_LIGHT if (2*i+j)%5==0 else TILE,'Roof/'+name+' laid tiles')
                if not lod and piece.area>.019:
                    xp,yp=piece.centroid.coords[0]
                    if name=='front':pts=[(xp,yy,high(xp,yy)+.005)for yy in (piece.bounds[1]+.009,piece.bounds[3]-.009)]
                    else:pts=[(xx,yp,high(xx,yp)+.005)for xx in (piece.bounds[0]+.009,piece.bounds[2]-.009)]
                    builder.tube(pts,.014,TILE_LIGHT,6,'Roof/'+name+' weather rolls')
    builder.tube([(x1,y0,e+.038),(x1-(y1-y0),y1,front(x0,y1)+.038)],.055,TILE_LIGHT,7 if lod else 13,'Roof/raised hip cap')
    for pa,pb in [((x0,y0),(x1,y0)),((x1,y0),(x1,y1))]:
        face=Facade(builder,pa,pb,'Roof edge')
        face.box(0,e-.106,face.length,.11,.13,-.035,EAVE,'projecting fascia')
        face.box(0,e-.004,face.length,.065,.11,.02,'Pale gutter metal','edge gutter')
    # The photographed shed window, located on the front slope above the red joinery.
    cx=d['dormer_x'];y=d['dormer_y'];width=d['dormer_width'];sill=front(cx,y)+.002;head=sill+d['dormer_glazed_height']
    face=Facade(builder,(cx-.5,y),(cx+.5,y),'Shed dormer')
    face.prism(box(-width/2-.095,sill-.06,width/2+.095,head+.106).difference(box(-width/2,sill,width/2,head)),-.12,0,'Warm sill paint','window face')
    for i in [0,1]:
        glazing(face,(i-.5)*width/2,sill+.012,width/2-.009,head-sill-.025,1,3,.006,lod,'Shed red sash '+str(i+1))
    back=y+.82
    roof_base=head+d['dormer_fascia_rise']-.072
    face.prism(box(-width/2-.094,head+.105,width/2+.094,roof_base),-.119,0,'Warm sill paint','solid header below roof soffit')
    for sign in [-1,1]:
        xx=cx+sign*(width/2+.094)
        q=Facade(builder,(xx,y),(xx,back),'Shed cheek') if sign>0 else Facade(builder,(xx,back),(xx,y),'Shed cheek')
        coords=[(sign*(yy-(back+y)/2),zz) for yy,zz in [(y,sill-.025),(back,front(cx,back)-.045),(back,roof_base-(back-y)*.16),(y,roof_base)]]
        q.prism(Polygon(coords),-.055,0,'Warm sill paint','painted cheek')
    plan=box(cx-width/2-.18,y-.31,cx+width/2+.18,back+.06)
    mono=lambda xx,yy:head+d['dormer_fascia_rise']-(yy-y)*.16
    surface(builder,plan,mono,.075,EAVE,'Dormer/overhanging shed roof')
    # The street photograph shows a pale overhanging soffit edged in dark red.
    soffit=box(cx-width/2-.165,y-.292,cx+width/2+.165,y+.018)
    surface(builder,soffit,lambda xx,yy:mono(xx,yy)-.067,.025,'Warm sill paint','Dormer/pale underside')
    face.box(0,head+d['dormer_fascia_rise']-.012,width+.35,.095,.085,.306,EAVE,'dark red front fascia')
