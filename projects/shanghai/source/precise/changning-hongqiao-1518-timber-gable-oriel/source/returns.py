"""Visible joinery of the two cornices, a shallow masonry cut and the garden drainpipes."""
import numpy as np
from shapely.geometry import Polygon
from photo_architecture import Facade
from photograph import wall_coordinates, wall_shape
from garden_wall import CREAM, PLINTH, END, FIELD, OUTLINE
from tiled_hip_roofs import ANCHORS

DRAIN='Dark grey cast iron'
CUT='Plaster at the cropped wall return'


def add_returns(b,lod):
    front = Facade(b,[-.5,0],[.5,0],'Garden return')
    wall = wall_shape(OUTLINE)
    front.prism(wall,-1.08,-.99,CUT,'back of the study section')
    for side,points in [('west',[[500,438],[500,279],[478,257],[478,239],[462,226],[525,111]]),
                        ('east',[[661,449],[663,243],[675,226],[603,101]])]:
        coords=wall_coordinates(points)
        for n,((x0,z0),(x1,z1)) in enumerate(zip(coords,coords[1:])):
            vs=[(x0,.29,z0),(x1,.29,z1),(x1,1.07,z1),(x0,1.07,z0)]
            direction=np.cross(np.subtract(vs[1],vs[0]),np.subtract(vs[2],vs[0]))
            if (direction[0]*(1 if side=='east' else -1)+direction[2]*.12)<0:vs=vs[::-1]
            b.add(vs,[(0,1,2,3)],CUT,'Garden return/'+side+' cut edge '+str(n+1))
    # Short roof cut on the two inclined gable edges. Its unseen depth
    # is limited to the same 1.07 m section as the back of the wall.
    for side,edge in [('west',[[462,226],[525,111]]),('east',[[603,101],[675,226]])]:
        coords=wall_coordinates(edge)
        e0,e1=[np.array([x,-.025,z])for x,z in coords]
        d=e1-e0
        along=d / np.linalg.norm(d)
        lift=np.array([-along[2],0,along[0]])
        if lift[2]<0:lift=-lift
        corners=[e0,e1,e1+[0,1.11,0],e0+[0,1.11,0]]
        top=[v+lift*.059 for v in corners]
        b.add([*corners,*top],[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],
              END,'Gable roof/'+side+' clipped roof planking')
        count=int(np.linalg.norm(d)/.168)
        for i in range(count):
            t0,t1=i/count,(i+.967)/count
            p0,p1=e0+d*t0+lift*.060,e0+d*t1+lift*.060
            strip=[p0,p1,p1+[0,1.10,0],p0+[0,1.10,0]]
            thick=[v+lift*.024 for v in strip]
            b.add([*strip,*thick],[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],
                  '480 weathered brown pan','Gable roof/'+side+' side courses')
    lip=[ANCHORS[n] for n in ('gable eave left','gable eave right')]
    lower=[v-[0,0,.12] for v in lip]
    vs=[*lower,*lip,*[v+[0,.32,0]for v in [*lower,*lip]]]
    b.add(vs,[(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)],END,'Gable roof/top eave fascia')
    skirt=wall_shape([[504,432],[519,433],[597,444],[660,445],[661,449],[504,438]]).intersection(wall)
    front.prism(skirt,-.05,.04,PLINTH,'garden plinth')
    for name,points in [('west',[[482,242],[482,256],[503,269],[505,277],[505,436]]),
                        ('east',[[673,228],[673,237],[664,247],[661,255],[661,445]])]:
        xz=wall_coordinates(points,-.117)
        pipe=np.array([(x,-.117,z)for x,z in xz]);b.tube(pipe,.048,DRAIN,8 if lod else 16,'Rainwater/'+name+' dogleg and downpipe')
        for i,q in enumerate([.17,.47,.77]):
            pos=pipe[-1]*(1-q)+pipe[-2]*q
            b.tube([pos-[0,0,.016],pos+[0,0,.016]],.057,DRAIN,8 if lod else 16,'Rainwater/'+name+' collar '+str(i+1))
    # The black and brown fascia follows the lower edge of all three tiled roof planes.
    edge=[ANCHORS[k] for k in ('oriel left wing eave','oriel front eave left','oriel front eave right','oriel right wing eave')]
    for n,(p,q) in enumerate(zip(edge,edge[1:]),1):
        for tag,lo,hi,material in [('shadow lip',.03,.115,END),('brown soffit',.106,.335,'Red brown roof cornice'),('cream soffit',.326,.577,PLINTH)]:
            verts=[]
            for back in [0.,.21]:
                for lev in [hi,lo]:
                    for v in [p,q]:verts.append([v[0],v[1]+back,v[2]-lev])
            b.add(verts,[(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)],material,'Oriel roof/'+str(n)+' '+tag)
    base=Polygon([(p[0],p[1])for p in edge]+[(edge[-1][0],.11),(edge[0][0],.11)])
    lowest=min(p[2]for p in edge)
    # The underside of the eaves closes the return to the wall.
    b.plan_prism(base,lowest-.59,lowest-.53,FIELD,'Oriel roof/closed soffit underside')
