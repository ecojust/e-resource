"""Observed metal casements and paired glazed doors at the former canteen."""
from math import asin, cos, sin
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from shapely.geometry.polygon import orient
from hall_coordinates import point

FRAME = 'Canteen | brown-black fixed frame'
LEAF = 'Canteen | painted dark sash'
SEAL = 'Canteen | charcoal glazing bead'
SKY = 'Canteen | pale reflected sky in the upper light'
UPPER = 'Canteen | smoke grey reflective window glass'
GROUND = 'Canteen | shaded ground-floor window glass'
DOOR = 'Canteen | dark glass of the paired entrance doors'
PULL = 'Canteen | weathered satin metal door pull'
WOOD = 'Canteen | brown wooden street door'
RAISED_WOOD = 'Canteen | raised wooden door panels'
BEVEL = 'Canteen | bevelled wooden panel frames'

def finish(rgb, roughness, metallic=0.):
    rgb = [v/255. for v in rgb]
    return {'color':[v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in rgb],
            'roughness':roughness, 'metallic':metallic}

PALETTE = {
    FRAME:finish((62,60,56),.54,.19), LEAF:finish((76,72,66),.54,.17),
    SEAL:finish((54,52,48),.72,.02), SKY:finish((152,165,165),.27,.14),
    UPPER:finish((119,129,126),.31,.17), GROUND:finish((81,89,85),.35,.15),
    DOOR:finish((73,74,71),.34,.13), PULL:finish((149,133,106),.41,.52),
    WOOD:finish((82,61,51),.60), RAISED_WOOD:finish((95,71,57),.63), BEVEL:finish((110,83,66),.57),
}

def segment_profile(center, width, sill, spring, crown, segments=24):
    """Section of a circular segment from its measured chord and sagitta."""
    half = width/2
    rise = crown-spring
    if not 0 < rise < half or not sill < spring:
        raise ValueError('Window head requires a positive segmental rise below half its span')
    radius = (half*half+rise*rise)/(2*rise)
    angle = asin(half/radius)
    head = [(center+radius*sin(angle*(1-2*i/segments)),
             crown-2*radius*sin(angle*(1-2*i/segments)/2)**2)
            for i in range(segments+1)]
    head[0],head[-1]=(center+half,spring),(center-half,spring)
    return Polygon([(center-half,sill),(center+half,sill),*head])

def _raised_field(b,face,poly,depth,width,label):
    """Cut the timber face back around each field with a real sloping bevel."""
    paper=orient(poly,sign=1.)
    contour=list(paper.exterior.coords)[:-1]
    cx,cz=paper.centroid.coords[0];x0,z0,x1,z1=paper.bounds
    edge=.014*width
    scale_x=1-2*edge/(x1-x0);scale_z=1-2*edge/(z1-z0)
    bottom=[point(face,u,depth+.009,z) for u,z in contour]
    top=[point(face,cx+(u-cx)*scale_x,depth-.009,cz+(z-cz)*scale_z) for u,z in contour]
    count=len(contour)
    vertices=bottom+top+[point(face,cx,depth+.009,cz),point(face,cx,depth-.009,cz)]
    faces=[]
    for i in range(count):
        j=(i+1)%count
        faces.extend([(2*count,j,i),(2*count+1,count+i,count+j),(i,j,count+j,count+i)])
    b.add(vertices,faces,RAISED_WOOD,label)

def add_window(b, face, number, level, opening, lod=False):
    """Fit a two-leaf sash or double door to one shared masonry opening."""
    center,width,sill,spring,crown=(float(opening[k]) for k in ('center','width','sill','spring','crown'))
    paired = opening['kind']=='double-door'
    street_door = opening['kind']=='street-door'
    level_name = str(level)
    prefix = f'{face[:2].upper()}{number} {level_name} '
    # The outside face of the frame sits just inside the stone/brick reveal.
    recess = float(opening.get('frame_recess', .13 if paired else (.105 if street_door else .055)))
    def solid(poly, front, thick, material, title):
        b.prism(poly,-front-thick,-front,
                lambda u,z,d:point(face,u,-d,z),material,prefix+title)
    outside = segment_profile(center,width,sill,spring,crown,12 if lod else 28)
    # The outer fixed jamb meets the masonry behind its visible front arris.
    jamb = width*(.029 if paired else .034)
    inside = outside.buffer(-jamb,join_style='mitre')
    solid(outside.difference(inside),recess,.074,FRAME,'fixed segmental frame')
    h = crown-sill
    if street_door:
        left,bottom,right,_ = inside.bounds
        inset = outside.buffer(-.110*width,join_style='mitre')
        for i,(lo,hi) in enumerate(((left,center-.002*width),(center+.002*width,right))):
            name=('left','right')[i]
            leaf=inside.intersection(box(lo,bottom,hi,crown))
            solid(leaf,recess+.011,.055,WOOD,name+' arched wooden leaf')
            a,c=(center-width*.392,center-width*.073) if not i else (center+width*.073,center+width*.392)
            panel_rows=((.076,.307),(.372,.605),(.665,1.))
            for j,(za,zb) in enumerate(panel_rows):
                panel=box(a,sill+za*h,c,sill+zb*h).intersection(inset)
                step=panel.buffer(-.014*width,join_style='mitre')
                core=step.buffer(-.012*width,join_style='mitre')
                title=f'{name} panel {j+1}'
                solid(panel.difference(step),recess+.004,.012,BEVEL,title+' outer fillet')
                if not lod:
                    solid(step.difference(core),recess+.010,.010,WOOD,title+' recessed border')
                _raised_field(b,face,core,recess+.006,width,prefix+title+' raised field')
        solid(inside.intersection(box(center-.003*width,bottom,center+.003*width,crown)),
              recess+.035,.028,SEAL,'meeting joint')
        _handles(b,face,prefix,center,width,sill,h,recess,lod,True)
        return
    mid_rail = sill+h*(.838 if paired else .795)
    rail_thick = (.052 if paired else .050)*width
    left,bottom,right,_=inside.bounds
    x0,x1=center-width/2,center+width/2
    rail_lo,rail_hi=mid_rail-rail_thick/2,mid_rail+rail_thick/2
    solid(inside.intersection(box(x0,rail_lo,x1,rail_hi)),
          recess+.001,.063,FRAME,'transom')
    # Each photographed arched light is a single sheet across the opening.
    head = inside.intersection(box(x0,rail_hi,x1,crown+.01))
    upper = level in (2,'2','upper','upper-storey') or sill>3.
    head_mat = SKY if upper else (DOOR if paired else GROUND)
    solid(head,recess+.041,.009,head_mat,'one-piece arched upper light')
    # From sill upwards the two bars subdivide each leaf into three lights.
    # The door has wider side/bottom rails and much heavier horizontal rails.
    rim = width*(.044 if paired else .018)
    meeting = width*(.070 if paired else .058)
    bar = width*(.047 if paired else .020)
    foot = width*(.046 if paired else .024)
    glass_mat = DOOR if paired else (UPPER if upper else GROUND)
    for i,(lo,hi) in enumerate(((left,center),(center,right))):
        a = lo+(rim if i==0 else meeting/2)
        c = hi-(meeting/2 if i==0 else rim)
        gl_bottom,gl_top=bottom+foot,rail_lo-rim
        z1=gl_bottom+(gl_top-gl_bottom)/3
        z2=gl_bottom+2*(gl_top-gl_bottom)/3
        panes=[box(a,bl,c,tp) for bl,tp in (
            (gl_bottom,z1-bar/2),(z1+bar/2,z2-bar/2),(z2+bar/2,gl_top))]
        margin = .002*width
        outer = box(lo+(margin if i else 0),bottom,hi-(margin if not i else 0),rail_lo)
        label = 'right' if i else 'left'
        solid(outer.difference(unary_union(panes)),recess+.010,.050,LEAF,label+' three-light leaf')
        for j,pane in enumerate(panes):
            if not lod:
                pane_clear=pane.buffer(-min(.007*width,.010),join_style='mitre')
                solid(pane.difference(pane_clear),recess+.032,.011,SEAL,f'{label} bead {j+1}')
            else:
                pane_clear=pane
            solid(pane_clear,recess+.045,.007,glass_mat,f'{label} pane {j+1}')
    solid(box(center-.0022*width,bottom,center+.0022*width,rail_lo),
          recess+.035,.028,SEAL,'meeting stile seam')
    if paired:
        _handles(b,face,prefix,center,width,sill,h,recess,lod)

def _handles(b,face,prefix,center,width,sill,h,recess,lod,street_door=False):
    # Both pull handles turn back into their respective leaf at each end.
    for sign,name in ((-1,'left'),(1,'right')):
        x=center+sign*(.044 if street_door else .039)*width
        z=sill+(.488 if street_door else .348)*h
        half=(.084 if street_door else .061)*h
        return_depth=min(.059,width*.035)
        end=recess+.012
        mid=end-return_depth
        pts=[point(face,x,d,z+dz) for d,dz in
             ((end,-half),(mid+.012,-half+.012),(mid,-half+.030),
              (mid,half-.030),(mid+.012,half-.012),(end,half))]
        b.tube(pts,max(.009,min(.017,width*.008)),PULL,7 if lod else 12,prefix+name+' door pull')
