"""Trace first visible surfaces through the delivered archway, inscription, upper lights and roof."""
from math import cos,pi,sin,sqrt
import numpy as np

def check_triangles(triangles,materials,distant):
    tri=np.asarray(triangles,float);m=np.asarray(materials)
    e1=tri[:,1]-tri[:,0];e2=tri[:,2]-tri[:,0]
    normals=np.cross(e1,e2)
    normals/=np.maximum(1e-30,np.linalg.norm(normals,axis=1)[:,None])
    rays=[]
    def ray(detail,origin,direction,expected,interval=None):
        o=np.array(origin);d=np.array(direction,dtype=float);d/=np.linalg.norm(d)
        h=np.cross(d,e2);det=np.einsum('ij,ij->i',e1,h)
        inv=np.divide(1,det,out=np.zeros_like(det),where=abs(det)>1e-11)
        delta=o-tri[:,0];u=np.einsum('ij,ij->i',delta,h)*inv
        q=np.cross(delta,e1);v=q@d*inv;t=np.einsum('ij,ij->i',e2,q)*inv
        ids=np.flatnonzero((abs(det)>1e-11)&(u>=-1e-8)&(v>=-1e-8)&(u+v<=1+1e-8)&(t>1e-7))
        wanted=(expected,)if isinstance(expected,str)else expected
        actual=None;distance=None;facing=None
        if len(ids):
            distance=float(t[ids].min())
            tied=ids[abs(t[ids]-distance)<2e-6]
            hit=tied[np.argmax(-normals[tied]@d)]
            actual=str(m[hit]);facing=float(-normals[hit]@d)
        passed=actual is None if wanted is None else (actual in wanted and facing>1e-5)
        if interval is not None and distance is not None:passed=passed and interval[0]<=distance<=interval[1]
        rays.append(dict(detail=detail,origin_m=list(origin),direction=list(direction),expected=wanted,
                         expected_distance_m=interval,first_material=actual,distance_m=distance,
                         facing=facing,passed=bool(passed)))
    def front(label,x,z,mat,lo=None,hi=None):
        ray(label,(x,-2,z),(0,1,0),mat,None if lo is None else [2+lo-.002,2+hi+.002])
    for x in [-1.6,-.81,.03,.81,1.6]:
        for z in [.26,1.36,2.30]:
            front('open public passage',x,z,None)
            ray('open from the courtyard',(x,5.22,z),(0,-1,0),None)
    for x in [-1.62,-.82,.12,.82,1.62]:
        ceiling=1.99+1.78*sqrt(1-(x/1.91)**2)
        for y in [.46,2.08,3.83]:
            ray('continuous arched soffit',(x,y,.12),(0,0,1),'grey passage plaster',(ceiling-.15,ceiling-.10))
    for x in [-2.61,2.61]:
        for z in [.77,2.63,4.47]:
            front('dressed street piers',x,z,'dressed gate granite',-.045,-.045)
    for z,mat in [(1.02,'aged bronze plaque'),(1.64,'faded enamel green'),(2.23,'faded enamel green')]:
        front('east pier plaque',2.51,z,mat,-.065,-.061)
    for a in [.22,.60,1.1,1.58,2.1,2.6,2.92]:
        front('light cut arch ring',1.984*cos(a),1.99+1.86*sin(a),'light cut granite',-.032,-.032)
    for char,x,z in [('邨',-.7799,4.7771),('門',.2193,4.7545),('龍',.712,4.7486)]:
        front('incised oxblood character '+char,x,z,'oxide red inscription',-.033,-.033)
    for x in [-1.087,1.09]:
        front('plain field in front of the red pigment',x,5.10,'pale inscribed slab',-.041,-.041)
    for left in [-2.21,1.59]:
        x=left+.10
        for i in [1,4,7,11,15,18,22]:
            z=5.85+(i+.44)*(9.54-5.85)/25
            front('running bond inside stone recess',x,z,('burnt red brick','rust brick','russet brick'),.107,.107)
        for row in [2,9]:
            z=5.85+(row+.37)*(9.54-5.85)/25
            mat='brick recess mortar' if row==2 else ('burnt red brick','rust brick','russet brick')
            depth=.142 if row==2 else .107
            front('staggered vertical joint or intact brick',left+.369,z,mat,depth,depth)
        front('brick bed joint',x,5.85+12*(9.54-5.85)/25,'brick recess mortar',.142,.142)
    for side in (-1,1):
        front('repainted open wood leaf',side*.824,6.55,'repainted red shutters',.16,.35)
    front('glass between shutter leaves',.133,6.48,'shaded upper glass',.492,.492)
    front('upper transom rail',.153,7.16,'dark red joinery',.385,.419)
    for i in range(20):
        z=8.33+i*.117
        front('sloped louvre '+str(i+1),.070,z+.067,'dark grey vent blades',.04,.179)
        front('gap between blades '+str(i+1),.071,z+.109,'shadowed upper recess',.414,.414)
    for ch,x,z in [('1',-.5934,11.3928),('9',-.1212,11.5054),('3',.2723,11.416),('5',.6764,11.4264)]:
        front('raised date '+ch,x,z,'dark metal numerals',.061,.061)
    for name,x in [('high',.11),('west',-2.75),('east',2.75)]:
        ray(name+' moulded ridge',(x,2.045,18),(0,0,-1),'Longmen grey ridge mortar')
    ray('street central tile roll',(0,.51,18),(0,0,-1),'Longmen charcoal cover tiles')
    ray('courtyard central tile roll',(0,3.57,18),(0,0,-1),'Longmen charcoal cover tiles')
    failed=[r for r in rays if not r['passed']]
    if failed:raise ValueError(failed)
    return dict(distant=bool(distant),triangles=len(tri),rays=rays)
