"""Finish concealed structural planes behind the photographed garden details."""
import numpy as np
from shapely.geometry import Polygon
from lawn import EYE,FRONT,plane_world,pitched,roof_z,front_poly
from cypress_loggia import PIER,REAR,PLASTER,SOFFIT,FRONT as GALLERY
from cypress_dormer import DARK,FIRED,WOOD

SHADE='Warm brick in loggia shade';TOP='Stone floor of covered gallery'
def photo_plane(b,outline,y,thickness,material,label):
    b.prism(front_poly(outline,y),-thickness,0.,lambda x,z,d:(x,y-d,z),material,label)
def add_cuts(b):
    # Plain wall closures represent the shaded rear of the real building. The
    # visible glazing and upper white panels remain on their own recessed planes.
    photo_plane(b,[[534.5,240],[667,233],[667,378],[535,384]],REAR+.126,.17,SHADE,'Loggia/rear masonry in shade')
    photo_plane(b,[[539,242],[666,235],[666,253],[538,256]],REAR+.108,.16,SOFFIT,'Loggia/shadow under upper eave')
    for name,px in [('left',[[539,341.7],[545.5,341.7],[545.5,377.8],[538.8,378.1]]),
                    ('right',[[658.5,331.8],[665,331.8],[665,374.5],[658.7,375.0]])]:
        photo_plane(b,px,GALLERY+.006,.29,PIER,'Loggia/'+name+' estimated concealed pier foot')
    front=plane_world([[537.4,378.2],[665.4,374.4]],1,GALLERY-.02)
    low=min(front[0,2],front[1,2]);x0,x1=front[:,0]
    b.box([(x0+x1)/2,(GALLERY+REAR)/2,low-.046],[x1-x0,REAR-GALLERY+.08,.104],TOP,label='Loggia/ground floor in section')
    # The photographed dormer has a deep red lintel between its projecting pent
    # and the two lights. Back its splayed overhang all the way to the wall.
    photo_plane(b,[[473.8,182.2],[520.2,176.7],[520.5,185.2],[478.6,191.1]],FRONT+.025,.124,WOOD,'Dormer/lintel behind pent overhang')
    # Join the high gable to the left verge of the lower wing. A daylight slot in
    # this abutment would incorrectly show the sky from slightly oblique views.
    main0,main1=pitched([[542.9,238.8],[581.,150.7]])
    a,e=plane_world([[550.4,246.1]],1,-1.14)[0],plane_world([[593.1,194.9]],1,1.71)[0]
    edge=[]
    delta=main1-main0;normal=np.array([delta[1],-delta[0],0.]);origin=np.r_[main0,0.]
    for v in [a,e]:
        ray=v-EYE
        on_wall=EYE+ray*(np.dot(origin-EYE,normal)/np.dot(ray,normal))
        edge.append(on_wall-[0,0,.033])
    floor=np.array([edge[0],a-[0,0,.041],e-[0,0,.041],edge[1]])
    thick=floor-[0,0,.142]
    b.add([*floor,*thick],[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],FIRED,'High gable/lower wing abutment')
