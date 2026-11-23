"""Shallow original relief of the photographed herringbone panels and the west ground-floor grille."""
from math import ceil,floor,sqrt
from shapely.geometry import Polygon,box
from brick_finishes import HERRINGBONE,RED_BAND
from materials import BROWN,DARK,STONE

def herringbone_panel(f,panel,name):
    # A 40 mm by 160 mm visible face. Across and down-going rows share the same 45-degree setting-out lines.
    width=.040;scale=width/sqrt(2)
    def grid(x,z):return (x+z)/(width*sqrt(2)),(x-z)/(width*sqrt(2))
    coords=[grid(x,z) for x,z in panel.exterior.coords];us,vs=zip(*coords)
    for i in range(floor(min(us))-4,ceil(max(us))+1):
        for j in range(floor(min(vs))-4,ceil(max(vs))+1):
            phase=(i+j)%8
            if phase not in [0,4]:continue
            length,height=(4,1) if phase==0 else (1,4)
            corners=[(i,j),(i+length,j),(i+length,j+height),(i,j+height)]
            face=Polygon([((u+v)*scale,(u-v)*scale) for u,v in corners]).buffer(-.0019,join_style=2)
            part=panel.intersection(face)
            if part.area>1e-6:
                f.solid(part,.0137,.0168+((i+2*j)%5)*.0003,HERRINGBONE,name+' | diagonal fired-clay faces')

def window_jambs(f,hole,name):
    x0,z0,x1,z1=hole.bounds
    for a,b in [(x0-.095,x0),(x1,x1+.095)]:
        n=max(1,round((z1-z0)/.056))
        for j in range(n):
            lo=z0+(z1-z0)*j/n;hi=z0+(z1-z0)*(j+1)/n
            f.rect(a+.0024,b-.0024,lo+.0024,hi-.0024,.0195,.024,RED_BAND,name+' | jointed red jamb')
    a,b=x0-.095,x1+.095;n=max(1,round((b-a)/.043))
    for i in range(n):
        f.rect(a+(b-a)*i/n+.002,a+(b-a)*(i+1)/n-.002,z1+.002,z1+.13,.0194,.024,RED_BAND,name+' | soldiers over window')

def grille(f,x0,x1,z0,z1,lod,name):
    # The flat grille beside the most westerly ground sash is seen against its blind brick backing.
    for x in (x0,x1):f.rect(x-.015,x+.015,z0,z1,.073,.106,STONE,name+' | perimeter')
    for j in range(1,4):
        x=x0+(x1-x0)*j/4
        f.rect(x-.009,x+.009,z0,z1,.074,.095,STONE,name+' | vertical iron')
    for j in range(6):
        z=z0+(z1-z0)*j/5
        f.rect(x0-.015,x1+.015,z-.011,z+.011,.089,.109,STONE,name+' | horizontal iron')
    if not lod:
        for x in (x0,x1):
            for z in (z0+.14,z1-.11):f.rect(x-.016,x+.016,z-.023,z+.023,.012,.077,DARK,name+' | stand-off')
