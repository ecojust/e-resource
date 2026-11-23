"""Blue and pale patterned glass under the street dial, as seen in the 2026 close view."""
from shapely.geometry import box,Polygon
from shapely.ops import unary_union
BLUE='blue floral clock glazing';PALE='pale green opalescent glazing'
PALETTE={BLUE:dict(color=[.086,.39,.59],roughness=.36),PALE:dict(color=[.40,.64,.65],roughness=.39)}
def add(f,q,i,lod,dark):
    x,z,r,t=q.bounds;w=r-x;h=t-z
    frame=q.difference(q.buffer(-.052,join_style=2))
    cuts=[box(x, z+h*j/4-.018,r,z+h*j/4+.018)for j in range(1,4)]
    if i==1:cuts.append(box((x+r)/2-.029,z,(x+r)/2+.029,t))
    f.prism(unary_union([frame,*cuts]),-.143,-.084,dark,'painted sash frame and crossrails')
    f.prism(q,-.188,-.165,PALE,'clouded pale panes')
    # Each original blue patch curls around pale almond-shaped areas. Curve contours
    # are an interpretation of the four visible rows, separated by actual sash bars.
    patches=[]
    for j in range(4):
        sy=z+j*h/4;dy=h/4
        for k in range(2 if i==1 else 1):
            span=w/(2 if i==1 else 1);sx=x+k*span;mirror=(i+k+j)%2
            xy=[(-.03,.11),(.19,.22),(.37,.56),(.56,.66),(.74,.53),(.99,.71),(1.04,.94),(.61,.89),(.42,.81),(.22,.64),(.14,.43),(-.03,.37)]
            if mirror:xy=[(1-a,b)for a,b in xy]
            poly=Polygon([(sx+a*span,sy+b*dy)for a,b in xy]);patches.append(poly.intersection(box(sx+.020,sy+.015,sx+span-.020,sy+dy-.015)))
    f.prism(unary_union(patches),-.161,-.152,BLUE,'blue floral glazing patches')
