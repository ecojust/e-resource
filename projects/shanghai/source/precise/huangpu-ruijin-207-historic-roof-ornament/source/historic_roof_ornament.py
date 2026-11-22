"""Editable historic crest with two upright blades, four shelf lips and a short mast section."""
import numpy as np
from shapely.geometry import Polygon
from rosholt_ornament_plane import DATA,on_face,depth,PROJECTION
STONE='Rosholt print | pale rendered ribs'
EDGE='Rosholt print | pale shelf lip'
METAL='Rosholt print | weathered mast'
SHOE='Rosholt print | mast shoe'
def grey(value,roughness,metallic=0.):
    return dict(color=[((value/255+.055)/1.055)**2.4]*3,roughness=roughness,metallic=metallic)
PALETTE={STONE:grey(192,.81),EDGE:grey(185,.74),METAL:grey(110,.58,.27),SHOE:grey(133,.72,.13)}
def blade(obs):
    a,b,c=[on_face(obs[k]) for k in ('top_left','top_right','bottom_left')]
    return [a[0],b[0],0.,depth(obs['top_left'],obs['rear_top_left']),c[2],(a[2]+b[2])/2]
def shelves():
    rows=[]
    for obs in DATA['shelves']:
        lo,hi,left=[on_face(obs[k]) for k in ('lower_lip','upper_lip','root')]
        rows.append([left[0],lo[0],-.05,.13,lo[2],hi[2]])
    return rows
def box(builder,bounds,material,label):
    x0,x1,y0,y1,z0,z1=bounds
    builder.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),material,label=label)
def mast_geometry():
    a,b=[on_face(DATA['mast'][k]) for k in ('top_sample','low_sample')]
    radius=DATA['mast']['diameter_px']/(2*np.linalg.norm(PROJECTION[0,:2]))
    return (a[0]+b[0])/2,.055,b[2],a[2],radius
def add_ornament(builder,lod=False):
    low=lod in (True,'lod')
    for obs in DATA['ribs']:box(builder,blade(obs),STONE,obs['name'])
    for i,(x0,x1,y0,y1,z0,z1) in enumerate(shelves()):
        cut=.022
        poly=Polygon([(x0,y0),(x1-cut,y0),(x1,y0+cut),(x1,y1),(x0,y1)])
        builder.plan_prism(poly,z0,z1,EDGE,f'cantilever lip {i+1}')
    x,y,lo,hi,r=mast_geometry()
    builder.tube([(x,y,lo),(x,y,hi)],r,METAL,sides=10 if low else 24,label='visible historic mast segment')
    foot=on_face(DATA['mast']['foot'])
    box(builder,[x-r*1.45,x+r*1.45,y-r*1.3,y+r*1.3,lo,foot[2]+.045],SHOE,'short terminal shoe')
    for i,(_,_,_,_,z0,z1) in enumerate(shelves()):
        builder.tube([(x,y,z0-.023),(x,y,z0+.017)],r*1.32,SHOE,sides=8 if low else 16,label=f'collar beneath lip {i+1}')
