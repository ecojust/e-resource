import numpy as np
from balconies import *
def test(tri,names,hit):
    rows=[]
    def ray(o,d,want,label):
        h=hit(tri,names,np.asarray(o,float),np.asarray(d,float));assert h and h[0] in want,(o,label,h,want)
        rows.append(dict(label=label,material=h[0],point=h[1]));return np.array(h[1])
    for c in CENTERS:
        for dx in np.linspace(-.712,.712,17):
            for z in (.803,1.027,1.25):
                p=ray([c+dx,-2,z],[0,1,0],[IRON],'Guard rod');assert abs(p[1]+(.741 if abs(dx)>.71 else .729))<.007
        for dx in (-.47,-.31,.22,.47):
            for z in (1.798,2.067,2.435,2.601):
                p=ray([c+dx,-1.6,z],[0,1,0],[LIGHT,GLASS],'French door or transom glass');assert abs(p[1]-.136)<.001
        for x in (c-.385,c+.385):
            for z in (.13,.18,.24,.32):
                p=ray([x,-1.51,z],[0,1,0],[STONE],'Taper of cantilever support');assert -.59<p[1]<-.12
        for x in np.linspace(c-.66,c+.66,7):
            for z,d,m in [(.40,.754,SHADE),(.453,.797,STONE),(.510,.806,EDGE),(.551,.787,STONE)]:
                p=ray([x,-2,z],[0,1,0],[m],'Rounded slab nosing');assert abs(p[1]+d)<.001
        for dx in (-.923,.923):
            for z in (.24,.85,1.77,2.97):
                p=ray([c+dx,-2,z],[0,1,0],[BRICK],'Brick pier');assert abs(p[1])<.001
    for x in np.linspace(-3,3,19):
        p=ray([x,-2,3.473],[0,1,0],[EDGE],'Stringcourse');assert abs(p[1]+.145)<.001
    return rows
