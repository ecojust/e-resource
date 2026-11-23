"""Street-facing timber oriel and shallow arch at 121 Yanqing Road, from the 2018 photograph.

Metres. Origin is the arch centre projected onto the adjoining brick frontage.
X runs towards the southwest, Y into the building and Z up from the pavement.
Call add_western_bay(builder, lod). Merge PALETTE with the building palette.
"""
from math import cos, hypot, pi, sin
from shapely.geometry import LineString, Polygon, box

WALL_LEFT, WALL_RIGHT = -1.43, 1.25
POST_LEFT, POST_RIGHT = -.95, .60
CROWN, SPRING, HALF_CLEAR = 2.95, 2.31, 1.055
CREAM, DARK, TIMBER, BLUE, GREEN, CLAY = (
    '121 bay | light sand render', '121 bay | charcoal trim',
    '121 bay | oxblood timber', '121 bay | reflected casement',
    '121 bay | painted panels', '121 bay | grey brown roofing',
)
def finish(rgb, roughness):
    def linear(value):
        s=value/255
        return s/12.92 if s<=.04045 else ((s+.055)/1.055)**2.4
    return dict(color=[linear(c) for c in rgb],roughness=roughness)

PALETTE={
    CREAM:finish((205,192,168),.90), DARK:finish((60,60,58),.81),
    TIMBER:finish((107,60,48),.72), BLUE:finish((70,84,94),.32),
    GREEN:finish((46,66,58),.71), CLAY:finish((101,91,82),.88),
}

def arch(half_width, spring, crown, bottom, count):
    top=[(half_width*cos(i*pi/count),spring+(crown-spring)*sin(i*pi/count)) for i in range(count+1)]
    return Polygon([(-half_width,bottom),(half_width,bottom),*top])

def extrusion(builder,polygon,front,back,material,label):
    # (u,z,d) points towards the street as d increases.
    builder.prism(polygon,-back,-front,lambda u,z,d:(u,-d,z),material,label)

def flat_face(builder, start, end):
    dx,dy=end[0]-start[0],end[1]-start[1]
    length=hypot(dx,dy)
    ux,uy=dx/length,dy/length
    def draw(shape,lo,hi,material,label):
        builder.prism(shape,lo,hi,lambda u,z,d:(start[0]+ux*u+uy*d,start[1]+uy*u-ux*d,z),material,label)
    return length,draw

def brace(draw,a,b,width,material,label,lo=.018,hi=.065):
    draw(LineString([a,b]).buffer(width/2,cap_style=2),lo,hi,material,label)

def add_western_bay(b,lod=False):
    if hasattr(b,'palette'):
        b.palette.update({k:dict(v) for k,v in PALETTE.items() if k not in b.palette})
    n=18 if lod else 32
    outer=arch(HALF_CLEAR+.145,SPRING,CROWN+.15,0,n)
    opening=arch(HALF_CLEAR,SPRING,CROWN,0,n)
    shell=box(WALL_LEFT,0,WALL_RIGHT,3.73)
    extrusion(b,shell.difference(outer),1.13,1.46,CREAM,'west bay | sandstone-coloured portal')
    extrusion(b,outer.difference(opening),1.095,1.48,CREAM,'west bay | rounded intrados')
    dark_arch=arch(HALF_CLEAR+.19,SPRING,CROWN+.195,0,n)
    extrusion(b,dark_arch.difference(outer),1.08,1.14,DARK,'west bay | narrow dark outer arch band')
    extrusion(b,Polygon([(-.090,3.07),(.090,3.07),(.145,3.29),(-.145,3.29)]),1.052,1.145,DARK,'west bay | central dark keystone')
    for a,z in ((WALL_LEFT,-HALF_CLEAR), (HALF_CLEAR,WALL_RIGHT)):
        extrusion(b,box(a,0,z,.24),1.052,1.14,DARK,'west bay | foot of jamb')
    # The photographed two leaves and the shadowed louvre transom occupy a recessed plane.
    gate=arch(HALF_CLEAR-.035,SPRING,CROWN-.055,.025,n)
    extrusion(b,gate,1.54,1.61,DARK,'west bay | deep painted iron opening')
    for i,(a,z) in enumerate([(-1.00,-.025),(.025,1.00)]):
        extrusion(b,box(a,.06,z,2.12),1.48,1.54,GREEN,'west bay | painted leaf')
        for h in (.12,.66,1.62,2.03):
            extrusion(b,box(a+.035,h,z-.035,h+.035),1.46,1.485,GREEN,'west bay | horizontal metal framing')
        for j in range(1,7 if lod else 11):
            u=a+(z-a)*j/(7 if lod else 11)
            extrusion(b,box(u-.008,.14,u+.008,2.01),1.453,1.486,GREEN,'west bay | pressed leaf ribs')
    for i in range(7):
        bottom=2.16+i*.102
        strip=box(-1.04,bottom,1.04,bottom+.038).intersection(gate)
        if not strip.is_empty:
            extrusion(b,strip,1.455,1.52,GREEN,'west bay | recessed transom slat')
    # A short east-side reveal turns from the brick wall to the recessed doorway.
    b.box((WALL_LEFT+.068,.573,1.86),(.136,1.155,3.72),CREAM,label='west bay | eastern return to street wall')
    # The photographed brick quoin ends at -1.72. Only the recessed, cream join to the arch is included here.
    b.box(((-1.72+WALL_LEFT)/2,1.204,1.86),(WALL_LEFT+1.72,.15,3.72),CREAM,label='west bay | narrow plaster joint behind brick quoin')
    rear_left=(WALL_LEFT,1.36);rear_right=(WALL_RIGHT,1.36)
    left=(POST_LEFT,.72);right=(POST_RIGHT,.72)
    oriel_outline=Polygon([rear_left,left,right,rear_right])
    b.plan_prism(oriel_outline,3.63,3.76,DARK,'west bay | projecting timber sill')
    b.plan_prism(oriel_outline,6.48,6.60,TIMBER,'west bay | oriel plate')
    for face,(start,end) in enumerate([(rear_left,left),(left,right),(right,rear_right)]):
        length,draw=flat_face(b,start,end)
        field=box(0,3.74,length,6.49)
        # In 2018 the front has a single narrow casement left of a broad opaque panel.
        # The 2015 pair shown in the measuring photographs only sets the unchanged timber frame.
        glass=box(.18,4.70,.81,6.09) if face==1 else None
        draw(field if glass is None else field.difference(glass),-.115,0,CREAM,'west bay | rendered oriel panel')
        if glass is not None:
            draw(glass,-.095,-.055,BLUE,'west bay | recessed blue-grey casement')
            draw(glass.boundary.buffer(.024,join_style=2),-.019,.020,DARK,'west bay | steel casement frame')
            for z in (5.15,5.64):
                draw(box(.19,z-.012,.80,z+.012),-.031,.009,DARK,'west bay | low steel glazing bars')
            draw(box(.487,4.71,.509,6.08),-.031,.009,DARK,'west bay | vertical steel glazing bar')
        for z,h in ((3.73,.092),(4.405,.067),(6.15,.085),(6.46,.095)):
            draw(box(0,z-h/2,length,z+h/2),0,.053,TIMBER,'west bay | exposed horizontal timber')
        cells=2 if face==1 else 1
        for j in range(cells):
            a=length*j/cells+.021;z=length*(j+1)/cells-.021
            brace(draw,(a,3.79),(z,4.366),.066,TIMBER,'west bay | diagonal saltire ascending')
            brace(draw,(a,4.366),(z,3.79),.066,TIMBER,'west bay | diagonal saltire descending',.013,.051)
        if face==1:
            u=length/2;draw(box(u-.035,3.76,u+.035,4.4),.013,.07,TIMBER,'west bay | centre rail post')
        draw(box(0,3.68,.076,6.51),.012,.078,TIMBER,'west bay | upright at panel joint')
        if face==2:
            draw(box(length-.065,3.70,length,6.51),.012,.066,TIMBER,'west bay | end post')
            # Shallow corrugated hood visible over the west return on the published photograph.
            for i in range(1 if lod else 9):
                count=1 if lod else 9
                a,bx=length*i/count,length*(i+1)/count
                def hood_point(u,d,z):
                    dx=(end[0]-start[0])/length;dy=(end[1]-start[1])/length
                    return(start[0]+dx*u+dy*d,start[1]+dy*u-dx*d,z)
                ridge=.0 if i%2==0 else .014
                top=[hood_point(a,.02,6.12+ridge),hood_point(bx,.02,6.12+ridge),hood_point(bx,.285,5.81+ridge),hood_point(a,.285,5.81+ridge)]
                b.add(top+[(x,y,z-.035) for x,y,z in top],[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],CREAM,'west bay | fluted side hood')
    centre=-.14;ea,wa=-1.43,1.27;eave=6.80;ridge=8.13
    extrusion(b,Polygon([(ea,eave),(wa,eave),(centre,ridge)]),.76,1.50,DARK,'west bay | shaded triangular gable')
    for a,bx,za,zb in [(ea,centre,eave,ridge),(centre,wa,ridge,eave)]:
        tilt=Polygon([(a,za-.108),(bx,zb-.108),(bx,zb+.024),(a,za+.024)])
        extrusion(b,tilt,.52,1.73,CLAY,'west bay | separate sloping roof edge')
    extrusion(b,box(ea,6.62,wa,6.75),.69,1.52,DARK,'west bay | upper cornice shadow')
