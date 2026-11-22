"""Model the two street returns, open window recesses, balconies and cornices."""
from math import cos,sin,pi
from shapely.geometry import Polygon, box as rect
from shapely.ops import unary_union
from photo_architecture import opening
from bank_finishes import (WALL,LIMESTONE,DEEP,PALE,JOINT,OCHRE,IRON,GLASS,FRAME,RED,PLINTH)

def band(f,z,height,depth,mat,label):
    f.box(0,z,f.length+.008,height,depth+.035,(depth-.035)/2,mat,label)

def ledges(f,central=False):
    for z,h,d,mat in [(0.20,.4,.07,PLINTH),(4.47,.095,.095,DEEP),(4.54,.10,.145,PALE),
                      (5.26,.19,.13,WALL),(5.43,.12,.23,OCHRE),(5.55,.12,.28,PALE),
                      (9.23,.075,.12,DEEP),(9.32,.095,.21,OCHRE),(9.46,.16,.27,PALE),
                      (13.22,.11,.11,OCHRE),(13.36,.14,.25,DEEP),(13.47,.10,.35,OCHRE),(13.56,.11,.40,PALE)]:
        if central and 9<z<10:
            continue
        band(f,z,h,d,mat,'continuous-belt-'+str(z))
    count=max(4,round(f.length/.24))
    for j in range(count):
        u=(j+.5)*f.length/count-f.length/2
        f.box(u,13.28,.10,.11,.115,.135,PALE,'dentils under street cornice')

def pilaster(f,x,w,lod):
    f.box(x,2.47,w,4.05,.10,.045,WALL,'shop pier')
    f.box(x,.32,w+.12,.60,.20,.065,PLINTH,'pier foot')
    for z0,z1,step in [(0.67,4.28,.53),(5.67,13.15,.68)]:
        courses=max(1,round((z1-z0)/step));height=(z1-z0)/courses
        for i in range(courses):
            z=z0+i*height
            f.box(x,z+height/2,w,height-.022,.19,.072, LIMESTONE,'two-storey rusticated pilaster')
    f.box(x,12.98,w+.055,.13,.19,.105,OCHRE,'pilaster necking')
    f.box(x,13.13,w+.13,.17,.26,.095,PALE,'pilaster cap')
    f.box(x,4.75,w+.08,.30,.13,.07,WALL,'ground capital')
    if not lod:
        for e in (-1,1):
            f.box(x+e*(w/2-.035),9.45,.035,7.03,.052,.152,PALE,'pilaster arris')

def railing(f,u,z,width,lod):
    # The iron rail bows forward in the middle, its rods turn inward under the handrail.
    def d(t):return .36+.25*(1-t*t)
    def point(x,h,dep):return f.point(u+x,z+h,dep)
    count=10 if lod else 16
    ts=[-1+2*i/count for i in range(count+1)]
    for h,r in [(0.08,.034),(.81,.031),(.91,.041)]:
        f.builder.tube([point(t*width/2,h,d(t))for t in ts],r,IRON,6 if lod else 9,f.label+'/curved-balcony/continuous-rail')
    for e in (-1,1):
        for h in (.08,.91):
            f.line((u+e*width/2,z+h,.10),(u+e*width/2,z+h,d(1)),.031,IRON,6,'balcony side return')
    pieces=8 if lod else 14
    for i in range(pieces+1):
        t=-1+2*i/pieces
        rod=[point(t*width/2,h,d(t)+bulge) for h,bulge in [(0.08,0),(.20,.045),(.33,.086),(.50,.052),(.70,-.01),(.90,0)]]
        f.builder.tube(rod,.020 if lod else .017,IRON,5 if lod else 7,f.label+'/curved-balcony/bowed-uprights')
    if not lod:
        for i in range(7):
            t=-.88+i*.29;mid=u+t*width/2
            for mirror in (-1,1):
                curve=[]
                for j in range(13):
                    theta=.20+j*(1.72*pi/12);r=.10*(1-.56*j/12)
                    curve.append(f.point(mid+mirror*(.055+r*cos(theta)),z+.57+.13*sin(theta),d(t)+.026))
                f.builder.tube(curve,.013,IRON,6,f.label+'/curved-balcony/paired-scrolls')

def balcony(f,u,z,width,lod):
    f.box(u,z-.095,width,.19,.68,.30,PALE,'projecting balcony slab')
    f.box(u,z-.215,width-.075,.085,.58,.28,OCHRE,'balcony bed mould')
    for offset in (-.31,.31):
        x=u+offset*width
        # A stepped stone bracket under the slab is visible at oblique angles.
        for dz,ex,w in [(-.31,.46,.30),(-.44,.35,.27),(-.57,.20,.23)]:
            f.box(x,z+dz,w,.15,ex+.05,ex*.45,DEEP,'balcony corbel')
    railing(f,u,z,width-.07,lod)

def pediment(f,u,head,w,lod):
    arch=opening(u,head-.035,w,.92,.84,10 if lod else 24)
    inner=opening(u,head+.08,w-.29,.63,.58,10 if lod else 24)
    f.prism(arch,-.012,.07,LIMESTONE,'rounded tympanum')
    frame=arch.difference(inner)
    f.prism(frame,.071,.135,OCHRE,'moulded semicircular hood')
    tri=Polygon([(u-w*.62,head+.03),(u,head+1.29),(u+w*.62,head+.03)])
    cut=Polygon([(u-w*.54,head+.04),(u,head+1.10),(u+w*.54,head+.04)])
    f.prism(tri.difference(cut),.075,.215,PALE,'triangular outer pediment')
    f.line((u-w*.62,head+.06,.23),(u,head+1.31,.23),.052,OCHRE,6,'ochre raking edge')
    f.line((u,head+1.31,.23),(u+w*.62,head+.06,.23),.052,OCHRE,6,'ochre raking edge')

def closed_shop(f,shape):
    l,b,r,t=shape.bounds
    f.prism(shape.buffer(-.008),-.327,-.293,RED,'2021 enclosed street shop')
    for x in (l+.037,r-.037):
        f.box(x,(b+t)/2,.035,t-b,.037,-.270,FRAME,'enclosure edge')
    f.box((l+r)/2,b+.064,r-l,.10,.105,-.216,PLINTH,'bottom rail behind street jamb')
    f.box((l+r)/2,t-.076,r-l-.04,.115,.075,-.244,FRAME,'shop head rail')
    # The 2021 panels retain narrow borders around the red closure. No advertising text is inferred.
    for x in (l+.145,r-.145):
        f.box(x,(b+t)/2,.011,t-b-.33,.017,-.278,OCHRE,'fine border of red shop panel')
    for z in (b+.16,t-.16):
        f.box((l+r)/2,z,r-l-.28,.011,.017,-.278,OCHRE,'fine border of red shop panel')

def return_bay(f,u,lod):
    width=1.58
    shop=rect(u-1.02,.17,u+1.02,4.32)
    lower=rect(u-width/2,5.63,u+width/2,8.76)
    upper=rect(u-width/2,9.56,u+width/2,11.76)
    attic=rect(u-.57,13.94,u+.57,14.86)
    f.wall(0,15.43,[shop,lower,upper,attic],.42,WALL)
    ledges(f)
    closed_shop(f,shop)
    f.prism(shop.buffer(.085,join_style=2).difference(shop),0,.095,DEEP,'street doorway surround')
    f.box(u,.125,2.18,.24,.40,.02,PLINTH,'street sill')
    for shape,rows in [(lower,3),(upper,2),(attic,1)]:
        f.window(shape,2,rows,FRAME,False,GLASS,'deep French windows'if shape!=attic else'attic glazing')
        f.prism(shape.buffer(.09,join_style=2).difference(shape),0,.11,PALE,'incised window surround')
    f.box(u,8.90,1.85,.20,.19,.082,PALE,'square-headed lower window')
    f.box(u,9.10,1.96,.11,.23,.085,OCHRE,'lower window drip sill')
    for z in [5.62,9.54]:balcony(f,u,z,2.13,lod)
    pediment(f,u,11.83,1.84,lod)
    f.box(u,15.10,1.42,.09,.11,.047,OCHRE,'attic lintel')
    pilaster(f,-f.length/2+.18,.33,lod);pilaster(f,f.length/2-.18,.33,lod)
    band(f,15.46,.13,.16,PALE,'parapet coping')
