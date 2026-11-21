"""Street gate and the glazed timber entry documented in the September 2021 walk-through."""
from math import cos, pi, sin
from shapely.geometry import box, Polygon, LineString, Point
from shapely.ops import unary_union
from trefoil_arch import color, CHALK, LIMESTONE, FILLET, RECESS, LEAF, TIMBER, leaf

IRON='Jinling dark iron grilles'
TEAL='Jinling weathered green street gate'
BROWN='Jinling deep-red vestibule timber'
MILK='Jinling milky etched glazing'
UPPER='Jinling warm transom glazing'
STREET_MILK='Jinling shaded exterior ground glass'
STREET_UPPER='Jinling shaded street-side transom'
SHADOW='Jinling recessed doorway shade'
STEP='Jinling worn threshold stone'
PALETTE={k:{'color':color(v),'metallic':.34 if k in [IRON,TEAL] else 0.,
            'roughness':.55 if k in [MILK,UPPER,IRON,TEAL] else .77}for k,v in [
    (IRON,(62,58,51)),(TEAL,(43,87,77)),(BROWN,(100,62,46)),(MILK,(180,181,162)),
    (UPPER,(187,174,141)),(STREET_MILK,(92,98,90)),(STREET_UPPER,(113,107,91)),(SHADOW,(66,59,47)),(STEP,(157,151,138))]}

def round_lintel(x,z0,z1,w,r,quality):
    """Straight jambs flowing into the shallow rounded corners visible in the street photograph."""
    r=min(r,w*.30,(z1-z0)*.45)
    pts=[(x-w/2,z0),(x+w/2,z0),(x+w/2,z1-r)]
    n=12 if quality else 5
    for i in range(1,n+1):
        a=i/n*pi*.5
        pts.append((x+w/2-r+r*cos(a),z1-r+r*sin(a)))
    pts.append((x-w/2+r,z1))
    for i in range(1,n+1):
        a=pi/2+i/n*pi/2
        pts.append((x-w/2+r+r*cos(a),z1-r+r*sin(a)))
    return Polygon(pts)

def semicircle(x,z,w,height,steps):
    return Polygon([(x+w*.5*cos(k*pi/steps),z+height*sin(k*pi/steps))for k in range(steps+1)])

def scroll(front,name,points,diameter,material,y):
    front.profile(name,material,LineString(points).buffer(diameter*.5,quad_segs=2,join_style='round'),y,y+.024)

def glazed_door(front,x,w,h,y,detail,transom_base,transom_head):
    """Three arched transom lights and the wrought scroll pattern survive behind the outer gate."""
    outer=round_lintel(x,.09,h,w,.36,detail)
    top_of_leaves=transom_base-.15
    lights=[]
    step=w*.30
    for j in [-1,0,1]:
        span=w*(.343 if j==0 else .239)
        lights.append(semicircle(x+j*step,top_of_leaves+.15,span,transom_head-transom_base,18 if detail else 8))
    for k in [-1,1]:
        c=x+k*w*.241
        lights.append(box(c-w*.196,.30,c+w*.196,top_of_leaves-.10))
    front.profile('Vestibule joined timber frame',BROWN,outer.difference(unary_union(lights)),y-.10,y)
    for i,g in enumerate(lights):
        front.profile('Vestibule inner glass',UPPER if i<3 else MILK,g,y-.143,y-.136)
        front.profile('Vestibule arched transom' if i<3 else 'Door street glass',STREET_UPPER if i<3 else STREET_MILK,g,y-.135,y-.115)
        if i<3:continue
        a,b,c,d=g.bounds;cx=(a+c)/2
        if detail:
            # The 2021 closer photograph shows the paired inward curls at the
            # upper guard, a line of roundels at the meeting rail and straight uprights.
            for k in [-1,1]:
                offset=(c-a)*.19;radius=(c-a)*.15
                center=(cx+k*offset,d-(d-b)*.19)
                curl=[(center[0]+k*radius*cos(t),center[1]+radius*sin(t))for t in [i*pi/10 for i in range(18)]]
                tail=[(cx+k*(c-a)*.034,b+.16),(cx+k*(c-a)*.034,center[1]+.04)]
                scroll(front,'Door iron scroll',tail+list(reversed(curl)),.028,IRON,y+.018)
            for k in [-1.5,-.5,.5,1.5]:
                outer_ring=Point(cx+k*(c-a)*.224,b+(d-b)*.39).buffer((c-a)*.105,quad_segs=9)
                front.profile('Door iron roundels',IRON,outer_ring.difference(outer_ring.buffer(-.026)),y+.018,y+.045)
        else:
            front.box('Door plain centre bar',IRON,cx-.018,cx+.018,y+.008,y+.041,b,d)
    return outer

def street_gate(front,x,w,h,y,detail):
    """The two green outer leaves are held to the sides of the darker recessed entry."""
    face=y
    # Storefront photo 3 shows the two leaves to the sides of the entrance and
    # a central pedestrian gap. Limit the modelling behind them to the documented vestibule.
    for side in (-1,1):
        inner=x+side*w*.255
        edge=x+side*w*.479
        a,c=sorted((inner,edge))
        front.box('Green gate lower panel',TEAL,a,c,face-.067,face,.08,h*.483)
        for u in (a+.025,c-.025):
            front.box('Street gate metal stile',IRON,u-.025,u+.025,face-.065,face+.01,.08,h-.06)
        for z in (.24*h,.48*h,.94*h):
            front.box('Street gate horizontal rail',TEAL,a,c,face-.032,face+.014,z-.025,z+.025)
        for k in range(1,8 if detail else 5):
            u=a+(c-a)*k/(8 if detail else 5)
            front.box('Street gate upper grille',IRON,u-.012,u+.012,face-.045,face+.004,h*.475,h*.94)
    front.box('Central threshold',STEP,x-w/2+.055,x+w/2-.055,y-.71,y+.035,0,.068)

def carved_lintel(front,x,high,w,y,detail):
    """Stone cartouche between two spiralling shoulders over the wide central street entrance."""
    z=high+.235
    field=Point(x,z).buffer(1,quad_segs=24)
    from shapely.affinity import scale
    medallion=scale(field,xfact=.245,yfact=.157,origin=(x,z))
    front.profile('Entrance central oval medallion',LEAF,medallion,y+.07,y+.136)
    rim=medallion.boundary.buffer(.029,quad_segs=2)
    front.profile('Entrance oval moulding',FILLET,rim,y+.13,y+.171)
    for side in [-1,1]:
        pts=[(x+side*w*.38,z-.10),(x+side*w*.29,z-.07),(x+side*w*.20,z+.055),(x+side*w*.10,z+.064)]
        scroll(front,'Door floral stems',pts,.053,LEAF,y+.079)
        for k in range(4 if detail else 2):
            u=x+side*w*(.13+k*.063)
            leaf(front,'Carved entrance foliage',u,z-.037,.17,.12+.035*(k%2),y+.10,detail)
        if detail:
            u=x+side*w*.463
            curve=[(u+side*.14*cos(a),z-.066+.124*sin(a))for a in [i*pi/9 for i in range(17)]]
            scroll(front,'Lintel end volute',curve,.039,RECESS,y+.078)

def build(front,x,low,high,w,y,detail,transom_base,transom_head):
    hole=round_lintel(x,low,high,w,.26,True)
    outer=hole.buffer(.16,join_style='round').intersection(box(x-w,low,x+w,high+.22))
    front.profile('Street entrance dressed frame',LIMESTONE,outer.difference(hole),y-.12,y+.09)
    front.profile('Street entrance raised lip',FILLET,outer.boundary.buffer(.027,quad_segs=2).intersection(box(x-w,low+.023,x+w,high+.22)),y+.092,y+.125)
    inner_opening=round_lintel(x,.09,high-.12,w-.18,.36,detail)
    front.profile('Stone vestibule jamb returns and soffit',LIMESTONE,hole.difference(inner_opening),y-.815,y-.038)
    glazed_door(front,x,w-.18,high-.12,y-.78,detail,transom_base,transom_head)
    street_gate(front,x,w,high,y-.105,detail)
    carved_lintel(front,x,high,w,y,detail)
    return hole
