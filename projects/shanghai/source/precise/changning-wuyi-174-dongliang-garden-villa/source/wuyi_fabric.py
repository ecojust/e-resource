"""Architectural finishes, wall prisms and window sections shared by the Wuyi villa elevations."""
from pathlib import Path
import sys
from shapely.geometry import Polygon, box
from shapely import set_precision

SOURCE=Path(__file__).resolve().parent
PROJECT=next(p for p in SOURCE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'tools'))
import package_architectural_model as packaging
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-tanggu-road-apartment-dated-crown/source'))
from crown_builder import CrownBuilder

WALL='174 | cream roughcast'
STONE='174 | dressed pale stone'
SOFFIT='174 | light soffit'
TIMBER='174 | dark gable timber'
FRAME='174 | steel sash'
GLASS='174 | shaded window glass'
BRICK='174 | flushed red brick'
IRON='174 | cast iron'
FABRIC='174 | pale shop awning'
DOOR='174 | oak entrance door'
DARK='174 | interior reveal'
PAVING='174 | sandstone paving'

def paint(rgb,rough=.85,metal=0.):
    return {'color':[(v/255.)**2.2 for v in rgb],'roughness':rough,'metallic':metal}

PALETTE={WALL:{'color':[1,1,1],'roughness':.96,'texture':str(SOURCE/'wuyi-cream-roughcast.png')},
         STONE:paint((193,184,157)),SOFFIT:paint((223,221,204)),TIMBER:paint((78,60,54)),
         FRAME:paint((58,59,56),.53,.25),GLASS:paint((86,100,103),.21,.19),
         BRICK:paint((163,94,75)),IRON:paint((66,69,65),.55,.35),
         FABRIC:paint((232,230,212),.93),DOOR:paint((74,63,50)),DARK:paint((48,46,42)),PAVING:paint((169,166,149))}


def metric(u,v):
    """Front-wall chart anchored by the independently intersected 2.60 m window-axis spacing."""
    px_m=(297.25-181.25)/2.60
    return ((u-79.5)/px_m,(616.-v)/px_m)


def rect(left,top,right,bottom):
    x,z=metric(left,bottom);r,h=metric(right,top)
    return box(x,z,r,h)


def polygons(shape):
    cleaned=set_precision(shape,.00001).simplify(.000011,preserve_topology=True)
    return [p for p in getattr(cleaned,'geoms',[cleaned]) if p.geom_type=='Polygon' and p.area>1e-7]


def wall(b,shape,a,c,front,back,material,label):
    """Extrude x/z outlines along a facade from start to end, with positive depth inward."""
    from math import hypot
    dx,dy=c[0]-a[0],c[1]-a[1];length=hypot(dx,dy);dx,dy=dx/length,dy/length
    for poly in polygons(shape):
        b.prism(poly,-back,-front,lambda s,z,n:(a[0]+dx*s+dy*n,a[1]+dy*s-dx*n,z),material,label)


def face(b,shape,front,back,material,label):
    wall(b,shape,(0.,0.),(1.,0.),front,back,material,label)


def slab(b,shape,low,high,material,label):
    for polygon in polygons(shape):b.plan_prism(polygon,low,high,material,label)


def glazing(b,opening,a,c,depth,label,columns=2,rows=3):
    outer=opening; inner=outer.buffer(-.048,join_style=2)
    wall(b,outer.difference(inner),a,c,depth,depth+.088,FRAME,label+' perimeter')
    l,z0,r,z1=inner.bounds
    for i in range(columns):
        left=l+(r-l)*i/columns;right=l+(r-l)*(i+1)/columns
        if i:wall(b,box(left-.023,z0,left+.023,z1),a,c,depth+.016,depth+.075,FRAME,label+' meeting stile')
        for j in range(rows):
            lo=z0+(z1-z0)*j/rows;hi=z0+(z1-z0)*(j+1)/rows
            if j:wall(b,box(left+.023,lo-.014,right-.023,lo+.014),a,c,depth+.025,depth+.076,FRAME,label+' glazing bar')
            light=box(left+(.023 if i else 0),lo+(.014 if j else 0),right-(.023 if i<columns-1 else 0),hi-(.014 if j<rows-1 else 0))
            wall(b,light,a,c,depth+.077,depth+.092,GLASS,label+' glass')


def roughcast(out):
    from PIL import Image
    import numpy as np
    rng=np.random.default_rng(174018);s=320
    grain=rng.normal(0,5.7,(s,s));clumps=np.array(Image.fromarray(rng.integers(0,255,(64,64),dtype=np.uint8)).resize((s,s),Image.Resampling.BICUBIC),dtype=float)/255.
    relief=13*(clumps-.48)+grain-.34*np.roll(grain,1,axis=0)
    shadow=np.clip((clumps-.50)*-4,0,1)*rng.choice([0,0,0,5,9,14],size=(s,s))
    im=np.clip(np.array([213,208,184])+relief[:,:,None]-shadow[:,:,None],0,255).astype('uint8');Image.fromarray(im).save(out,optimize=True)
