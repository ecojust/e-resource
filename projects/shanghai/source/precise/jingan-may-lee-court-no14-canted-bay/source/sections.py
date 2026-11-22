"""First surface of each real glazing panel, frame, sill, brick spandrel and terrace railing."""
import numpy as np
from garden_bay import FACES,BRICK,STEEL,STONE,LIP,RAIL,MULLION,HEIGHT,xyz,pane_material
def test(tri,names,hit):
    readings=[]
    for face,(span,frames,cols) in FACES.items():
        direction=np.array((0,1,0) if face=='wide' else (1,0,0))
        def ray(u,z,expected,label):
            point=np.array(xyz(face,u,z,.63))
            result=hit(tri,names,point,direction)
            assert result and result[0]==expected,(face,label,u,z,expected,result)
            readings.append({'label':face+' '+label,'material':result[0],'point':result[1]})
        for level,(a,b,lo,hi) in enumerate(frames):
            jamb=.093 if face=='wide' else .077
            xs=np.linspace(a+jamb+.033,b-jamb-.033,cols+1)
            zs=np.linspace(lo+.105+.033,hi-.092-.033,6)
            for i,(left,right) in enumerate(zip(xs[:-1],xs[1:])):
                for j,(bottom,top) in enumerate(zip(zs[:-1],zs[1:])):
                    ray((left+right)/2,(bottom+top)/2,pane_material(face,level,i,j),'glass pane')
            for i,x in enumerate(xs[1:-1],1):
                for y,z in zip(zs[:-1],zs[1:]):
                    ray(x,(y+z)/2,MULLION if i==cols//2 else STEEL,'steel vertical')
            for z in zs[1:-1]:ray((xs[0]+xs[1])/2,z,STEEL,'horizontal glazing bar')
            for z in np.linspace(lo+.2,hi-.2,3):
                ray(a+jamb/2,z,STONE,'cement surround')
            for x in np.linspace(a+.1,b-.1,5):ray(x,lo+.055,LIP,'projecting sill')
        for u in np.linspace(.08,span-.08,6):
            for z in (.49,3.11,3.64,6.24):ray(u,z,BRICK,'continuous brickwork')
        count=6 if face=='wide' else 3
        for i in range(count+1):
            u=.025+(span-.05)*i/count
            ray(u,HEIGHT+.46,RAIL,'terrace upright')
    return readings
