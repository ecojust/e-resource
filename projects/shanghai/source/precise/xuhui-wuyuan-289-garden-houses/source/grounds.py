"""The common approach seen in the numbered photo series and the north gate image."""
from shapely.geometry import Polygon
from materials import *
from placement import Facade
def add_lane(b,lod=False):
    f=Facade(b,'1-2')
    # The lane passes both east fronts. Its north entrance is documented
    # directly by the Commons street photograph; the houses remain behind it.
    f.rect(-28.95,14.0,-.105,-.038,.26,4.03,PAVE,'shared pedestrian lane from Wuyuan Road')
    for u0,u1,dmax in [(-26.1,-14.2,11.3),(-6.8,6.84,11.34)]:
        f.rect(u0-.10,u1+.08,-.135,-.074,-dmax-.30,.255,PAVE,'narrow apron at ground-floor entrances')
    # In 2017 two plain dark leaves close the north street mouth. The tree,
    # later office elevations and fittings of the adjacent properties are not modeled.
    gate=f.face(13.80,-4.03,0,1)
    gate.rect(.02,1.81,.04,2.17,-.058,-.015,IRON,'street entrance left leaf')
    gate.rect(1.835,3.69,.04,2.17,-.058,-.015,IRON,'street entrance right leaf')
    for x0,x1 in [(.02,1.81),(1.835,3.69)]:
        for z in [.12,1.72,2.095]:gate.rect(x0+.03,x1-.03,z-.022,z+.022,-.013,.017,IRON,'gate cross member')
        gate.rect(x0+.011,x0+.04,.058,2.17,-.012,.015,LEAD,'edge of lane gate')
