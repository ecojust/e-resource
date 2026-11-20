"""The two numbered doors and shared street gable of the Yongkang Road terrace."""
from math import cos, pi, sin

from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

from photo_architecture import Facade

WALL = 'sand coloured roughcast'
TRIM = 'cream render moulding'
BASE = 'charcoal plinth'
BRICK = 'burgundy brick'
TILE = 'weathered clay pantile'
SHADOW = 'deep shaded render'
TIMBER = 'brown wooden doors'
SASH = 'dark painted steel'
GLASS = 'blue grey glass'
IRON = 'grey security bars'
GREEN = 'enamel house plate'
WHITE = 'ivory enamel digits'
BLUE = 'blue community plaque'
PALETTE = {
    key: {'color':rgb,'roughness':rough}
    for key,rgb,rough in [
        (WALL,[.68,.576,.41],.93), (TRIM,[.75,.655,.493],.89),
        (BASE,[.246,.251,.239],.92), (BRICK,[.411,.231,.166],.83),
        (TILE,[.53,.284,.177],.85), (SHADOW,[.315,.263,.196],.91),
        (TIMBER,[.27,.205,.153],.73), (SASH,[.169,.177,.164],.76),
        (GLASS,[.237,.29,.303],.30), (IRON,[.364,.378,.356],.57),
        (GREEN,[.055,.272,.213],.63),(WHITE,[.858,.849,.734],.65),
        (BLUE,[.144,.233,.317],.68)
    ]}
LEFT = -3.63
RIGHT = 4.18
DEPTH = 1.75
DOORS = [(-.565, .815),(.535, .835)]
MID = [(-.86,1.01),(.905,.97)]
UPPER = [(-.59,.99),(1.00,1.01)]
WALL_OUTLINE = [
    (LEFT,0),(RIGHT,0),(RIGHT,9.49),(3.44,9.54),(3.44,10.47),
    (2.37,10.47),(2.37,10.25),(.92,10.25),(.83,10.66),
    (.57,10.69),(.39,10.43),(-1.23,10.43),(-1.23,10.84),
    (-1.91,10.84),(-1.91,9.89),(LEFT,9.48)]
DIGITS = {
  '1': [[(-.15,.30),(.08,.49),(.08,-.47)],[(-.17,-.47),(.26,-.47)]],
  '8': [[(0,.02),(-.27,.18),(-.26,.38),(0,.48),(.23,.39),(.25,.18),(0,.02),
         (-.28,-.14),(-.25,-.39),(0,-.49),(.25,-.39),(.28,-.14),(0,.02)]],
  '3': [[(-.24,.37),(0,.48),(.26,.34),(.21,.15),(-.01,.01),(.21,-.08),
         (.27,-.28),(.11,-.46),(-.11,-.46),(-.28,-.36)]]
}


def arch(cx, width, spring, bottom=0.0, divisions=32):
    r=width/2
    curve=[(cx+r*cos(pi*i/divisions),spring+r*sin(pi*i/divisions)) for i in range(divisions+1)]
    return Polygon([(cx-r,bottom),(cx+r,bottom),*curve])


def arc_band(cx, spring, inner, outer, n=40):
    outside=[(cx+outer*cos(pi*i/n),spring+outer*sin(pi*i/n))for i in range(n+1)]
    inside=[(cx+inner*cos(pi*i/n),spring+inner*sin(pi*i/n))for i in reversed(range(n+1))]
    return Polygon(outside+inside)


def plaque(f, cx, z, number):
    f.box(cx,z,.279,.168,.021,.028,GREEN,'house number '+number)
    for j,digit in enumerate(number):
        for line in DIGITS[digit]:
            pts=[(cx+(j-1)*.064+x*.078,z+y*.098)for x,y in line]
            mark=LineString(pts).buffer(.0055,cap_style='round',join_style='round',quad_segs=2)
            f.prism(mark,.039,.045,WHITE,'painted address '+number)


def door_leaf(f,cx,width,lod):
    leaf=arch(cx,width-.065,1.485,.045,18 if lod else 36)
    f.prism(leaf,-.337,-.311,TIMBER,'arched recessed timber leaf')
    inset=leaf.buffer(-.065,join_style='round')
    f.prism(leaf.difference(inset),-.307,-.286,SASH,'dark timber stop')
    for xx in [-.176,.176]:
        for z,h in [(.45,.56),(1.11,.55)]:
            panel=box(cx+xx-.125,z-h/2,cx+xx+.125,z+h/2)
            f.prism(panel.difference(panel.buffer(-.018,join_style='mitre')),-.308,-.284,
                    TIMBER,'raised door panel')
    f.box(cx-width*.32,.91,.028,.078,.035,-.264,IRON,'door handle')
    f.box(cx,.025,width-.01,.05,.22,-.155,BASE,'threshold')


def tile_canopy(f,cx,bottom,width,lod):
    n=max(5,round(width/.134));pitch=width/n
    f.box(cx,bottom,width,.085,.235,.134,BRICK,'shade bearer')
    for i in range(n):
        u=cx-width/2+(i+.5)*pitch
        outer=pitch*.48
        f.prism(arc_band(u,bottom+.022,outer*.60,outer,5 if lod else 10),
                .025,.285,TILE,'hollow curved window tiles')


def sash(f, cx, width, bottom, height, barred, lod):
    inner=box(cx-width/2,bottom,cx+width/2,bottom+height)
    f.prism(inner,-.173,-.153,GLASS,'recessed casement glass')
    stops=inner.difference(inner.buffer(-.047,join_style='mitre'))
    bars=[box(cx-.022,bottom,cx+.022,bottom+height)]
    for z in (bottom+height*.37,bottom+height*.68):
        bars.append(box(cx-width/2,z-.013,cx+width/2,z+.013))
    f.prism(unary_union([stops,*bars]),-.139,-.098,SASH,'casement frame and muntins')
    f.box(cx,bottom-.04,width+.13,.087,.19,.033,BRICK,'brick window sill')
    if barred:
        n=6 if lod else 8
        for i in range(n):
            x=cx-width*.45+i*width*.90/(n-1)
            f.box(x,bottom+height/2,.012,height-.035,.022,.055,IRON,'external vertical bars')
        f.box(cx,bottom+height*.52,width-.025,.017,.025,.060,IRON,'security rail crosspiece')


def add_housefront(builder,lod):
    f=Facade(builder,[-1,0],[1,0],'Yongkang 181-183')
    openings=[arch(x,w,1.50,-.02,20 if lod else 40)for x,w in DOORS]
    for row,low,h in [(MID,3.70,1.08),(UPPER,7.30,1.11)]:
        openings.extend(box(x-w/2,low,x+w/2,low+h)for x,w in row)
    outline=Polygon(WALL_OUTLINE)
    holes=unary_union(openings)
    f.prism(outline.difference(holes),-DEPTH,0,WALL,'roughcast wall, six openings')
    # A recessed closed backing stops the view at each actual wooden door or window.
    for x,w in DOORS:door_leaf(f,x,w,lod)
    f.prism(box(LEFT,0,RIGHT,.165).difference(holes),-.041,.011,BASE,'painted street plinth')
    for x,w in MID:sash(f,x,w,3.70,1.08,x>0,lod)
    for x,w in UPPER:sash(f,x,w,7.30,1.11,False,lod)
    for z in [4.99,8.56]:
        tile_canopy(f,.045,z,2.91,lod)
    # The crimson horizontal course separates the middle and upper windows.
    f.box((LEFT+RIGHT)/2,5.82,RIGHT-LEFT,.188,.082,.045,BRICK,'brick string course')
    if not lod:
        for z in (5.77,5.85):f.box((LEFT+RIGHT)/2,z,RIGHT-LEFT,.009,.014,.09,TRIM,'mortar bed')
        for i in range(36):
            x=LEFT+(i+.58)*(RIGHT-LEFT)/36
            f.box(x,5.82,.009,.16,.011,.09,TRIM,'brick perpends')
    # The single tiled archivolt springs outside the two small door arches.
    spring=1.52;inner=1.267
    for ri,ro,back,front in [(inner,inner+.056,.025,.168),
                              (inner+.055,inner+.112,.023,.131),
                              (inner+.111,inner+.169,.019,.102)]:
        f.prism(arc_band(.02,spring,ri,ro),back,front,TRIM,'three archivolt mouldings')
    # Individually hollow clay caps turn with the outer curve.
    n=24 if lod else 30;radius=1.44
    for i in range(n):
        angle=pi*(i+.5)/n
        contact=(.02+radius*cos(angle),spring+radius*sin(angle));r=radius*sin(pi/(2*n))*.96
        seg=5 if lod else 10
        def pt(theta,rad):
            along=rad*cos(theta);out=rad*sin(theta)
            return (contact[0]-along*sin(angle)+out*cos(angle),
                    contact[1]+along*cos(angle)+out*sin(angle))
        shell=Polygon([pt(pi*j/seg,r)for j in range(seg+1)]+
                      [pt(pi*j/seg,r*.65)for j in reversed(range(seg+1))])
        f.prism(shell,.044,.276,TILE,'turned barrel tile on arch')
    for x in [-1.76,1.80]:
        for z,wi,hi,pr in [(1.42,.57,.095,.071),(1.51,.67,.088,.112),(1.59,.74,.078,.154)]:
            f.box(x,z,wi,hi,pr,pr/2,TRIM,'stepped impost')
    # These shallow upper piers, cropped at the roofline, bound the street-facing roof screen.
    for cx,width,top in [(-1.57,.676,10.84),(2.89,1.032,10.47)]:
        f.box(cx,(top+5.97)/2,width,top-5.97,.052,.028,WALL,'projecting parapet pier')
        f.box(cx,top-.026,width+.063,.075,.14,.041,TRIM,'parapet coping')
    for i,width in enumerate([.48,.34,.22]):
        f.box(.25,9.31-i*.126,width,.08,.104,.069,TRIM,'three stepped plaster corbels')
    plaque(f,-.622,2.026,'181')
    plaque(f,1.708,1.865,'183')
    f.box(.015,1.35,.154,.236,.017,.019,BLUE,'small marker on common pier')
