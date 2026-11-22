"""Rays measure both rounded fasciae, the four round supports, the guard, and open intercolumniations."""
from terrace import *
def test(tri,m,hit):
    readings=[]
    def ask(name,o,d,mat):
        row=hit(tri,m,np.array(o,float),np.array(d,float));assert (row and row[0])==mat,(name,o,mat,row)
        readings.append(dict(label=name,material=mat,point=row[1]if row else None))
    for x in np.linspace(-2.18,2.18,17):
        for z,name,mat in [(2.82,'Inner curved band',STONE),(3.235,'Overhanging slab nose',RIM),(3.808,'Lower horizontal tube',RAIL),(3.943,'Middle horizontal tube',RAIL),(4.069,'Upper horizontal tube',RAIL),(4.204,'Continuous curved handrail',RAIL)]:
            ask(name,[x,-2.79,z],[0,1,0],mat)
        y=-REACH*math.sqrt(1-(x/RADIUS)**2)*.80
        ask('Curved upper terrace paving',[x,y,3.51],[0,0,-1],WALK)
    for angle in(-1.22,-.41,.41,1.22):
        x,y,_=loc(angle,0,.914)
        for z in(.19,.51,1.111,1.97,2.45):ask('One of four round independent supports',[x,-2.5,z],[0,1,0],COLUMN)
    for x in(-1.35,-.42,.34,1.39):
        for z in(.41,1.39):ask('Clear span in front of recessed wall',[x,-2.45,z],[0,1,0],WALL)
    return readings
