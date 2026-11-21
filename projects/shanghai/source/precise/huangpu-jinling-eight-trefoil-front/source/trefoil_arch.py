"""Blind ogival tympana and shallow-cut stone capitals above the street windows at No. 8."""
from math import atan2, cos, pi, sin
from shapely.geometry import Point, Polygon, box, LineString
from shapely.ops import unary_union

def color(rgb):
    def convert(v):
        v=v/255.
        return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
    return [convert(v)for v in rgb]

CHALK='Jinling warm lime finish'
LIMESTONE='Jinling pale window stone'
FILLET='Jinling projecting stone arris'
RECESS='Jinling shadowed moulding'
LEAF='Jinling carved leaf face'
TIMBER='Jinling red-brown joinery'
GLASS='Jinling upper dark window'
PALETTE={k:{'color':color(c),'roughness':r}for k,c,r in [
    (CHALK,(198,193,180),.90),(LIMESTONE,(185,180,165),.87),
    (FILLET,(216,209,192),.86),(RECESS,(157,151,136),.90),
    (LEAF,(203,197,179),.86),(TIMBER,(106,68,61),.68),(GLASS,(83,87,84),.36)]}

def ogive(x,z,half,rise,steps):
    """Profile of two circular arcs tangent to the springing at either jamb."""
    c=(rise*rise-half*half)/(2*half)
    radius=half+c
    angle=atan2(rise,c)
    arc=[(x-c+radius*cos(angle*i/steps),z+radius*sin(angle*i/steps))for i in range(steps+1)]
    arc[-1]=(x,z+rise)
    return Polygon([*arc,*[(2*x-u,v) for u,v in reversed(arc[:-1])]])

def trefoil(x,z,width):
    """Three tangent lobes, one above two, with the cusp at their common heart."""
    rad=width*.24
    centres=[(x,z+rad*1.13),(x-rad*.98,z-rad*.57),(x+rad*.98,z-rad*.57)]
    return unary_union([Point(a,b).buffer(rad,quad_segs=10)for a,b in centres])

def leaf(front,name,x,z,w,h,y,detail):
    # A shallow exposed stone leaf fans outward from a stalk. Its centre vein
    # is a real ridge higher than its folded edges.
    outline=[(x,z),(x-w*.38,z+h*.30),(x-w*.45,z+h*.67),(x-w*.20,z+h*.94),
             (x,z+h),(x+w*.20,z+h*.94),(x+w*.45,z+h*.67),(x+w*.38,z+h*.30)]
    if not detail or min(u for u,v in outline)<front.extent[0] or max(u for u,v in outline)>front.extent[1]:
        front.profile(name,LEAF,Polygon(outline),y,y+.032)
        return
    n=len(outline)
    vertices=[(u,y,v) for u,v in outline]+[(x,y+.065,z+h*.60)]
    faces=[tuple(reversed(range(n)))]+[(i,(i+1)%n,n)for i in range(n)]
    # Outline is clockwise in X,Z and therefore has its front along +Y.
    front.builder.add(vertices,faces,LEAF,name)

def capital(front,name,x,z,width,y,detail):
    w=width
    # Abacus steps wider at the top of the little foliate pier.
    shape=Polygon([(x-w*.35,z),(x+w*.35,z),(x+w*.39,z+.08),(x+w*.49,z+.18),
                   (x+w*.5,z+.29),(x-w*.5,z+.29),(x-w*.49,z+.18),(x-w*.39,z+.08)])
    front.profile(name+' capital block',LIMESTONE,shape,y-.095,y+.085)
    front.box(name+' abacus',FILLET,x-w*.54,x+w*.54,y-.075,y+.142,z+.26,z+.315)
    count=5 if detail else 3
    for i in range(count):
        dx=(i-(count-1)/2)*w*.74/count
        leaf_width=w*.93/count
        leaf(front,name+' foliage relief',x+dx,z+.045,leaf_width,.20,y+.085,detail)
        if detail:
            side=-1 if i<count//2 else 1
            cx=x+dx
            stem=[(cx-side*leaf_width*.16,z+.063),(cx-side*leaf_width*.08,z+.116),
                  (cx+side*leaf_width*.10,z+.160),(cx+side*leaf_width*.21,z+.183)]
            curl=[(cx+side*leaf_width*(.12+.15*cos(a)),z+.190+.021*sin(a))
                  for a in [j*pi/10 for j in range(16)]]
            vein=LineString(stem+curl).buffer(.006,quad_segs=2)
            front.profile(name+' curled leaf veins',FILLET,vein,y+.129,y+.150)


def model(front,name,x,sill,head,apex,width,y,detail,glass_head=None):
    """Add one window and its blind arch. Return only the true rectangular opening."""
    half=width/2
    reveal=.17
    glass_head=head-.34 if glass_head is None else glass_head
    opening=box(x-half,sill,x+half,head)
    field=ogive(x,head,half,apex-head,24 if detail else 12)
    front.profile(name+' blind tympanum',CHALK,field,y-.13,y+.016)
    # The photograph shows a narrow raised outer hood and broad strip of stone,
    # followed by a darker incision around its blind infill.
    for label,w,low,high,mat in [('hood band',.095,y+.008,y+.079,LIMESTONE),
                                 ('outer bead',.036,y+.074,y+.121,FILLET),
                                 ('inner incision',.028,y+.018,y+.039,RECESS)]:
        profile=field if label!='inner incision'else ogive(x,head+.016,half-.11,apex-head-.16,18 if detail else 9)
        border=profile.boundary.buffer(w*.5,quad_segs=2).intersection(box(x-half-.15,head+.011,x+half+.15,apex+.15))
        front.profile(name+' '+label,mat,border,low,high)
    ornament=trefoil(x,head+.34*(apex-head),width*.49)
    if detail:
        front.profile(name+' trefoil cut',RECESS,ornament.boundary.buffer(.034,quad_segs=2),y+.020,y+.042)
        front.profile(name+' trefoil rim',FILLET,ornament.boundary.buffer(.014,quad_segs=2),y+.042,y+.063)
    else:
        front.profile(name+' trefoil outline',LIMESTONE,ornament.boundary.buffer(.035,quad_segs=2),y+.017,y+.059)
    # The photographed upper red joinery panel lies under the blind carved arch.
    front.box(name+' red lintel',TIMBER,x-half+.025,x+half-.025,y-reveal,y-.09,glass_head,head-.013)
    front.box(name+' dark window glass',GLASS,x-half+.025,x+half-.025,y-.30,y-.25,sill+.03,glass_head+.01)
    rim=opening.difference(box(x-half+.062,sill+.065,x+half-.062,head-.061))
    front.profile(name+' timber casing',TIMBER,rim,y-.26,y-.13)
    if detail:
        lower=box(x-half+.07,glass_head+.029,x+half-.07,head-.047)
        edge=lower.difference(lower.buffer(-.019,join_style='mitre'))
        front.profile(name+' lintel panel',RECESS,edge,y-.09,y-.072)
        front.box(name+' steel guard',TIMBER,x-half+.014,x+half-.014,y+.025,y+.05,sill+.80,sill+.839)
    front.box(name+' sill stone',FILLET,x-half-.11,x+half+.11,y-.12,y+.132,sill-.075,sill+.012)
    return opening
