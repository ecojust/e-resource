"""The twin upper lights and short three-face bay of the No. 51 mill residence."""
from pathlib import Path
import math
from random import Random
from PIL import Image
from shapely.geometry import Polygon, box

WALL='Ochre dash render'
TRIM='Weathered cream timber'
RIB='Pale timber glazing bar'
GLASS='Slate blue glass'
DARK='Dark glazing rebate'
STONE='Weathered grey window stool'
EDGE='Brown grey fascia boarding'
SOFFIT='Shadow below roof projection'
TILE='Dark fired roof tile'
TILE_LIGHT='Weathered raised tile edge'
BASE='Shaded cut below upper bay'
PALETTE={key:dict(color=c,roughness=r) for key,c,r in [
    (WALL,[1.,1.,1.],.96),(TRIM,[.83,.78,.66],.78),(RIB,[.83,.81,.71],.73),
    (GLASS,[.26,.33,.37],.31),(DARK,[.16,.18,.17],.91),(STONE,[.47,.45,.38],.91),
    (EDGE,[.39,.31,.26],.91),(SOFFIT,[.235,.212,.19],.95),
    (TILE,[.258,.255,.256],.87),(TILE_LIGHT,[.33,.32,.30],.88),(BASE,[.45,.41,.33],.94)]}

def texture(path):
    if path.exists():return
    rng=Random(431)
    img=Image.new('RGB',(240,210))
    pixels=[]
    for y in range(img.height):
        for x in range(img.width):
            mote=rng.uniform(-11,11)+3.8*math.sin(x/24+y/32)+3.2*math.sin(x/9-y/47)
            stain=max(0,math.sin(x/51+1.4*math.sin(y/45)))**5 * (4.6+7*y/img.height)
            delta=int(mote-stain)
            pixels.append((178+delta,149+delta,97+delta))
    img.putdata(pixels);img.save(path,optimize=True)

def arch(x,z,r,shoulder,n):
    return Polygon([(x-r,z),(x+r,z)]+[(x+r*math.cos(i*math.pi/n),shoulder+r*math.sin(i*math.pi/n))for i in range(n+1)])

def add_building(b,lod):
    def wall(poly,a,d,material,label):
        b.prism(poly,a,d,lambda x,z,u:(x,-u,z),material,label)
    # Survey proportions from the near frontal photograph. Unit scale is estimated.
    verge=[(-3.52,2.28),(-1.01,4.62),(-.69,4.81),(-.22,4.89),(.18,4.89),(.71,4.80),(1.01,4.63),(3.52,2.28)]
    clipped=[(-3.24,2.20),*verge[1:-1],(3.24,2.20)]
    xs=[-.378,.378];n=14 if lod else 26;radius=.236;sill=3.14;spring=3.54
    outer=Polygon([(-3.24,2.02),(3.24,2.02),*reversed(clipped)])
    holes=[arch(x,sill,radius,spring,n)for x in xs]
    for opening in holes:outer=outer.difference(opening)
    wall(outer,-.38,0,WALL,'Roughcast gable with twin arched apertures')
    for i,(x,opening)in enumerate(zip(xs,holes)):
        side=['Left','Right'][i]
        inside=arch(x,sill+.037,radius-.037,spring,n)
        wall(opening,-.13,-.118,DARK,side+' dark inset reveal')
        wall(opening.difference(inside),-.114,-.031,TRIM,side+' arched head and jamb lining')
        wall(inside,-.110,-.103,GLASS,side+' arch-head glazing')
        for off in (-.075,.075):
            wall(box(x+off-.009,sill+.025,x+off+.009,spring+radius).intersection(inside),-.102,-.077,RIB,side+' narrow upper mullion')
        wall(box(x-radius+.023,spring-.048,x+radius-.023,spring-.027).intersection(inside),-.102,-.076,RIB,side+' arch spring rail')
        wall(box(x-radius-.054,sill-.072,x+radius+.054,sill-.007),-.01,.095,STONE,side+' projecting sill')
    def strip(points,below,above):
        return Polygon([(x,z+below)for x,z in points]+[(x,z+above)for x,z in reversed(points)])
    for i in range(len(verge)-1):
        v=verge[i:i+2]
        wall(strip(v,-.095,.014),-1.04,.035,TILE,'Short roof return behind gable')
        wall(strip(v,-.199,-.094),-.75,.142,SOFFIT,'Deep shadow under overhanging gable')
        wall(strip(v,-.117,.043),-.026,.172,EDGE,'Broad painted fascia following both pitches')
        wall(strip(v,.044,.075),-.67,.20,TILE_LIGHT,'Upper rolled weathering edge')
        x0,z0=v[0];x1,z1=v[1]
        intervals=max(1,round(math.hypot(x1-x0,z1-z0)/.24))
        for j in range(intervals):
            t=(j+.44)/intervals;u=(j+.78)/intervals
            l=(x0+(x1-x0)*t,z0+(z1-z0)*t);r=(x0+(x1-x0)*u,z0+(z1-z0)*u)
            wall(strip([l,r],.076,.093),-.67,.17,TILE,'Visible individual lip along tiles')
    # The shadow at the base of the gable is a shallow bow. It spans the faceted bay below.
    underside=[(x,2.095+.19*math.cos(x/3.24*math.pi/2))for x in [-3.24,-2.60,-1.80,-.90,0,.90,1.80,2.60,3.24]]
    wall(strip(underside,-.095,.017),.002,.155,SOFFIT,'Shallow bowed shadow at the upper window head')
    bay=[(-2.22,-.035),(-.75,-.48),(.75,-.48),(2.22,-.035)]
    def panel(poly,mat,label,a,d,start,end):
        x0,y0=start;x1,y1=end;length=math.hypot(x1-x0,y1-y0);cx=(x0+x1)/2;cy=(y0+y1)/2;ux=(x1-x0)/length;uy=(y1-y0)/length
        b.prism(poly,a,d,lambda x,z,u:(cx+x*ux+u*uy,cy+x*uy-u*ux,z),mat,label)
    for j in range(3):
        a,c=bay[j:j+2];span=math.dist(a,c);left=-.47;right=.47;bottom=.14;head=1.93;transom=1.39;name=['Left splayed','Centre','Right splayed'][j]
        def front(poly,mat,label,back,forward):panel(poly,mat,name+' '+label,back,forward,a,c)
        frame=box(left,bottom,right,head)
        front(box(-span/2,-.17,span/2,2.075).difference(frame),WALL,'ochre window wall',-.26,0)
        front(frame,DARK,'sash rebate',-.153,-.128)
        inset=box(left+.058,bottom+.053,right-.058,head-.060)
        front(frame.difference(inset),TRIM,'timber sash perimeter',-.11,-.023)
        front(inset,GLASS,'blue-grey glazing',-.112,-.099)
        front(box(-.021,bottom+.046,.021,head-.044),TRIM,'meeting rail and centre divider',-.097,-.055)
        front(box(left+.05,transom-.03,right-.05,transom+.03),TRIM,'transom with paired upper lights',-.105,-.035)
        for z in (.49,.84,1.16):
            front(box(left+.058,z-.009,right-.058,z+.009),RIB,'slender casement glazing rail',-.091,-.065)
        front(box(left-.058,bottom-.090,right+.058,bottom-.016),STONE,'projecting sill',-.025,.105)
        if not lod:
            front(box(left+.057,bottom+.053,right-.057,head-.059).difference(box(left+.072,bottom+.068,right-.072,head-.074)),DARK,'narrow glazing gasket',-.098,-.081)
    # Plain side margins connect the upper gable and the clipped bay.
    for side in [-1,1]:
        a,c=sorted([side*2.14,side*3.24]);wall(box(a,-.17,c,2.055),-.27,-.01,WALL,'Outer plaster margin beside bay')
    b.palette[WALL]['texture']=str(Path(__file__).with_name('ochre-render.png'))
    for part in b.parts:
        if part['material']==WALL:part['texcoords']=[[(x+3.55+.24*y)/7.20,(z+.23)/5.36] for x,y,z in part['vertices']]
