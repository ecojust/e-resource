"""The pierced stair elevation and the flight visible behind its inclined parapet."""
import json,math
from pathlib import Path
from shapely.geometry import Point,Polygon,box
from shapely.ops import unary_union
from loggia_materials import ROUGHCAST,LIME,CEMENT,BEAM,STEEL,GREEN,GLASS,TILE,SHADE

HERE=Path(__file__).resolve().parent
CONTROL=json.loads((HERE.parent/'measurements/loggia-arch-control.json').read_text())['model_parameters']
EAST=-4.58
WEST=4.98
FACADE_PROFILE=[(EAST,0),(WEST,0),(WEST,10.76),(0.38,13.49),(EAST,11.49)]
# The splayed front of the stair is the solid band between these two profiles.
LIP=[(-2.35,7.36),(-.075,7.36),(2.01,5.98),(2.84,5.98)]
SOFFIT=[(-2.29,6.67),(-.12,6.67),(1.92,5.25),(2.96,5.25)]


def arch_aperture(lod):
    cx,spring,rx,rise=(CONTROL[key] for key in ('centre_x','spring_z','radius_x','rise'))
    n=28 if lod else 72
    arc=[(cx+rx*math.cos(j*math.pi/n),spring+rise*math.sin(j*math.pi/n)) for j in range(n+1)]
    return Polygon([*LIP,(cx+rx,spring),*arc[1:]])


def framed_light(f,bounds,columns,rows,label,glass=GLASS):
    x0,z0,x1,z1=bounds;hole=box(*bounds);inner=hole.buffer(-.042,join_style=2)
    f.solid(hole,-.084,-.074,SHADE,label+' | shadow reveal')
    f.solid(hole.difference(inner),-.065,-.014,STEEL,label+' | perimeter')
    f.solid(inner,-.065,-.051,glass,label+' | glazing')
    for i in range(1,columns):
        x=x0+(x1-x0)*i/columns
        f.rect(x-.011,x+.011,z0+.04,z1-.04,-.054,-.017,STEEL,label+' | mullions')
    for i in range(1,rows):
        z=z0+(z1-z0)*i/rows
        f.rect(x0+.04,x1-.04,z-.010,z+.010,-.054,-.017,STEEL,label+' | bars')


def roof_vent(cx,z,w):
    # A square set on the diagonal, whose five dark cells can be read above the arch.
    return Polygon([(cx-w/2,z),(cx,z+w/2),(cx+w/2,z),(cx,z-w/2)])


def grille(f,cx,z,width,lod):
    hole=roof_vent(cx,z,width)
    f.solid(hole,-.159,-.14,SHADE,'Stair gable | depth behind ventilator')
    bars=[box(cx-.023,z-width,cx+.023,z+width),box(cx-width,z-.024,cx+width,z+.024)]
    if not lod:
        for u in [-.19,.19]:
            bars.append(box(cx+u*width-.011,z-width,cx+u*width+.011,z+width))
    f.solid(unary_union(bars).intersection(hole.buffer(-.026)), -.04,-.008,STEEL,'Stair gable | iron grille')
    f.solid(hole.difference(hole.buffer(-.049)), -.067,.003,LIME,'Stair gable | ventilator jamb')


def main_stair(f,lod):
    # The long parapet obscures the feet on the upper run. The landing heights
    # and outer nosing follow the image; individual riser heights are inferred.
    left,right=-.12,1.94;low,high=5.29,6.70
    n=9;step=(right-left)/n;rise=(high-low)/n
    profile=[(left,high)]
    for i in range(n):
        a=left+i*step;top=high-i*rise
        profile.extend([(a+step,top),(a+step,top-rise)])
        if not lod:
            f.b.box((a+step-.003,.83,top-.016),(.028,1.285,.031),LIME,
                    label='Upper flight | tread nosing')
    profile.extend([(right,low-.22),(left,high-.22)])
    f.solid(Polygon(profile),-1.53,-.18,CEMENT,'Upper flight | treads, risers and continuous soffit')
    for x0,x1,z,name in [(-2.34,left,high,'upper landing'),(right,3.0,low,'lower landing')]:
        f.b.box(((x0+x1)/2,1.01,z-.062),(x1-x0,1.68,.124),CEMENT,label='Open stair | '+name)
    # Thin iron guard over the plaster cheek, with two levels visible across the upper arch.
    path=[(x,z)for x,z in LIP];depth=.10
    for rail_h in [.42,.94]:
        f.rail([(x,depth,z+rail_h)for x,z in path],.021,STEEL,'Upper flight | tubular handrail',6 if lod else 12)
    for i in range(1,7):
        x=-2.32+i*.735
        t=min(1,max(0,(x+.075)/2.085));z=7.36-1.38*t
        f.rail([(x,depth,z-.025),(x,depth,z+.94)],.014,STEEL,'Upper flight | railing post',6 if lod else 10)
    # Through the lower aperture a second diagonal balustrade is visible behind the front run.
    for dz in [.0,.62]:
        f.rail([(-1.83,.70,3.24+dz),(.53,1.30,4.98+dz)],.020,STEEL,'Lower landing | diagonal railing',6 if lod else 10)
    for i in (0,1,2,3):
        t=i/3;f.rail([(-1.83+2.36*t,.7+.60*t,3.16+1.74*t),(-1.83+2.36*t,.7+.60*t,3.86+1.74*t)],
                      .013,STEEL,'Lower landing | railing posts',6)


def add_loggia(f,lod=False):
    front=Polygon(FACADE_PROFILE);arch=arch_aperture(lod)
    mid=Polygon([(-2.29,2.80),(2.96,2.82),*reversed(SOFFIT)])
    little=box(-3.48,9.44,-2.77,10.36)
    # The ground-floor opening is partly screened by gate and shrubs.
    low=box(-3.52,.15,-2.71,2.07)
    vents=[roof_vent(.30,12.04,.62),roof_vent(-.33,12.01,.30),roof_vent(.93,12.04,.30)]
    visible=front.difference(unary_union([arch,mid,little,low,*vents]))
    f.solid(visible,-.33,0,ROUGHCAST,'Central gable | roughcast street wall with open stair apertures')
    framed_light(f,little.bounds,1,2,'Loggia | small high light')
    framed_light(f,low.bounds,2,3,'Loggia | visible ground floor side light')
    for v in vents:
        (x,z)=v.centroid.coords[0];grille(f,x,z,v.bounds[2]-v.bounds[0],lod)
    main_stair(f,lod)
    back=f.face(0,2.26,1,0)
    # Recesses and doors visible in the photograph terminate the local stair model.
    upper_door=box(-1.90,6.73,-.63,10.03);upper_light=box(-.42,7.03,2.25,10.41)
    lower_door=box(-1.92,2.92,-.74,5.15)
    rear=box(-2.94,.01,3.33,11.22).difference(unary_union([upper_door,upper_light,lower_door]))
    back.solid(rear,-.15,0,BEAM,'Stair hall | back wall behind landings')
    for door,name in [(upper_door,'upper'),(lower_door,'lower')]:
        x0,z0,x1,z1=door.bounds;back.solid(door,-.083,-.050,GREEN,'Stair hall | '+name+' painted door')
        framed_light(back,(x0+.10,z1-.75,x1-.10,z1-.09),2,2,'Stair hall | '+name+' door light')
    framed_light(back,upper_light.bounds,4,3,'Stair hall | sheltered upper glazing')
    for x,sign in [(-2.37,1),(2.95,-1)]:
        side=f.face(x,0,0,sign);limits=(0,2.26) if sign==1 else (-2.26,0)
        side.rect(*limits,2.80,11.22,-.10,0,LIME,'Stair hall | side reveal')
    f.b.box((.25,1.33,11.22),(5.93,2.02,.12),BEAM,label='Stair hall | ceiling inside the high arch')
    f.rail([(-2.54,-.10,.16),(-2.54,-.10,6.15),(-2.54,-.10,10.86),
            (-2.64,-.15,11.09)],.048,STEEL,'Stair gable | rainwater pipe',8 if lod else 12)
    for z in (3.15,6.05,8.76):
        f.rail([(-2.54,-.098,z-.049),(-2.54,-.098,z+.045)],.059,STEEL,'Stair gable | pipe collar',8)
    for a,b in [(FACADE_PROFILE[2],FACADE_PROFILE[3]),(FACADE_PROFILE[3],FACADE_PROFILE[4])]:
        f.band([a,b],.098,-.25,.040,TILE,'Central gable | raised clay verge')
