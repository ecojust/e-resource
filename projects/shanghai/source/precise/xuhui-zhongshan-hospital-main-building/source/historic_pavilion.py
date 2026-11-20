"""Central hospital block from the 1936 front and dated 2019 reverse oblique."""
import math

import numpy as np
from shapely.geometry import box
from photo_architecture import Facade

STONE='light cast stone'; BRICK='weathered red brick'; SILVER='pale horizontal band'
WINDOW='dark blue grey glazing'; FRAME='dark painted casement'; DOOR='dark bronze door'
TILE='warm glazed yellow tile'; RIDGE='amber glazed crests'; VERMILION='red gable and dormers'
SOFFIT='brown rafter tails'; FLOOR='terrace paving'
def material(rgb,rough=.75,metal=0):
    return {'color':rgb,'roughness':rough,'metallic':metal}
PALETTE={STONE:material([.74,.72,.67]), BRICK:material([.57,.335,.275]), SILVER:material([.83,.81,.74]),
         WINDOW:material([.13,.20,.20],.28,.13), FRAME:material([.15,.16,.14],.54,.17), DOOR:material([.22,.19,.16],.58),
         TILE:material([.83,.565,.19],.47), RIDGE:material([.69,.415,.103],.41), VERMILION:material([.61,.215,.145]),
         SOFFIT:material([.38,.252,.157]), FLOOR:material([.54,.53,.46])}

HALF=26.5; DEPTH=8.75; TERRACE=15.6; EAVES=20.3
ROOF_X=28.15; ROOF_Y=9.92; RIDGE_X=24.15; RISE=4.85

def decorated_window(f,u,z,w,h,lod,door=False):
    aperture=box(u-w/2,z,u+w/2,z+h)
    f.window(aperture,2,1 if lod else (3 if door else 2),FRAME,False,DOOR if door else WINDOW,'entrance doors' if door else 'casements')
    return aperture

def ward_elevation(b,north,lod):
    direction=1 if north else -1
    y=direction*DEPTH
    f=Facade(b,(direction*HALF,y),(-direction*HALF,y),'North forecourt/ward facade' if north else 'South court/ward facade')
    pier_centers=[-23.64,23.64];span=40.5;spacing=2.13
    for level in range(4):
        floor=level*3.87; openings=[]
        for bay in range(-9,10):
            u=bay*spacing
            if north and level==0 and abs(bay)<=1:
                if bay==0: openings.append(decorated_window(f,0,.18,5.29,3.13,lod,True))
            else:openings.append(decorated_window(f,u,floor+.74,1.24,2.36,lod))
        for u in pier_centers:openings.append(decorated_window(f,u,floor+.90,1.03,2.10,lod))
        f.wall(floor,floor+3.87,openings,.43,STONE)
        for index in range(-9,9):
            u=(index+.5)*spacing
            if not north or level>0 or abs(u)>3.5:
                f.box(u,floor+1.91,.66,2.41,.07,.017,BRICK,'brick window spandrels')
        for u in pier_centers:
            for offset in [-1.75,1.75]:f.box(u+offset,floor+1.91,.28,3.83,.19,.05,SILVER,'flanking masonry piers')
        f.box(0,floor+3.66,span+.52,.29,.14,.07,SILVER,'horizontal cast-stone bands')
    f.beam(TERRACE-.13,.28,.30,SILVER,label='terrace edge')
    if north:
        for u in [-3.45,3.45]:f.box(u,1.88,.66,3.76,.52,.12,STONE,'central entrance piers')
        f.box(0,3.55,8.65,.40,1.24,.39,SILVER,'central entrance canopy')
    return f

def railing(f,w,lod):
    z=TERRACE+.16
    f.box(0,z+.11,w,.22,.39,.13,SILVER,'balustrade plinth')
    f.box(0,z+.92,w,.14,.24,.15,SILVER,'balustrade rail')
    n=max(2,round(w/2.4))
    for i in range(n+1):
        u=(i/n-.5)*(w-.25)
        f.box(u,z+.54,.24,1.06,.29,.13,STONE,'balustrade posts')
        f.box(u,z+1.13,.30,.14,.34,.13,SILVER,'balustrade pier caps')
    if not lod:
        for i in range(n):
            for j in (1,2,3):
                u=((i+j/4)/n-.5)*(w-.25)
                f.box(u,z+.53,.096,.62,.12,.13,STONE,'balustrade uprights')

def roof_z(v,x):
    corner=(abs(x)/ROOF_X)**17
    return EAVES+RISE*(v**1.43)+.83*corner*(1-v)**2

def roof_panel(b,vertices,faces,material,label,offset):
    """Close every exposed edge and give the overhang a timber soffit."""
    vertices=np.asarray(vertices,float)
    edges={}
    for face in faces:
        for i,j in zip(face,(*face[1:],face[0])):
            key=tuple(sorted((i,j)))
            edges[key]=None if key in edges else (i,j)
    lower=vertices+np.asarray(offset)
    b.add(vertices,faces,material,label)
    b.add(lower,[tuple(reversed(face))for face in faces],SOFFIT,label+'/soffit')
    pairs=np.vstack((vertices,lower));n=len(vertices)
    edges=[(j,i,i+n,j+n)for pair in edges.values()if pair is not None for i,j in [pair]]
    b.add(pairs,edges,material,label+'/edge')

def slope(b,lod,sign):
    nx=15 if lod else 29; nz=5 if lod else 11
    def point(u,v):
        h=ROOF_X-(ROOF_X-RIDGE_X)*min(v/.51,1)
        x=u*h; y=sign*ROOF_Y*(1-v)
        return (x,y,roof_z(v,x))
    vertices=[point(u,v)for v in np.linspace(0,1,nz+1) for u in np.linspace(-1,1,nx+1)]
    faces=[]
    for j in range(nz):
        for i in range(nx):
            a=j*(nx+1)+i;q=(a,a+1,a+nx+2,a+nx+1)
            faces.append(tuple(reversed(q))if sign>0 else q)
    roof_panel(b,vertices,faces,TILE,'Roof/north clay-tile slope' if sign>0 else 'Roof/south clay-tile slope',(0,0,-.095))
    rib_n=36 if lod else 100
    for i,u in enumerate(np.linspace(-.99,.99,rib_n)):
        points=[(x,y,z+.034)for x,y,z in (point(u,v)for v in np.linspace(0,1,4 if lod else 9))]
        b.tube(points,.057 if not lod else .073,RIDGE,5,'Roof/glazed tile rolls')
    lip=[point(u,0)for u in np.linspace(-1,1,32)]
    b.tube(lip,.127,RIDGE,7,'Roof/upswept projecting eaves')

def roof_end(b,xsign,lod):
    z0=roof_z(0,ROOF_X);z1=roof_z(.51,RIDGE_X);zt=roof_z(1,RIDGE_X)
    x0=xsign*ROOF_X;x1=xsign*RIDGE_X;ym=ROOF_Y*.49
    quad=(0,1,2,3) if xsign>0 else (3,2,1,0)
    triangle=(0,1,2) if xsign>0 else (2,1,0)
    roof_panel(b,[(x0,-ROOF_Y,z0),(x0,ROOF_Y,z0),(x1,ym,z1),(x1,-ym,z1)],[quad],TILE,'Roof/lower end hip',(0,0,-.095))
    roof_panel(b,[(x1,-ym,z1),(x1,ym,z1),(x1,0,zt)],[triangle],VERMILION,'Roof/red upper gable',(-xsign*.09,0,0))
    b.tube([(x1,-ym,z1),(x1,0,zt),(x1,ym,z1)],.14,RIDGE,7,'Roof/gable bargeboards')
    for side in [-1,1]:
        b.tube([(x0,side*ROOF_Y,z0),(x1,side*ym,z1)],.15,RIDGE,7,'Roof/hip roll')
    for y in np.linspace(-ym,ym,7 if lod else 17):
        b.tube([(x0,y*ROOF_Y/ym,z0+.025),(x1,y,z1+.025)],.045,RIDGE,5,'Roof/hip tile rolls')
    b.tube([(x1,0,zt),(x1+xsign*.30,0,zt+.46),(x1+xsign*.48,0,zt+1.01),(x1+xsign*.83,0,zt+1.16)],.17,RIDGE,8,'Roof/ridge-end ornaments')

def dormer(b,x,w,lod):
    # Five apertures on the southern pitch, broader in the centre in the 2019 oblique.
    ymin=-7.57;ymax=-4.45;z=roof_z(1-abs(ymin)/ROOF_Y,x);height=1.30
    f=Facade(b,(x-w/2,ymin),(x+w/2,ymin),'Roof/south dormer')
    pane=decorated_window(f,0,z+.13,w-.58,height-.28,lod)
    f.wall(z,z+height,[pane],.22,VERMILION)
    for sx in [-1,1]:
        xx=x+sx*w/2;quad=(0,1,2,3) if sx>0 else (3,2,1,0)
        roof_panel(b,[(xx,ymin,z),(xx,ymax,z+.64),(xx,ymax,z+height+.16),(xx,ymin,z+height)],[quad],VERMILION,'Roof/dormer cheeks',(-sx*.07,0,0))
    roof_panel(b,[(x-w/2-.25,ymin-.32,z+height),(x+w/2+.25,ymin-.32,z+height),(x+w/2+.19,ymax+.28,z+height+.36),(x-w/2-.19,ymax+.28,z+height+.36)],[(0,1,2,3)],TILE,'Roof/dormer glazed canopies',(0,0,-.075))
    b.tube([(x-w/2-.25,ymin-.32,z+height+.14),(x,ymin-.33,z+height),(x+w/2+.25,ymin-.32,z+height+.14)],.084,RIDGE,6,'Roof/dormer eave crests')

def add_building(b,lod):
    north=ward_elevation(b,True,lod);south=ward_elevation(b,False,lod)
    for end in [-1,1]:
        f=Facade(b,(end*HALF,-end*DEPTH),(end*HALF,end*DEPTH),'Retained wing join')
        f.wall(0,TERRACE,[],.38,STONE)
        railing(f,f.length,lod)
        # Continue the last photographed wall bay to the two retained native sections.
        link=1.74
        b.box((end*(HALF+link/2),0,7.67),(link,2*DEPTH,15.34),STONE,label='Retained wing joins/end bays')
        b.box((end*(HALF+link/2),0,15.40),(link,2*DEPTH,.12),FLOOR,label='Retained wing joins/end bay terrace')
    for f in (north,south):railing(f,f.length,lod)
    b.box((0,0,.12),(2*HALF-.5,2*DEPTH-.5,.24),STONE,label='Central wards/base slab')
    b.box((0,0,TERRACE-.05),(2*HALF,2*DEPTH,.23),FLOOR,label='Open terrace/paving')
    for side in [-1,1]:
        y=side*(DEPTH-1.25);f=Facade(b,(side*(HALF-.86),y),(-side*(HALF-.86),y),'Upper gallery/north' if side>0 else 'Upper gallery/south')
        holes=[]
        for u in np.linspace(-23.2,23.2,18):
            holes.append(decorated_window(f,u,TERRACE+.63,1.47,2.53,lod))
        f.wall(TERRACE,EAVES-.12,holes,.33,BRICK)
        for x in np.linspace(-HALF+.65,HALF-.65,13):
            b.box((x,side*(DEPTH-.41),TERRACE+2.10),(.34,.39,4.18),STONE,label='Upper gallery/colonnade')
    for side in [-1,1]:
        b.box((side*(HALF-.98),0,(TERRACE+EAVES)/2),(.36,14.9,EAVES-TERRACE),VERMILION,label='Upper gallery/end wall')
    b.box((0,0,EAVES-.15),(55.3,19.25,.34),SOFFIT,label='Roof/timber soffit')
    for sign in [-1,1]:slope(b,lod,sign);roof_end(b,sign,lod)
    b.tube([(-RIDGE_X,0,EAVES+RISE+.13),(RIDGE_X,0,EAVES+RISE+.13)],.245,RIDGE,8,'Roof/long glazed main ridge')
    for x,w in [(-15.6,2.22),(-8.0,2.24),(0,4.63),(8.0,2.24),(15.6,2.22)]:dormer(b,x,w,lod)
