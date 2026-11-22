"""First intersections with the photographed columns, turned rail, side opening and roof."""
import numpy as np
from end_loggia import COLUMNS,BALUSTERS,STONE,SEAT,WALL,DARK,ROOF,INNER
def test(tri,names,hit):
    rows=[]
    def ray(label,p,d,expect):
        ans=hit(tri,names,np.array(p),np.array(d))
        assert (ans and ans[0]==expect) if expect else ans is None,(label,p,expect,ans)
        rows.append(dict(label=label,material=ans[0] if ans else None,point=ans[1] if ans else None))
    for x in COLUMNS:
        for z in (1.03,1.31,1.67,1.97,2.31,2.67,2.98,3.22,3.50):
            ray('Rounded shaft at multiple elevations',(x,-.75,z),(0,1.,0),STONE)
        for z in (.42,.56,3.68,3.81):ray('Moulded capital and base',(x,-.77,z),(0,1.,0),STONE)
    for x in BALUSTERS:
        if min(abs(x-c)for c in COLUMNS)<.14:continue
        for z in (.384,.515,.688):ray('Turned stone spindle section',(x,-.78,z),(0,1.,0),STONE)
    for x in (-1.63,-1.27,-.67,-.38,0,.38,.67,1.27,1.63):
        ray('Continuous upper rail',(x,-.78,.878),(0,1.,0),SEAT)
    for x in (-2.11,2.11):
        for z in (.65,1.2,1.8,2.3,2.9,3.50):ray('Square rendered pier',(x,-.76,z),(0,1.,0),WALL)
    for x in (-.52,0,.48):
        for z in (1.31,1.78,2.21,2.63):ray('Recessed opening seen though gallery',(x,-.76,z),(0,1.,0),DARK)
    for y,z in ((.90,1.45),(1.08,1.92),(1.26,2.25),(1.07,2.72)):
        ray('Open arch on side return',(-2.75,y,z),(1.,0,0),None)
    for y,z in ((.45,2.86),(.71,3.23),(1.08,3.45),(1.57,3.32),(1.80,2.55)):
        ray('Side wall above or beside the curve',(-2.78,y,z),(1.,0,0),WALL)
    for x in (-.73,-.36,.03,.42,.82):ray('Front entablature recessed band',(x,-.79,4.10),(0,1.,0),INNER)
    for x in (-.35,.37,.82):ray('Sloping roof plane',(x,.59,5.68),(0,0,-1.),ROOF)
    ray('Intersection with the eave-to-ridge hip seam',(-2.413+(1.323*.5),-.30+1.66*.5,5.70),(0,0,-1.),SEAT)
    return rows
