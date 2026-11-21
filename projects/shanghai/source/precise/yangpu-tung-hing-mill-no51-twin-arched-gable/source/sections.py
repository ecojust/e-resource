"""Probe the two independent openings, three splayed windows and folded roof outline."""
import math
import numpy as np
from arched_gable import WALL,TRIM,RIB,GLASS,STONE,EDGE,SOFFIT,TILE_LIGHT
def test(tri,names,hit):
    rows=[]
    def ray(label,p,v,material):
        origin=np.asarray(p,dtype=float);direction=np.asarray(v,dtype=float)
        contact=hit(tri,names,origin,direction)
        value=contact[0] if contact else None
        assert value==material,(label,p,v,value,material)
        rows.append(dict(label=label,origin=origin.tolist(),direction=direction.tolist(),material=value,point=contact[1] if contact else None))
    def front(label,x,z,m):ray(label,(x,-3,z),(0,1,0),m)
    for side,x in [('left',-.378),('right',.378)]:
        for dx in (-.15,0,.15):
            for z in (3.23,3.42,3.58):
                front(side+' arched glass',x+dx,z,GLASS)
        for dx in (-.075,.075):
            for z in (3.24,3.46,3.62):front(side+' separate vertical',x+dx,z,RIB)
        for dx in (-.219,.219):
            for z in (3.29,3.43):front(side+' pale jamb',x+dx,z,TRIM)
        front(side+' curved frame crown',x,3.757,TRIM)
        front(side+' spring rail',x,3.502,RIB)
        for dx in (-.18,0,.18):front(side+' own sill',x+dx,3.104,STONE)
    for x in (-2.21,-1.19,0,1.19,2.21):front('Continuous ochre gable',x,2.62,WALL)
    for x in (-2.17,2.17):
        roof=2.28+(3.52-abs(x))*(4.62-2.28)/(3.52-1.01)
        front('Projected painted fascia',x,roof-.035,EDGE)
        front('Rolled tile edge',x,roof+.063,TILE_LIGHT)
        front('Open sky',x,roof+.32,None)
    bay=[(-2.22,-.035),(-.75,-.48),(.75,-.48),(2.22,-.035)]
    for i,(p,q) in enumerate(zip(bay,bay[1:])):
        d=math.dist(p,q);ux=(q[0]-p[0])/d;uy=(q[1]-p[1])/d
        cx=(p[0]+q[0])/2;cy=(p[1]+q[1])/2
        def local(label,u,z,m):
            ray(str(i+1)+' '+label,(cx+ux*u+uy*3,cy+uy*u-ux*3,z),(-uy,ux,0),m)
        for u in (-.19,.19):
            for z in (.31,.68,1.03,1.56):local('separate pane',u,z,GLASS)
            for z in (.49,.84,1.16):local('casement bar',u,z,RIB)
            local('transom',u,1.39,TRIM)
        for u in (-.445,.445):local('jamb',u,.68,TRIM)
        local('meeting stile',0,.68,TRIM)
        local('window stool',.19,.09,STONE)
    return rows

