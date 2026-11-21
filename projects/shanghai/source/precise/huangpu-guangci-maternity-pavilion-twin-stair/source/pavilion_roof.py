"""Roof section over the seven photographed courtyard bays, with projecting timber eaves."""
from math import floor, ceil
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from photo_architecture import Facade,opening
from pavilion_materials import CREAM,EDGE,CUT,WOOD,GLASS,TILE,ROOF_SHADE,TIMBER
from pavilion_windows import framed

HALF=20.18
RIDGE=5.85
HEIGHT=16.45


def roof_height(y):
    return 11.38+(y+1.25)*(HEIGHT-11.38)/(RIDGE+1.25)


def prism_section(builder,section,x0,x1,material,label):
    builder.prism(Polygon(section),x0,x1,lambda y,z,x:(x,y,z),material,label)


def roof_surface(builder,top,material,label,thickness=.072):
    lower=[(x,y,z-thickness)for x,y,z in top]
    builder.add(lower+top,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],material,label)


def traditional_bracket(b,x,back,eave,label,lod):
    # The brace forks outward and down from a horizontal ceiling timber.
    shape=[(back-.11,10.68),(back-.12,9.49),(back-.28,9.53),(back-.35,9.74),
           (back-.42,10.05),(back-.57,10.27),(eave+.20,10.60),(eave+.06,10.69),
           (eave+.08,10.83),(back-.31,10.89)]
    prism_section(b,shape,x-.070,x+.070,TIMBER,label+' curved console')
    b.box((x,back-.09,9.54),(.19,.24,.20),EDGE,label=label+' stone corbel foot')
    b.box((x,(back+eave)/2,10.95),(.14,back-eave+.14,.15),TIMBER,label=label+' rafter tail')
    if not lod:
        shape=[(back-.17,10.38),(back-.2,10.15),(back-.52,10.52),(back-.90,10.69),(back-.78,10.72),(back-.47,10.62)]
        prism_section(b,shape,x-.054,x+.054,TIMBER,label+' upper knee')


def dormer(b,x,lod):
    front=1.53;w=1.43;bottom=roof_height(front)-.04;apex=16.10
    f=Facade(b,(x-w,front),(x+w,front),'small gabled dormer')
    form=Polygon([(-w,bottom),(w,bottom),(w,15.12),(0,apex),(-w,15.12)])
    window=box(-1.04,bottom+.04,1.04,15.02)
    f.prism(form.difference(window),-.26,0,CREAM,'triangular plaster face')
    framed(f,window,'recessed dormer light',lod,4,[(bottom+.60,.05)])
    for sign in (-1,1):
        side=sign*(w+.15)
        peak=(x,front-.13,apex+.08)
        back_y=(apex+.08-11.38)/(HEIGHT-11.38)*(RIDGE+1.25)-1.25
        side_y=(15.06-11.38)/(HEIGHT-11.38)*(RIDGE+1.25)-1.25
        pts=[peak,(x+side,front-.13,15.06),(x+side,side_y,15.06),(x,back_y,apex+.08)]
        if sign<0:pts.reverse()
        roof_surface(b,pts,TILE,'pitched dormer roof')
        trim=Polygon([(0,apex+.10),(side,15.08),(side,14.94),(0,apex-.045)])
        f.prism(trim,.055,.18,CUT,'dormer bargeboard')


def plan_layer(b, plan, height, low, high, material, name):
    if not plan.is_empty:
        b.prism(plan,low,high,lambda x,y,d:(x,y,height(x,y)+d),material,name)


def tiled_pitch(b, plan, height, crosswise, lod, name):
    """Tile a planar roof polygon up to its actual valleys and front cut edge."""
    if plan.is_empty:
        return
    plan_layer(b,plan,height,-.095,.035,ROOF_SHADE,name+' tile bed')
    min_x,min_y,max_x,max_y=plan.bounds
    start,end=(min_y,max_y) if crosswise else (min_x,max_x)
    pitch=.33 if lod else .185
    def strip(lo,hi):
        return box(min_x,lo,max_x,hi) if crosswise else box(lo,min_y,hi,max_y)
    for k in range(floor(start/pitch),ceil(end/pitch)):
        a=k*pitch
        for lo,hi,first,last in [(a,a+pitch*.5,.048,.125),(a+pitch*.5,a+pitch,.125,.048)]:
            clipped=plan.intersection(strip(lo,hi))
            def crown(x,y):
                t=((y if crosswise else x)-lo)/(hi-lo)
                return height(x,y)+(1-t)*first+t*last
            plan_layer(b,clipped,crown,-.028,0,TILE,name+' convex tile channels')
    spacing=.55 if lod else .32
    start,end=(min_x,max_x) if crosswise else (min_y,max_y)
    for k in range(floor(start/spacing),ceil(end/spacing)):
        u=k*spacing
        band=box(u,min_y,u+.033,max_y) if crosswise else box(min_x,u,max_x,u+.033)
        plan_layer(b,plan.intersection(band),height,.069,.099,ROOF_SHADE,name+' tile overlaps')


def cross_gables(b,lod,eave):
    """Raised roof halves meet the original pitch along two converging valleys."""
    cuts=[]
    for centre,half,wall,base,peak in [(0,8.62,0,11.79,16.10),(-16.14,3.89,.48,11.68,14.87),(16.14,3.89,.48,11.68,14.87)]:
        back=wall+.29
        def underlying(z):
            return eave+(RIDGE-eave)*(z-11.38)/(HEIGHT-11.38)
        # The short apron in the frontal photos leaves the entire attic sill exposed.
        apron=box(centre-half,eave,centre+half,wall+.03)
        a0=roof_height(eave)
        tiled_pitch(b,apron,lambda x,y:a0+(base-.15-a0)*(y-eave)/(wall+.03-eave),
                    False,lod,'pediment apron')
        cuts.append(box(centre-half,eave,centre+half,back))
        for sign in (-1,1):
            def height(x,y):
                return peak-sign*(x-centre)*(peak-base)/half
            # At the front masonry the two pitches intersect inside the end of the gable.
            join=half*(peak-roof_height(back))/(peak-base)
            end=centre+sign*join
            plan=Polygon([(centre,back),(end,back),(centre,underlying(peak))])
            tiled_pitch(b,plan,height,True,lod,'pediment return')
            cuts.append(plan)
            # The tile canopy also covers the narrow back edge of the stone pediment.
            cap=box(min(centre,end),wall+.025,max(centre,end),back)
            tiled_pitch(b,cap,height,True,lod,'pediment return')
            b.tube([(end,back,roof_height(back)+.12),(centre,underlying(peak),peak+.12)],
                   .045,ROOF_SHADE,sides=5 if lod else 8,label='pediment valley flashing')
            # The strips at the two corners are still part of the main pitch.
            x0,x1=sorted((end,centre+sign*half))
            shelf=box(x0,wall+.03,x1,back)
            tiled_pitch(b,shelf,lambda x,y:roof_height(y),False,lod,'outer gable return')
    return unary_union(cuts)


def roof(b,lod):
    eave=-1.25
    occupied=cross_gables(b,lod,eave)
    main=box(-HALF,eave,HALF,RIDGE).difference(occupied)
    tiled_pitch(b,main,lambda x,y:roof_height(y),False,lod,'main roof')
    b.box((0,RIDGE,HEIGHT+.10),(2*HALF,.20,.15),TILE,label='rounded ridge tile course')
    for x in (-10.67,-4.95,4.95,10.67):dormer(b,x,lod)
    for x0,x1,ywall in [(-HALF,-8.10,.48),(-8.10,8.10,0),(8.10,HALF,.48)]:
        front=ywall-1.30
        b.box(((x0+x1)/2,(ywall+front)/2,11.10),(x1-x0,ywall-front,.19),CREAM,label='light painted projecting soffit')
        b.box(((x0+x1)/2,front,11.25),(x1-x0,.17,.24),TIMBER,label='continuous timber fascia')
        for idx in range(1,round((x1-x0)/.56)):
            u=x0+idx*.56
            b.box((u,(ywall+front)/2,10.97),(.105,ywall-front+.03,.13),TIMBER,label='exposed rafter ends')
    for x in [-19.64,-13.35,-7.83,-2.56,2.56,7.83,13.35,19.64]:
        y=.48 if abs(x)>8.11 else 0.
        for dx in [-.49,-.17,.17,.49]:
            traditional_bracket(b,x+dx,y,y-1.3,'group of four eaves brackets',lod)
