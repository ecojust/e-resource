"""Two shallow tile eaves, with progressively lifted hips, fascia and round cover tiles."""
import numpy as np
from shapely.geometry import Polygon

# A return at the back remains inside the individually identified street wing.
LEVELS = (
    ('Lower sheltering eaves', 27.95, [(-.05, .15, .45),(.35,.35,.38),(.70,.66,.31),(1.12,1.25,.22)]),
    ('Upper roof', 31.73, [(0,.09,.54),(.27,.21,.49),(.62,.45,.39),(1.03,.83,.29),(1.44,1.41,.19),(1.66,1.73,.14)]),
)


def ring(width, front, back, k):
    return np.array([[-width+k,front+k],[width-k,front+k],
                     [width-k,back-k],[-width+k,back-k]])


def add_eaves(b,lod):
    for name,height,profile in LEVELS:
        outer_width=19.48 if height<30 else 19.65
        front=-.95 if height<30 else -1.10
        back=10.36
        outlines=[ring(outer_width,front,back,inset) for inset,_,_ in profile]
        # The corner uplift dies out a few metres from the hip on each edge.
        def point(edge,s,level):
            poly=outlines[level];a=poly[edge];q=poly[(edge+1)%4];length=np.linalg.norm(q-a)
            at=(1-s)*a+s*q;dist=min(s,1-s)*length
            lift=profile[level][2]*max(0,1-dist/2.8)**2
            return [*at,height+profile[level][1]+lift]
        for edge in range(4):
            length=np.linalg.norm(outlines[0][(edge+1)%4]-outlines[0][edge])
            n=max(10,round(length/(.53 if lod else .24)))
            vertices=[point(edge,j/n,level) for level in range(len(profile)) for j in range(n+1)]
            faces=[]
            for lev in range(len(profile)-1):
                for j in range(n):
                    k=lev*(n+1)+j
                    faces.extend([(k,k+1,k+n+1),(k+1,k+n+2,k+n+1)])
            b.add(vertices,faces,'blue glazed tile',name+'/sloped pan tiles')
            for j in range(n):
                b.tube([np.array(point(edge,(j+.5)/n,lev))+[0,0,.035] for lev in range(len(profile))],
                       .047 if lod else .058,'glazed tile rib',5 if lod else 7,name+'/round cover tiles')
            edgepts=[point(edge,j/n,0) for j in range(n+1)]
            b.tube(edgepts,.105,'vermilion',7,name+'/vermilion eave lip')
            b.tube([point(edge,j/n,len(profile)-1) for j in range(n+1)],.118,'glazed tile rib',7,name+'/ridge')
            # Sloping soffit closes the skirt above the carved frieze.
            verts=edgepts+[np.array(p)+[0,0,-.16] for p in edgepts]
            b.add(verts,[(a,c,d) for j in range(n) for a,c,d in
                         [(j,j+n+1,j+1),(j+1,j+n+1,j+n+2)]],'vermilion',name+'/drip fascia')
            b.tube([point(edge,0,lev) for lev in range(len(profile))],.12,'glazed tile rib',8,name+'/hip roll')
        if height>30:
            # Flat service surface behind the upper rolled ridge, including its full perimeter.
            b.plan_prism(Polygon(outlines[-1]),height+profile[-1][1]-.12,
                         height+profile[-1][1]+.015,'flat upper roof',name+'/roof deck')
