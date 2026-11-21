"""Measure actual ray intersections in each delivered mesh against the photographed levels."""
import numpy as np
from shapely.geometry import Point
from gate_pier import WIDTH,HEIGHT,TOP_RECT,BLUE_RECT,STONE,CAP,JOINT,PLINTH,BRASS,RIM,INK,BLUE,EDGE,JOINT_Z,z,_number_shapes
def test(tri,names,hit):
    rows=[]
    def probe(name,x,height,mat,origin_y=-2.):
        o=np.array([x,origin_y,height]);d=np.array([0.,1.,0.]);q=hit(tri,names,o,d)
        actual=None if not q else q[0]
        assert actual==mat,(name,x,height,actual,mat)
        rows.append(dict(label=name,material=actual,point=q[1] if q else None,origin=o.tolist(),direction=d.tolist()))
    for j in JOINT_Z:
        for x in [-.27,.27]:probe('Shaft course bed',x,j,JOINT)
    for im in [451,405,352,304,262,215]:
        for x in [-.28,-.24,.24,.28]:probe('Uncovered stone beside the blue plate',x,z(im),STONE)
    for h in [475,490]:probe('Darkened lower pier',0.,z(h),PLINTH)
    for x in (-.36,-.25,.25,.36):
        for h in [190,119,112]:probe('Projecting cap and neck ledges',x,z(h),CAP)
    for x in (-.25,.25):probe('Top bevel side air',x,z(95.2),None)
    for x in (-.20,-.12,0,.12,.20):probe('Ochre plaque behind the lettering',x,z(160),BRASS)
    outline=_number_shapes()
    for i,letter in enumerate(sorted(outline.geoms,key=lambda g:g.bounds[0])):
        pt=letter.representative_point();probe('Raised number '+str(i+1),pt.x,pt.y,INK)
        for hole in letter.interiors:
            from shapely.geometry import Polygon
            p=Polygon(hole).representative_point();probe('Number counter exposing ochre face',p.x,p.y,BRASS)
    l,b,r,t=TOP_RECT
    for x in [l+.021,r-.021]:probe('Retained two bronze fasteners',x,(b+t)/2,RIM)
    l,b,r,t=BLUE_RECT
    for x in [-.18,0,.18]:
        for k in [.1,.3,.5,.7,.9]:probe('Lower independent blue plate',x,b+(t-b)*k,BLUE)
    probe('Right edge of thin mounting plate',r-.001,(t+b)/2,EDGE)
    return rows
