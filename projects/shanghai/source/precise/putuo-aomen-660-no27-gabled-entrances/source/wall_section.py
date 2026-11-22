"""Close the short section immediately behind the measured gable front."""
from shapely.geometry import Polygon
from photo_architecture import Facade
from garden_gable import x,z,poly,FIELD
CUT='Neutral section through rear wall'
FOUNDATION='Grey garden threshold slab'
def add_section(b):
    left=x(128);right=x(414);depth=1.91
    for label,edge,other,h in [('left',left,right,z(101)),('right',right,left,z(82))]:
        b.box([edge,depth/2.,h/2.],[.13,depth,h],FIELD,label='Shallow return/'+label+' plastered side')
    fq=Facade(b,[-.5,depth],[.5,depth],'Roof section')
    shape=poly([(128,359),(128,92),(251,-43),(414,77),(414,359)])
    fq.prism(shape,-.015,.05,CUT,'rear section')
    b.plan_prism(Polygon([(left,0),(right,0),(right,depth),(left,depth)]),-.085,.005,FOUNDATION,'Short section/underfloor')
