"""Semicircular terrace of the former Shanghai Animation Film Studio's administrative villa.

Coordinates are local; the published photograph fixes the visible profile and the rail motifs.
"""
import math
from pathlib import Path
import numpy as np
from PIL import Image
from shapely.geometry import Polygon,box
ID='jingan-animation-studio-white-villa-terrace'
STONE='Ivory terrace finish';RIM='Chalk-white slab nose';WALK='Buff paving';COLUMN='Dark circular support';RAIL='Dark handrail';ART='Geometric balustrade';WALL='Recessed white wall'
PALETTE={k:dict(color=c,roughness=r,metallic=m)for k,c,r,m in [(STONE,[1,1,1],.92,0),(RIM,[.79,.76,.65],.91,0),(WALK,[.58,.47,.342],.89,0),(COLUMN,[.093,.084,.074],.68,.13),(RAIL,[.068,.066,.061],.56,.42),(ART,[.078,.075,.069],.61,.39),(WALL,[.78,.76,.68],.95,0)]}
RADIUS=2.55;REACH=1.59
def texture():
    p=Path(__file__).with_name('ivory-render.png')
    if not p.exists():
        g=np.random.default_rng(631);yy,xx=np.indices((174,512));m=2.2*np.sin(xx*.032+np.cos(yy*.05))+g.normal(0,2.9,(174,512))+1.6*np.sin(yy*.032)
        Image.fromarray(np.clip(np.array([199,194,175])+m[:,:,None],0,255).astype('uint8')).save(p)
    PALETTE[STONE]['texture']=str(p)
def loc(a,h,r=1):
    return RADIUS*r*math.sin(a), -REACH*r*math.cos(a),h
def deck(r,steps):
    pts=[loc(a,0,r)[:2]for a in np.linspace(-math.pi/2,math.pi/2,steps)]
    return Polygon(pts+[(RADIUS*r,.35),(-RADIUS*r,.35)])
def add_building(b,far=False):
    texture();n=33 if far else 81
    def xyz(x,y,z):return x,y,z
    def plate(p,z0,z1,mat,label):b.prism(p,z0,z1,xyz,mat,label)
    plate(deck(.965,n),-.09,0.015,WALK,'Paved curved floor beneath portico')
    plate(deck(.93,n),2.65,3.16,STONE,'Deep inner curved plaster fascia')
    plate(deck(1,n),3.125,3.365,RIM,'Projecting white rounded outer slab')
    plate(deck(.986,n),3.363,3.386,WALK,'Walking surface inside outer lip')
    plate(box(-2.56,.348,2.56,.49),0,3.13,WALL,'Rear wall bounding the sheltered space')
    for a in (-1.22,-.41,.41,1.22):
        b.tube([loc(a,.01,.914),loc(a,2.731,.914)],.077,COLUMN,sides=12 if far else 28,label='Four independent circular columns')
    def curve(points,thick,mat,label):
        # Points are azimuth/elevation, linear fittings follow the curved terrace in plan.
        guard_radius=.898 if mat==ART else .923
        vertices=[]
        for (a,z),(bb,zz) in zip(points,points[1:]):
            divisions=max(1,math.ceil(abs(bb-a)/(.15 if far else .044)))
            for t in np.arange(divisions)/divisions:vertices.append(loc(a+t*(bb-a),z+t*(zz-z),guard_radius))
        vertices.append(loc(*points[-1],guard_radius));b.tube(vertices,thick,mat,sides=5 if far else 10,label=label)
    for z,r in [(4.204,.024),(4.069,.017),(3.943,.016),(3.808,.016)]:
        curve([(-1.57,z),(1.57,z)],r,RAIL,'Four parallel curved guard rails')
    for a in (-1.55,-.94,-.52,-.12,.27,.70,1.18,1.55):
        curve([(a,3.378),(a,4.199)],.015,RAIL,'Balustrade standard')
    curve([(-.57,3.67),(-.43,3.435),(-.29,3.66),(-.13,3.45),(.015,3.69),(.16,3.465),(.31,3.69),(.46,3.49)],.017,ART,'Central folded zigzag in the lower guard')
    for sign in (-1,1):
        def mirror(points):return[(a*sign,z)for a,z in points]
        for a0,z0 in((.51,3.525),(.59,3.62)):
            curve(mirror([(a0,3.39),(a0,z0),(.77,z0),(.817,z0+.011),(.85,z0+.046),(.865,z0+.093)]),.015,ART,'Nested square elbow with rounded tip')
        for a0,z0 in((.58,3.995),(.65,4.055)):
            curve(mirror([(a0,4.075),(a0+.011,z0),(.68,z0),(.712,z0-.069),(.754,z0-.107),(.83,z0-.124),(.977,z0-.124)]),.014,ART,'Paired inset curved upper corner')
    for p in b.parts:
        if p['material']==STONE:p['texcoords']=[[(x+RADIUS)/(2*RADIUS),(z-2.65)/.51]for x,y,z in p['vertices']]
