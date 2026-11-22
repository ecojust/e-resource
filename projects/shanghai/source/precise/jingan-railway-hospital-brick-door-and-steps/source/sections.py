"""Read two glass levels, reveals, pulls, both vents, and each step off real triangles."""
from door_and_steps import *
def test(tri,materials,hit):
    result=[]
    def view(o,d,mat,name):
        row=hit(tri,materials,np.array(o),np.array(d));assert row and row[0]==mat,(name,o,mat,row)
        result.append(dict(label=name,material=row[0],point=row[1]));return row[1]
    def front(x,z,mat,name):return view([x,-2,z],[0.,1.,0.],mat,name)
    for x in(-1.31,-1.15,-.94,-.801,.80,.971,1.143,1.29):
        for z in(.425,.87,1.39,1.978,2.379,2.788):front(x,z,BRICK,'Actual brick surround')
    for x in(-.60,-.34,-.14,.14,.34,.60):
        for z in(.53,.825,1.111,1.49,1.95,2.33,2.47):front(x,z,GLASS,'Two glazed leaves and fixed transom')
    for x in(-.70,0,.70):
        for z in(.51,.817,1.79,2.44,2.53):front(x,z,FRAME,'Full height metal rail')
    for x in(-.60,-.25,0,.25,.60):front(x,2.655,LEDGE,'Projected lintel face')
    for x in(-1.244,1.244):front(x,.055,VOID,'Basement vent depth')
    for x in(-.052,.052):
        for z in(1.080,1.173,1.29,1.354):front(x,z,HANDLE,'Vertical handle')
    for x in(-.367,.367):front(x,1.69,MEDAL,'Circular door mark')
    for y in(-.64,-.45,-.236):
        for x in(-.682,-.482,-.226,.177,.49,.711):view([x,y,.64],[0.,0.,-1.],TILE,'Walkable tiled step top')
    return result
