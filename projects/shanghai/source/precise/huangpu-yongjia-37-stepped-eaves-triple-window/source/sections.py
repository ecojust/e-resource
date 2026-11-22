"""Read the actual two meshes from the front, the left return and above the two eaves."""
from upper_bay import *

def test(tri,materials,hit):
    samples=[]
    def take(origin,direction,expected,label):
        contact=hit(tri,materials,np.array(origin),np.array(direction))
        assert contact and contact[0]==expected,(label,origin,expected,contact)
        samples.append(dict(label=label,material=contact[0],point=contact[1]))
        return contact[1]
    for x0,x1 in WINDOWS:
        centre=(x0+x1)*.5
        for x in (x0+.095,x1-.085):
            for z in (.74,.98,1.43,1.77,1.93):
                p=take((x,-2,z),(0,1,0),GLASS,'Recessed glazing below the tilted upper light')
                assert abs(p[1]-.175)<.001
            for z in (1.294,2.111):
                take((x,-2,z),(0,1,0),STEEL,'Steel transoms')
        for z in (.86,1.49,1.94):
            take((centre,-2,z),(0,1,0),STEEL,'Vertical steel bar')
        take((centre-.045,-2,.56),(0,1,0),HOOD,'Separate sill')
    for i in range(1,11):
        for x in (-1.17,-.98):
            take((x,-2,.18+i*.34),(0,1,0),ASHLAR,'Staggered front corner block')
        take((-3,.20,.18+i*.34),(1,0,0),ASHLAR,'Quoin carried around corner')
    for x in np.linspace(-.72,1.54,15):
        z=2.948+.329*(1-((x-.412)/1.18)**2)-.043
        take((x,-2,z),(0,1,0),HOOD,'Shallow hood spanning three separate lights')
    for x,y,z in [(-1.79,.45,2.547),(-2.13,.45,2.547),(-1.68,.66,2.547),
                    (-.53,-.065,3.837),(.35,.14,3.837),(1.05,.349,3.837)]:
        p=take((x,y,6),(0,0,-1),TILE,'True pitched surface on upper and lower roofs')
        front=.31 if x < -1.43 else -.206
        assert abs(p[2]-z-.48*(y-front)) < .002
    return samples
