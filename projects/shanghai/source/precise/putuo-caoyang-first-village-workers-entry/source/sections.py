"""Read the two wall planes, stair and side sash, doorway, canopy and tile courses from each exported mesh."""
import numpy as np
from entry import WALL, BASE, FRAME, GLASS, LIGHT, SHADE, TILES, DOOR, STAIR, SIDE_LOW, SIDE_HIGH

def test(mesh, names, hit):
    results = []
    def cast(origin, direction, allowed, label):
        intersect = hit(mesh,names,np.array(origin,dtype=float),np.array(direction,dtype=float))
        assert intersect and intersect[0] in allowed,(label,origin,direction,intersect,allowed)
        results.append(dict(label=label,material=intersect[0],point=intersect[1]))
        return intersect[1]
    for x in np.linspace(-.60,2.83,11):
        for z in [.145,.42,1.18,1.95,2.97,3.61,4.17,4.76]:
            if any(l-.08<x<r+.08 and b-.10<z<t+.08 for l,r,b,t in [DOOR,STAIR]):continue
            if 1.0<x<2.7 and 2.20<z<2.78:continue
            v=cast((x,-.18,z),(0,1,0),[BASE] if z<.265 else [WALL],'Entrance wall or plinth')
            assert abs(v[1]) < .001
    for y in [-2.03,-1.9,-.29,-.14]:
        for z in [.34,.67,1.26,2.12,2.88,3.61,4.48]:
            v=cast((1.5,y,z),(-1,0,0),[WALL],'Return facade normal')
            assert abs(v[0]+.82)<.001
    for x in [1.47,1.77,2.08,2.26]:
        for z in [.31,.74,1.21,1.72,2.045]:
            v=cast((x,-2,z),(0,1,0),[SHADE],'Open doorway shadow')
            assert v[1]>.27
    for frac,mat in [(.25,GLASS),(.75,LIGHT)]:
        l,r,b,t=STAIR
        for x in [l+.11,(l+r)/2,r-.10]:
            v=cast((x,-2,b+frac*(t-b)),(0,1,0),[mat],'Stair light behind the wall plane')
            assert v[1]>.12
    for l,r,b,t in [SIDE_LOW,SIDE_HIGH]:
        for i in range(4):
            y=(l+r)*.5+(r-l)*.24
            z=b+.025+(t-b-.05)*(i+.45)/4
            p=cast((1.5,y,z),(-1,0,0),[LIGHT if i==3 else GLASS],'Return sash panes')
            assert p[0]<-.90
    l,r,b,t = SIDE_LOW
    for frac in [.22,.47,.77]:
        along = (r-l)*.40*frac
        y = l+.045+np.cos(.91)*along
        z = b+.275*(t-b)
        p=cast((1.5,y,z),(-1,0,0),[GLASS],'Open casement extends into the entrance court')
        assert p[0]>-.99+np.sin(.91)*along
    for x in np.linspace(1.16,2.54,10):
        for y in [-.59,-.40,-.17]:
            v=cast((x,y,3.23),(0,0,-1),TILES,'Door hood follows the tiled incline')
            assert 2.39 < v[2] < 2.79
    for x in np.linspace(-.56,2.71,8):
        for y in [-.12,.05,.28,.52,.76,.98]:
            v=cast((x,y,7),(0,0,-1),TILES,'Pitched roof above the entrance')
            assert 5.09 < v[2] < 5.91
    for y in [-2.16,-1.83,-1.44,-.91,-.53]:
        for x in [-.95,-1.33,-1.70,-2.18,-2.67,-2.94]:
            v=cast((x,y,7),(0,0,-1),TILES,'Short roof above the projecting return')
            assert 5.13<v[2]<6.02
    return results
