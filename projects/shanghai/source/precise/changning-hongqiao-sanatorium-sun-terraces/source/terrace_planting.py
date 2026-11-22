"""The two pot silhouettes distinct from the trees beyond the terrace rails."""
import json
import math
import numpy as np
from terraced_section import HERE, UPPER

POTS=json.loads((HERE.parent/'measurements/potted-evergreens.json').read_bytes())['pots']
POT='Weathered dark plant pot'
RIM='Pot lip in daylight'
SOIL='Planting soil'
BARK='Small conifer trunk'
FOLIAGE=['Evergreen outer shoots','Evergreen inner shoots','Evergreen side shoots']

def planting(b,lod):
    for idx,spec in enumerate(POTS):
        x,y=spec['base_xy_m'];pot_h=spec['pot_height_m'];rad=spec['pot_width_m']/2;h=spec['height_m'];z=UPPER+.010;label='Potted evergreen '+spec['name']
        # Open tapered clay body and rim, with a recess occupied by a separate soil surface.
        rings=[(z,.64*rad),(z+.022,.66*rad),(z+pot_h-.029,rad*.966),(z+pot_h-.016,rad),(z+pot_h,rad),(z+pot_h,rad-.014),(z+pot_h-.036,rad-.018)]
        sides=12 if lod else 24
        vs=[(x+radius*math.cos(j*math.tau/sides),y+radius*math.sin(j*math.tau/sides),zg) for zg,radius in rings for j in range(sides)]
        fs=[(k*sides+j,k*sides+(j+1)%sides,(k+1)*sides+(j+1)%sides,(k+1)*sides+j) for k in range(len(rings)-1) for j in range(sides)]
        b.add(vs,fs,POT,label+'/tapered open pot')
        b.lathe((x,y),[(z+pot_h-.030,.96*rad),(z+pot_h-.025,rad+.002),(z+pot_h-.012,rad+.002),(z+pot_h-.009,.99*rad)],RIM,segments=12 if lod else 24,label=label+'/rolled band')
        b.lathe((x,y),[(z+pot_h-.034,.88*rad),(z+pot_h-.026,.89*rad)],SOIL,segments=12 if lod else 24,label=label+'/visible soil')
        b.tube([(x,y,z+pot_h-.024),(x+.015,y-.014,z+h)],.011,BARK,6 if lod else 9,label+'/stem')
        rng=np.random.default_rng(139+idx);levels=13 if lod else 26;count=6 if lod else 10
        # A ragged inner crown fills the space behind the longer shoots. It keeps the two shrubs readable at a distance.
        core_rings=15 if lod else 25;core_sides=11 if lod else 18;rings=[]
        for band in range(core_rings):
            fraction=band/(core_rings-1);elev=z+pot_h+.036+fraction*(h-pot_h-.065)
            rcore=(.133 if idx==0 else .140)*(1.-fraction)**.62+.006
            rcore*=.88+.15*math.sin(band*1.89+idx)
            ring=[]
            for n in range(core_sides):
                ang=math.tau*n/core_sides+.09*math.sin(band*.53);rs=rcore*rng.uniform(.76,1.19)
                ring.append((x+.015*fraction+rs*math.cos(ang),y-.013*fraction+rs*math.sin(ang),elev+rng.uniform(-.026,.026)*(1.-fraction)))
            rings.append(ring)
        for band in range(core_rings-1):
            faces=[(j,(j+1)%core_sides,core_sides+(j+1)%core_sides,core_sides+j) for j in range(core_sides)]
            b.add(rings[band]+rings[band+1],faces,FOLIAGE[1 if band%3 else 2],label+'/inner crown '+str(band+1))
        for row in range(levels):
            level=(row+.4)/levels;zc=z+pot_h+.039+level*(h-pot_h-.060);spread=(1.-level)**.64*(.237 if idx==0 else .245)
            for az in range(count):
                angle=az*math.tau/count+row*2.1+rng.normal(0,.17);u=np.array([math.cos(angle),math.sin(angle),0.]);v=np.array([-u[1],u[0],0.]);radial=spread*rng.uniform(.66,1.03);start=np.array([x+.015*level,y-.014*level,zc]);tip=start+u*radial+[0,0,radial*rng.uniform(.15,.50)];middle=start+u*radial*.52-[0,0,radial*.08]
                # Three small keeled, overlapping fans per twig approximate the dark, irregular outline in the scan.
                verts=[start,middle+v*radial*.31,middle+[0,0,radial*.14],middle-v*radial*.29,tip,
                       middle+v*radial*.14+[0,0,radial*.29],middle-v*radial*.10+[0,0,radial*.21]]
                faces=[(0,1,2),(0,2,3),(1,4,2),(3,2,4),(1,5,2),(2,6,3),(5,4,2),(2,4,6)]
                b.add(verts,faces,FOLIAGE[(row+az)%3],label+'/shoot whorl '+str(row+1))
