"""Street-facing right wing of the Guangdong Theatre after the 2025 restoration."""
from math import cos, pi, sin, sqrt

COLORS = {
    'buff joints': (191,176,156), 'rose buff': (176,147,125), 'earth brown': (147,119,101),
    'dark umber': (127,105,88), 'cream brick': (194,170,141), 'cast stone': (195,190,175),
    'stone highlight': (213,207,190), 'steel': (64,68,66), 'steel highlight': (85,88,83),
    'slate reflection': (133,151,159), 'lower reflection': (91,105,108),
    'shadow glass': (108,124,132), 'panel field': (189,181,162),
    'panel brick': (157,132,109), 'coping': (105,108,103), 'coping edge': (145,148,137)
}
def linear(c):
    c=c/255
    return c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4
PALETTE = {k:{'color':[linear(c) for c in rgb], 'roughness':.34 if ('reflection' in k or 'glass' in k) else .87} for k,rgb in COLORS.items()}

def box(b,label,material,x0,x1,y0,y1,z0,z1):
    b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),material,label=label)
def prism(b,label,material,outline,front,back):
    # Each elevation slice is convex. Positive front normals face the street (-y).
    if sum(x*v-u*z for (x,z),(u,v) in zip(outline,outline[1:]+outline[:1]))<0:
        outline=list(reversed(outline))
    n=len(outline)
    pts=[(x,y,z)for y in (front,back)for x,z in outline]
    faces=[]
    for i in range(1,n-1):faces.extend(((0,i,i+1),(n,n+i+1,n+i)))
    for j in range(n):
        k=(j+1)%n
        faces.extend(((j,n+j,n+k),(j,n+k,k)))
    b.add(pts,faces,material,label)

WIDTH=3.95
SPRING=6.82
OPEN=.46
EDGE=.76
ARC=.48

def ring(b,label,material,inside,outside,front,back,n,gap=0):
    for i in range(n):
        a=pi*i/n+gap;c=pi*(i+1)/n-gap
        def polar(rad,t):return rad*cos(t), SPRING+(rad+ARC-OPEN)*sin(t)
        prism(b,label,material(i) if callable(material) else material,
              [polar(inside,a),polar(outside,a),polar(outside,c),polar(inside,c)],front,back)

def masonry(b,far):
    box(b,'Wall core behind the window assembly','buff joints',-1.975,1.975,.225,.39,0,9.16)
    for side in (-1,1):
        x0,x1=sorted((side*EDGE,side*1.975))
        box(b,'Masonry beside the arch','buff joints',x0,x1,.008,.235,0,9.16)
    # The mixed buff face brick has a pale vertical joint and irregular darker units in the photographs.
    row_h=.095 if not far else .172
    course=.155 if not far else .231
    for row in range(int(9.16/row_h)+1):
        z=row*row_h;zt=min(z+row_h-.011,9.16)
        if zt<=z:continue
        for col in range(-18,19):
            l=max(-1.975,col*course+(row%2)*course*.16+.007)
            r=min(1.975,(col+1)*course+(row%2)*course*.16-.006)
            if r<=l:continue
            if z<SPRING+EDGE+.025:
                ext=EDGE if z<SPRING else EDGE*sqrt(max(0,1-((z-SPRING)/(EDGE+.02))**2))
                if l<0<r:continue
                if l<0:r=min(r,-ext)
                else:l=max(l,ext)
                if r-l<.007:continue
            v=(row*43+col*17+row*col*5)%17
            tone='dark umber' if v<3 else 'earth brown' if v<8 else 'rose buff' if v<15 else 'cream brick'
            pts=[(l,0,z+.005),(r,0,z+.005),(r,0,zt),(l,0,zt)]
            b.add(pts,[(0,1,2),(0,2,3)],tone,'Face brick course '+str(row+1))
    # Concave arch-top wall is built from thin trapezoids spanning to the top.
    n=32 if not far else 20
    for i in range(n):
        a=pi*i/n;c=pi*(i+1)/n
        xa,za=EDGE*cos(a),SPRING+(EDGE+.02)*sin(a)
        xc,zc=EDGE*cos(c),SPRING+(EDGE+.02)*sin(c)
        prism(b,'Backing above arch','buff joints',[(xa,za),(xc,zc),(xc,9.16),(xa,9.16)],.009,.236)

def window_band(b,far):
    for sign in (-1,1):
        def strip(lo,hi,front,material):
            a,c=sorted((sign*lo,sign*hi))
            box(b,'Vertical course in the arched border',material,a,c,front,.16,0,SPRING)
        strip(OPEN,.515,-.045,'cast stone')
        strip(.515,.648,-.018,'buff joints')
        strip(.648,EDGE,-.065,'stone highlight')
        for i in range(56 if not far else 39):
            h=SPRING/(56 if not far else 39)
            a,c=sorted((sign*.534,sign*.632))
            box(b,'Brown units in upright inset band','panel brick',a,c,-.037,.04,i*h+.009,(i+1)*h-.009)
    n=48 if not far else 28
    ring(b,'Pale outer semicircle','stone highlight',.648,EDGE,-.065,.16,n)
    ring(b,'Mortar in curved soldier course','buff joints',.515,.650,-.018,.16,n)
    ring(b,'Short radial bricks','panel brick',.525,.635,-.037,.018,n,.006)
    ring(b,'Inner arched pale reveal','cast stone',OPEN,.516,-.045,.19,n)
    # The upper light is rounded. Its horizontal transom and central steel meeting stile are legible.
    ring(b,'Curved dark steel frame','steel',.412,OPEN,.037,.125,n)
    ring(b,'Semicircular fanlight glass','shadow glass',.00001,.413,.146,.165,n)
    for index,(lower,upper) in enumerate(((.39,1.82),(3.07,4.58),(5.77,SPRING))):
        for j,(lo,hi) in enumerate(((-.457,-.025),(.025,.457))):
            box(b,'Recessed glazing '+str(index+1),['lower reflection','slate reflection','slate reflection'][index],lo,hi,.146,.174,lower,upper)
        for x,k in ((-.438,.023),(.438,.023),(0,.024)):
            box(b,'Upright steel casement '+str(index+1),'steel',x-k,x+k,.039,.138,lower,upper)
        box(b,'Upper steel crossbar','steel',-.454,.454,.035,.141,upper-.047,upper+.003)
        if index!=2:
            box(b,'Shallow upper light transom','steel highlight',-.447,.447,.043,.136,upper-.225,upper-.185)
        box(b,'Pale sill and projecting end','cast stone',-.486,.486,-.081,.21,lower-.077,lower+.020)
    for lower,upper in ((0,.31),(1.82,3.0),(4.58,5.70)):
        box(b,'Pale apron panels between windows','panel field',-.46,.46,.023,.21,lower,upper)
        for x in (-.173,.173):
            n=max(2,round((upper-lower)/(.12 if not far else .16)))
            for i in range(n):
                z=lower+(upper-lower)*i/n
                box(b,'Short brown tile in spandrel upright','panel brick',x-.048,x+.048,-.014,.032,z+.009,z+(upper-lower)/n-.009)
        box(b,'Spandrel top bead','stone highlight',-.46,.46,-.026,.11,upper-.035,upper)

def cornice(b,far):
    for low,high,front,material in ((8.72,8.80,-.075,'cast stone'),(8.80,8.92,-.15,'stone highlight'),(8.92,9.15,-.11,'panel field'),(9.15,9.26,-.205,'coping'),(9.26,9.30,-.245,'coping edge')):
        box(b,'Projecting horizontal cornice',material,-1.975,1.975,front,.38,low,high)
    for i in range(31 if not far else 19):
        count=31 if not far else 19
        x=-1.91+(i+.5)*3.82/count
        box(b,'Uprights in narrow cornice frieze','cream brick',x-.028,x+.028,-.122,-.109,8.94,9.13)
def add_building(builder,lod=False):
    masonry(builder,lod)
    window_band(builder,lod)
    cornice(builder,lod)
