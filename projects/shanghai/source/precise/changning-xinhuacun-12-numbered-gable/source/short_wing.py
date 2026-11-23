"""Short masonry return and hipped roof beneath the second chimney in both numbered-house photographs."""
import json
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
HERE=Path(__file__).absolute().parent
P=np.array(json.loads((HERE.parent/'measurements/three-photographic-stations.json').read_bytes())['numbered-front']['P'])
B='warm red facing brick';S='coarse grey-brown pebble dash';T='terracotta roof';C='pale precast cement';W='deep green window joinery';G='dark casement glass';I='dark cast rainwater iron'
def point(uv,y):
    v=np.linalg.solve(np.column_stack([P[:,0],P[:,2],P[:,3]+P[:,1]*y]),[*uv,1])
    return np.array([v[0]/v[2],y,v[1]/v[2]])
def make(b,lod):
    face=1.10;ridge=2.80
    def plane(poly,lo,hi,mat,name):
        b.prism(poly,-hi,-lo,lambda x,z,d:(x,-d,z),mat,'short wing/'+name)
    lower_l=point((361,244),face);lower_r=point((479,234),face);peak_l=point((427,184),ridge);peak_r=point((480,182),ridge)
    lower_r[2]=lower_l[2];peak_r[2]=peak_l[2];bl=lower_l+np.array([.02,2.80,0]);br=lower_r+np.array([.02,2.80,0])
    def roofplate(top,label):
        # Orient the upper face outward before closing the lower face and sides.
        if np.cross(top[1]-top[0],top[2]-top[0])[2]<0:top=list(reversed(top))
        n=len(top);v=[p.copy() for p in top]+[p-[0,0,.11]for p in top];f=[[0,j,j+1]for j in range(1,n-1)]+[[n,n+j+1,n+j]for j in range(1,n-1)]
        for j in range(n):
            q=(j+1)%n;f.append((j,j+n,q+n,q))
        b.add(v,f,T,'short wing/'+label)
    roofplate([lower_l,lower_r,peak_r,peak_l],'hipped clay roof front slope')
    roofplate([lower_l,peak_l,bl],'western hipped end')
    roofplate([bl,peak_l,peak_r,br],'ridge return')
    count=9 if lod else 20
    for i in range(count):
        t=(i+.42)/count
        low=lower_l+(lower_r-lower_l)*t;high=peak_l+(peak_r-peak_l)*t
        b.tube([low+[0,0,.011],high+[0,0,.011]],.025,T,5 if lod else 8,f'short wing/roof tile roll {i+1}')
    x0,z0=lower_l[[0,2]];x1=lower_r[0];front=face+.095
    window=box(-1.55,3.0,-.27,4.63);wall=box(x0+.14,.05,x1-.05,z0-.115).difference(window)
    plane(wall,front,front+.28,S,'roughcast front with recessed bay')
    plane(window.difference(window.buffer(-.049,join_style='mitre')),front+.083,front+.22,W,'green frame at left bay')
    plane(window.buffer(-.053,join_style='mitre'),front+.19,front+.215,G,'window behind parapet')
    b.box((x0+.20,(front+bl[1])/2,(z0-.09)/2),(.28,bl[1]-front,z0-.09),B,label='short wing/brick side below hipped end')
    b.box(((x0+x1)/2,front-.045,z0-.033),(x1-x0+.13,.38,.143),I,label='short wing/eaves lip and gutter')
    for j in range(12):
        x=x0+.23+(x1-x0-.50)*j/11
        b.box((x,front-.031,z0-.14),(.062,.15,.090),C,label=f'short wing/soffit end {j+1:02}')
    plane(box(-1.63,.03,-.12,2.74),front-.55,front-.37,B,'projecting low brick parapet')
    b.box((-.875,front-.465,2.777),(1.57,.23,.080),C,label='short wing/parapet coping')
    # The stack meets the slope where the tile surface passes its four corners.
    x,y,z=json.loads((HERE/'roof-end.json').read_bytes())['west_chimney_center_xyz']
    slope=(y-face)/(ridge-face);roof_z=lower_l[2]+slope*(peak_l[2]-lower_l[2]);bottom=roof_z-.43;top=z-.465
    if top>bottom:
        b.box((x,y,(bottom+top)/2),(.488,.558,top-bottom),B,label='short wing/brick chimney shaft into roof')
    return b
