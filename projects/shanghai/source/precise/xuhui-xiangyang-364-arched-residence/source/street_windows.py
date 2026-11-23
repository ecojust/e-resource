"""Street-facing steel casements and the three floral grilles below the middle pair."""
from math import cos, sin, pi
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from materials import CEMENT, DARK, DENTIL, FRAME, GLASS, GRILLE, SHADOW

def rounded_light(u, bottom=3.90, spring=5.51, rise=.46, radius=.49, steps=32):
    arc=[(u+radius*cos(i*pi/steps),spring+rise*sin(i*pi/steps)) for i in range(steps+1)]
    return Polygon([(u-radius,bottom),(u+radius,bottom),*arc])

def sash(f,shape,rows,columns,label,head=None,trim=True):
    x0,z0,x1,z1=shape.bounds
    if trim:
        rim=shape.buffer(.093,join_style=2).difference(shape)
        f.solid(rim,.001,.052,CEMENT,label+' | rendered architrave')
    clear=shape.buffer(-.039,join_style=2)
    f.solid(shape.difference(clear),-.205,-.002,SHADOW,label+' | deep jamb')
    f.solid(clear,-.223,-.204,GLASS,label+' | recessed glazing')
    frame=clear.difference(clear.buffer(-.036,join_style=2))
    lights=clear.buffer(-.026,join_style=2)
    for x in columns:
        frame=frame.union(box(x-.017,z0,x+.017,head or z1).intersection(lights))
    for z in rows:
        frame=frame.union(box(x0,z-.017,x1,z+.017).intersection(lights))
    if head:
        u=(x0+x1)/2
        for angle in (pi/4,pi/2,3*pi/4):
            end=(u+.8*cos(angle),head+.8*sin(angle))
            frame=frame.union(LineString([(u,head),end]).buffer(.014,cap_style=2).intersection(lights))
    f.solid(frame,-.203,-.158,FRAME,label+' | opening steel casements')
    if trim:
        f.rect(x0-.105,x1+.105,z0-.10,z0-.032,.004,.101,CEMENT,label+' | projecting sill')

def photo_lights(lod):
    steps=16 if lod else 34
    return [
        ('south fanlight',rounded_light(-4.20,steps=steps),[4.53,5.16,5.51],[-4.20],5.51),
        ('central wide steel window',box(-.90,3.90,.81,6.18),[4.46,5.03,5.62],[-.47,-.045,.38],None),
        ('north fanlight',rounded_light(4.61,steps=steps),[4.53,5.16,5.51],[4.61],5.51),
        ('south upper steel window',box(-4.72,7.75,-3.68,9.60),[8.36,8.97],[-4.20],None),
        ('north upper steel window',box(4.09,7.75,5.13,9.60),[8.36,8.97],[4.61],None),
        ('central upper south light',box(-.87,7.75,-.21,9.60),[8.34,8.96],[-.54],None),
        ('central upper north light',box(.11,7.75,.77,9.60),[8.34,8.96],[.44],None)]

def floral_apron(f,lod):
    x0,x1=-1.03,.94
    top,base=7.66,6.92
    panel=box(x0,base,x1,top)
    # Each small ogee on the lower edge is a cut through the projecting panel.
    for i in range(4):
        x=x0+(i+.5)*(x1-x0)/4
        scallop=Point(x,base-.08).buffer(.205,resolution=6 if lod else 14)
        panel=panel.difference(scallop)
    centers=[(-.69,7.32),(-.045,7.32),(.60,7.32)]
    def octagon(x,z,r):
        return Polygon([(x+r*cos((i+.5)*pi/4),z+r*sin((i+.5)*pi/4)) for i in range(8)])
    apertures=[octagon(x,z,.205) for x,z in centers]
    f.solid(panel.difference(unary_union(apertures)),.003,.125,CEMENT,'paired window | scalloped apron')
    for (x,z),aperture in zip(centers,apertures):
        f.solid(aperture,.004,.045,DARK,'apron | octagonal recess')
        rim=aperture.difference(octagon(x,z,.173))
        rose=Point(x,z).buffer(.033,resolution=8)
        for i in range(4):
            a=pi/4+i*pi/2
            px=x+.088*cos(a);pz=z+.088*sin(a)
            petal=Point(px,pz).buffer(.058,resolution=6 if lod else 12)
            rose=rose.union(petal.difference(petal.buffer(-.023)))
            rose=rose.union(LineString([(x,z),(px,pz)]).buffer(.012,cap_style=2))
        f.solid(rim,.046,.129,GRILLE,'apron | octagonal frame')
        f.solid(rose,.046,.098,GRILLE,'apron | four-petal grille')
    f.rect(x0-.045,x1+.045,7.65,7.74,.020,.20,FRAME,'paired window | dark sill lip')
    for i in range(9):
        x=x0+.085+i*.226
        f.rect(x,x+.064,7.58,7.65,.12,.164,DENTIL,'paired window | sill teeth')
