"""The common approach seen in the numbered photo series and the north gate image."""
from shapely.geometry import Polygon
from materials import *
from placement import Facade
def add_lane(b,lod=False):
    f=Facade(b,'1-2')
    # The lane passes both east fronts. Its north entrance is documented
    # directly by the Commons street photograph; the houses remain behind it.
    f.rect(-28.95,12.02,-.105,-.038,.26,4.03,PAVE,'shared pedestrian lane from Wuyuan Road')
    for u0,u1,dmax in [(-26.1,-14.2,11.3),(-6.8,6.84,11.34)]:
        f.rect(u0-.10,u1+.08,-.135,-.074,-dmax-.30,.255,PAVE,'narrow apron at ground-floor entrances')
    from lane_gate import add_gate
    add_gate(f,lod)
