"""The recessed stair bay and roof surfaces read in the street photographs and archived orthophotos."""
import json
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
TILE='weathered red roof tile'
CAP='rounded terracotta ridge'
JOINT='dark red tile lap'
PALETTE={TILE:dict(color=[.398,.171,.111],roughness=.91),CAP:dict(color=[.458,.234,.157],roughness=.89),JOINT:dict(color=[.287,.130,.092],roughness=.96)}

def court(b,m,lod):
    def mapper(u,z,d):return (u,.62-d,z)
    def face(op,back,front,mat,name):b.prism(op,back,front,mapper,mat,'recessed stair bay/'+name)
    raw={'top window':[[423,118],[437,124],[441,174],[427,169]],'middle window':[[429,210],[443,210],[449,290],[434,285]],'ground narrow opening':[[431,341],[452,340],[456,360],[433,365]]}
    openings={}
    for name,pts in raw.items():
        v=[m.on_plane(p,1,.62)for p in pts]
        openings[name]=Polygon([(p[0],p[2])for p in v]).intersection(box(3.36,.05,5.47,11.14))
    wall=box(3.29,0,5.53,11.18).difference(unary_union(list(openings.values())))
    face(wall,-.34,-.005,m.WALL,'wall with vertically aligned recessed openings')
    face(wall.intersection(box(3.29,0,5.53,4.25)),0,.038,m.BELT,'banded ground floor')
    for key,op in openings.items():
        if not op.is_empty:m.joinery(face,op,key,lod)
    for i,(a,c,d) in enumerate([(3.87,3.94,.072),(4.17,4.25,.115),(10.95,11.09,.15),(11.09,11.21,.205)]):
        face(box(3.29,a,5.53,c),-.05,d,m.LINTEL,'recessed belt '+str(i+1))
    # The sliver of return reveals the offset between the parapet and stair bay in the 2011 and 2015 photographs.
    b.prism(box(-.11,0,.62,11.16),-.31,0,lambda u,z,d:(3.29+d,u,z),m.WALL,'recessed stair bay/parapet return')
    return b

def roof(b,m,lod):
    s=m.street_control
    def px(x,y):return s.final_xyz((x,y,0))[:2]
    def xyz(x,y,z):return (*px(x,y),z)
    control=json.loads((Path(__file__).absolute().parents[1]/'measurements/roof-and-register.json').read_bytes())
    peak=control['sensitivity_to_roof_setback_m']['3.3']
    eave=s.P['roof_lip_height'];side=s.final_xyz((0,0,11.04))[2]
    left=px(5.53,-3.30)[0]-(s.P['west_to_east_eave_width']-s.P['waist_frontage_width'])/2
    right=left+s.P['west_to_east_eave_width'];front=px(0,-3.30)[1]-.16;back=px(0,12.70)[1]
    def roof_facet(verts,label,courses=True):
        q=np.array(verts,dtype=float)
        if np.cross(q[1]-q[0],q[2]-q[0])[2]<0:q=q[::-1]
        n=len(q);p=np.vstack((q-np.array([0,0,.115]),q))
        faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
        faces.extend((i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n))
        b.add(p,faces,TILE,'roof/'+label)
        if not courses:return
        edges=list(zip(q,np.roll(q,-1,axis=0)))
        for j,z in enumerate(np.arange(q[:,2].min()+.12,q[:,2].max()-.05,.43 if lod else .21)):
            cuts=[a+(c-a)*(z-a[2])/(c[2]-a[2]) for a,c in edges if (a[2]<=z<c[2])or(c[2]<=z<a[2])]
            if len(cuts)==2 and np.linalg.norm(cuts[1]-cuts[0])>.19:
                b.tube([p+[0,0,.004]for p in cuts],.020 if lod else .017,JOINT,5 if lod else 7,f'roof/{label}/tile lap {j+1}')
    a=(left,front,eave);d=(right,front,eave);e=(right,back,eave);h=(left,back,eave)
    v=tuple(peak);g=(v[0],back-3.15,v[2])
    roof_facet([a,d,v],'south hip seen from street')
    roof_facet([d,e,g,v],'east roof slope')
    roof_facet([e,h,g],'north hip behind main ridge')
    roof_facet([h,a,v,g],'west roof slope facing valley')
    x0=px(-1.32,0)[0]-.17;x1=left+.09
    yf=px(0,-.11)[1]+.12;yb=px(0,14.80)[1]
    cl=(x0,yf,side);cr=(x1,yf,side);br=(x1,yb,side);bl=(x0,yb,side)
    # A transverse break and two slopes behind the curved parapets are visible in all three roof surveys.
    r0=(x0+.88,yf+5.85,eave+1.83);r1=(x1-.83,yf+5.85,eave+1.83)
    roof_facet([cl,cr,r1,r0],'south-facing roof behind curved parapet')
    roof_facet([cl,r0,bl],'lane-side hip')
    roof_facet([cr,br,r1],'east hip at valley')
    roof_facet([br,bl,r0,r1],'rear slope behind lane ridge')
    for j,(f,t) in enumerate([(a,v),(d,v),(v,g),(g,e),(g,h),(cl,r0),(cr,r1),(r0,r1)]):
        b.tube([np.array(f)+[0,0,.04],np.array(t)+[0,0,.04]],.071,CAP,8 if lod else 12,'roof/rounded ridge '+str(j+1))
    # Undocumented far walls are plain backing, stopping at the interpreted eave line.
    for name,P,Q,high in [('east flank',d,e,eave),('rear wing',e,h,eave),('lane roof rear',br,bl,side)]:
        a1=np.array(P[:2]);v1=np.array(Q[:2])-a1;length=np.linalg.norm(v1);t=v1/length;n=np.array([t[1],-t[0]])
        def mapwall(u,z,depth):
            xy=a1+u*t+depth*n
            return (xy[0],xy[1],z)
        b.prism(box(0,.90,length,high-.095),-.31,-.06,mapwall,m.WALL,'plain unobserved extent/'+name)
    return b
