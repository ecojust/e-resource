"""Photo-visible curved steel sash, sill, solid parapet and its left arched railing."""
from math import asin,sin,cos,pi

def pigment(rgb):
    return {'color':[v/3294.6 if v<=10 else ((v/255+.055)/1.055)**2.4 for v in rgb],'roughness':.76}
PALETTE={k:pigment(c) for k,c in {'dark steel':(54,57,50),'quiet glass':(143,152,143),'light glass':(164,171,155),'render':(192,180,159),'coping':(174,164,148),'railing iron':(85,83,71),'brick corbel':(130,103,87)}.items()}
R=2.36
def theta(u):
    # Perspective foreshortens the narrow leftmost sash. Only the photographed arc is included.
    return asin((u-437)/379)
def section(t,z,d=0):
    return ((R+d)*sin(t),R-(R+d)*cos(t),z)
def band(b,t0,t1,z0,z1,inner,outer,mat,name,steps=1):
    for j in range(steps):
        lo=t0+(t1-t0)*j/steps;hi=t0+(t1-t0)*(j+1)/steps
        v=[section(t,z,d)for z in (z0,z1) for d in(inner,outer) for t in(lo,hi)]
        b.add(v,[(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5)],mat,name)
def add_building(b,lod):
    limits=[100,119,164,218,301,379,461,530,558]
    angles=list(map(theta,limits));start,end=angles[0],angles[-1]
    seg=14 if not lod else 8
    for z0,z1,di,do,material,name in [(-.20,0,-.17,.035,'render','wall below sill'),(0,.10,-.17,.109,'coping','curved projecting sill'),(1.49,2.51,-.16,.022,'render','parapet face')]:
        band(b,start,end,z0,z1,di,do,material,name,seg)
    for j,(l,r) in enumerate(zip(angles,angles[1:])):
        for k,(z0,z1) in enumerate([(.12,.89),(.94,1.47)]):
            band(b,l,r,z0,z1,-.078,-.061,'light glass' if (j+2*k)%4==0 else 'quiet glass',f'bay {j+1} glazing {k+1}')
        for k,(z0,z1) in enumerate([(.091,.128),(.875,.951),(1.453,1.505)]):
            band(b,l,r,z0,z1,-.08,.004,'dark steel',f'bay {j+1} rail {k+1}')
    for j,t in enumerate(angles):
        band(b,max(start,t-.014),min(end,t+.014),.096,1.502,-.081,.014,'dark steel',f'mullion {j+1}')
    # The tree conceals the right return of the terrace. Railing follows the left end only.
    t0=theta(100);t1=theta(270);sides=8 if not lod else 5
    railpoints=lambda z:[section(t0+(t1-t0)*j/seg,z,-.025)for j in range(seg+1)]
    b.tube(railpoints(2.84),.023,'railing iron',sides,'terrace top rail')
    for i in range(4):
        l=t0+(t1-t0)*i/4;r=t0+(t1-t0)*(i+1)/4
        b.tube([section(l,2.5,-.025),section(l,2.84,-.025)],.013,'railing iron',sides,f'terrace post {i+1}')
        for k in range(2):
            steps=11 if not lod else 6
            pts=[section(l+(r-l)*j/steps,2.52+.28*sin((j/steps if k==0 else 1-j/steps)*pi/2),-.026)for j in range(steps+1)]
            b.tube(pts,.009,'railing iron',sides,f'terrace curved brace {i+1}.{k+1}')
    for i,u in enumerate([108,159]):
        t=theta(u);band(b,t-.065,t+.065,2.45,2.53,-.12,.10,'brick corbel',f'brick projecting cushion {i+1}',3)
