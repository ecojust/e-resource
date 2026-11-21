"""Check actual model intersections at beds, perpendicular joints, shoulder stones, roof and wall."""
import numpy as np
from chimney import BED,UNIT,MORTAR,DASH,SLATE,TILE,BRICKS
def test(tri,names,hit):
    rows=[]
    def probe(label,origin,direction,allowed):
        result=hit(tri,names,np.array(origin),np.array(direction));m=result[0] if result else None
        assert m in allowed,(label,origin,m)
        rows.append(dict(label=label,material=m,point=result[1] if result else None,origin=origin,direction=direction))
    for i in [1,4,7,10,13,19,26,33,37,40,44,48,52,56,58]:
        width=1.30 if i<10 else .91 if i<38 else .69
        for j in (1,2):
            joint=-width/2+UNIT*(j-(i%2)*.5)
            probe('Front brick arris and face',[joint+.048,-2.,(i+.49)*BED],[0.,1.,0.],BRICKS)
            probe('Recessed perp joint',[joint,-2.,(i+.49)*BED],[0.,1.,0.],[MORTAR])
        probe('Horizontal bed joint',[.018,-2.,(i+1)*BED-.0001],[0.,1.,0.],[MORTAR])
    for z,outside,inner in [(10*BED,.653,.455),(38*BED,.459,.345)]:
        for sign in (-1,1):
            probe('Weathered upper face of stepped shoulder',[sign*(outside+inner)/2,-.25,z+.27],[0.,0.,-1.],[SLATE])
    for x in [-1.25,-.98,.94,1.29]:
        for z in [.37,1.5,2.05]:probe('Coarse cast at either side',[x,-2,z],[0.,1.,0.],[DASH])
        for y in [.17,.57]:probe('Ribbed red clay tile',[x,y,4.6],[0.,0.,-1.],[TILE])
    for x in (-1.77,1.77):probe('Open sky at the ends of the verge',[x,-1,3.3],[0.,1.,0.],[None])
    return rows
