"""Façade fragment at Tongji Village No. 347 based on Fayhoo's 2015 exterior photograph."""
from pathlib import Path
import math
from random import Random

from PIL import Image
from shapely.affinity import translate
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

WALL = 'Chalk-coloured roughcast'
LATTICE = 'Grey cast cement lattice'
FRAME = 'Warm olive painted sash'
GLASS = 'Muted blue green glass'
DARK = 'Unlit window recess'
HOLD = 'Stone band above and below the window'
TILE = 'Terracotta tile'
EAVES = 'Dark rounded eaves edge'
PALETTE = {k: dict(color=colour, roughness=rough) for k, colour, rough in [
    (WALL,[1,1,1],.93),(LATTICE,[.57,.55,.50],.89),(FRAME,[.68,.63,.40],.67),
    (GLASS,[.27,.34,.35],.29),(DARK,[.085,.095,.093],.97),(HOLD,[.65,.61,.51],.91),
    (TILE,[.50,.26,.15],.88),(EAVES,[.29,.28,.25],.92)]}

def texture(path):
    if path.is_file() and path.stat().st_size:return
    rng=Random(347)
    im=Image.new('RGB',(128,128))
    im.putdata([tuple(c+d for c in (216,212,195)) for d in [round(rng.uniform(-7,7)+1.5*math.cos(i/26)+math.sin(i//128/9)) for i in range(128**2)]])
    im.save(path)

def screen(lod):
    # Four continuous corner webs connect the nested rectangular frame to the outer casing.
    frame=box(-.35,-.42,.35,.42).difference(box(-.314,-.382,.314,.382))
    middle=box(-.233,-.293,.233,.293).difference(box(-.199,-.257,.199,.257))
    center=box(-.158,-.185,.158,.185).difference(box(-.127,-.153,.127,.153))
    corners=[LineString([(sx*.33,sy*.39),(sx*.275,sy*.305),(sx*.220,sy*.273)]).buffer(.024,cap_style=2,join_style=2)
             for sx in (-1,1) for sy in (-1,1)]
    supports=[box(-.215,-.019,.215,.019),box(-.019,-.269,.019,.269)]
    petals=[]
    for sx,sz in ((0,1),(1,0),(0,-1),(-1,0)):
        shape=Point(sx*.044,sz*.044).buffer(.087,quad_segs=3 if lod else 7)
        petals.append(shape.boundary.buffer(.010,quad_segs=2))
    return unary_union([frame,middle,center,*supports,*corners,*petals])

def add_building(b,lod):
    def panel(poly,front,back,mat,label):
        b.prism(poly,back,front,lambda x,z,d:(x,-d,z),mat,label)
    side_x=1.205
    vents=[(sx*side_x,z)for sx in (-1.,1.)for z in (.76,2.66)]
    flat=box(-1.78,-.16,1.78,3.52).difference(box(-.716,-.18,.716,3.53))
    for x,z in vents:
        flat=flat.difference(box(x-.35,z-.42,x+.35,z+.42))
    panel(flat,0,-.245,WALL,'Side wall with four open lattice reveals')
    projected=box(-.717,-.16,.717,3.49)
    aperture=box(-.465,.46,.465,2.62)
    panel(projected.difference(aperture),.158,-.245,WALL,'Shallow projecting strip around the high window')
    for idx,(x,z) in enumerate(vents):
        prefix=('Left' if x<0 else 'Right')+(' lower' if z<1 else ' upper')
        face=translate(screen(lod),xoff=x,yoff=z)
        panel(face,-.027,-.098,LATTICE,prefix+' recessed open cement grille')
        if not lod:
            casing=box(x-.377,z-.449,x+.377,z+.449).difference(box(x-.351,z-.421,x+.351,z+.421))
            panel(casing,.009,-.008,WALL,prefix+' narrow plaster arris')
    # A whole fixed perimeter encloses the central band and the two narrow sidelights.
    inset=box(-.419,.509,.419,2.569)
    panel(aperture.difference(inset),.137,.061,FRAME,'Perimeter of painted tall window')
    for x in (-.28,.28):
        panel(box(x-.022,.49,x+.022,2.6),.122,.05,FRAME,'Continuous meeting stile beside the narrow sidelights')
    levels=[.508,.818,1.395,1.708,2.271,2.57]
    for z in levels[1:-1]:
        panel(box(-.431,z-.020,.431,z+.020),.121,.041,FRAME,'Continuous horizontal rail across the high window')
    for i,(low,high) in enumerate(zip(levels,levels[1:])):
        for left,right in ((-.419,-.303),(.303,.419)):
            panel(box(left,low+.009,right,high-.009),.054,.040,GLASS,'Fixed narrow sidelight')
        if i not in (1,3):
            panel(box(-.258,low+.012,.258,high-.012),.060,.045,GLASS,'Fixed light in the central sash')
            continue
        # The photograph shows different pitch on the two real projecting awnings.
        theta=math.radians(30 if i==1 else 42)
        c,s=math.cos(theta),math.sin(theta)
        h=high-low-.045;wid=.508
        leaf=box(-wid/2,-h,wid/2,0)
        light=box(-wid/2+.025,-h+.034,wid/2-.025,-.027)
        def hinged(x,z,d):
            return (x,-(.131-z*s+d*c),high-.023+z*c+d*s)
        b.prism(leaf.difference(light),-.019,.015,hinged,FRAME,'Outward hinged painted sash')
        b.prism(light,-.012,-.005,hinged,GLASS,'Glass tilted out with its sash')
        panel(box(-.262,low+.009,.262,high-.009),-.165,-.176,DARK,'Shallow dark recess behind open sash')
    # The two horizontal cast strips are incised through a thin front skin onto a deep reveal.
    for z in (.29,2.78):
        strip=box(-.476,z-.12,.476,z+.12)
        cuts=[]
        for idx,x in enumerate((-.36,-.21,-.075,.075,.21,.36)):
            cuts.append(translate(box(-.035,-.041,.035,.041).difference(box(-.017,-.020,.017,.020)),xoff=x,yoff=z))
        panel(strip,.161,.157,HOLD,'Cast band with small recessed geometric marks')
        panel(strip.difference(unary_union(cuts)),.178,.163,HOLD,'Raised face of the patterned band')
    # A short tile hood belongs to this projecting window bay, below the main gable.
    roof=Polygon([(-.04,3.49),(.258,3.38),(.258,3.417),(-.04,3.527)])
    b.prism(roof,-.80,.80,lambda d,z,x:(-x,-d,z),TILE,'Red tile hood over the projecting window bay')
    fascia=box(.222,3.353,.264,3.402)
    b.prism(fascia,-.81,.81,lambda d,z,x:(-x,-d,z),EAVES,'Dark eaves roll below red tiles')
    for i in range(9):
        a=-.755+i*.189
        b.prism(roof,a,a+.023,lambda d,z,x:(-x,-d,z+.013),TILE,'Individual upstand in the short clay-tile hood')
    b.palette[WALL]['texture']=str(Path(__file__).with_name('plaster.png'))
    for part in b.parts:
        if part['material']==WALL:part['texcoords']=[[(x+1.82+.03*y)/3.65,(z+.19)/3.76]for x,y,z in part['vertices']]
