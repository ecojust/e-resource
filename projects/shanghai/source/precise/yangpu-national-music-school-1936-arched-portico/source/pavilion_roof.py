"""Four sloping tile fields and exposed fascia of the historic music-school pavilion."""
import numpy as np
from shapely.geometry import box

TILE='Grey roof tile';PALE='Weathered tile';FASCIA='Shadowed timber fascia';LIP='Edge of tile'

def prism(builder,points,normal,depth,material,label):
    upper=np.asarray(points);lower=upper-np.asarray(normal)*depth;n=len(points)
    faces=[tuple(range(n)),tuple(reversed(range(n,2*n)))]
    faces.extend((j+n,(j+1)%n+n,(j+1)%n,j) for j in range(n))
    builder.add([*upper,*lower],faces,material,label)

def build(builder,roof,lod):
    l,f,z=roof['left_front_eave_xyz'];r,b,_=roof['right_rear_eave_xyz'];top=np.array(roof['apex_xyz'])
    corners=[np.array(v) for v in [(l,f,z),(r,f,z),(r,b,z),(l,b,z)]]
    outline=box(l,f,r,b)
    for label,za,zb,inset,mat in [('lower eave fascia',z-.18,z-.095,.075,FASCIA),('projecting eave nosing',z-.095,z-.045,.018,LIP),
                                  ('tile edge bed',z-.045,z,.008,FASCIA)]:
        builder.plan_prism(outline.buffer(-inset,join_style=2),za,zb,mat,'Roof/'+label)
    for idx,first in enumerate(corners):
        last=corners[(idx+1)%4];normal=np.cross(last-first,top-first);normal/=np.linalg.norm(normal)
        assert normal[2]>0
        name='Hip '+str(idx+1);prism(builder,[first,last,top],normal,.070,TILE,name+'/continuous slope')
        # Shallow convex tile beds taper in plan as the hip narrows. They stop
        # below the crest, so no zero-length tiles meet at a single vertex.
        nrows=10 if lod else 19;wide=.59 if lod else .33
        for j in range(nrows):
            t0=j/nrows;t1=min(.973,(j+1)/nrows-.0021)
            a=(1-t0)*first+t0*top;c=(1-t0)*last+t0*top
            aa=(1-t1)*first+t1*top;cc=(1-t1)*last+t1*top
            length=np.linalg.norm(c-a);nt=max(1,int(np.ceil(length/wide)))
            split=[0.,*[(k+(.5 if j%2 else 0))/nt for k in range(0 if j%2 else 1,nt) if .06<(k+(.5 if j%2 else 0))/nt<.94],1.]
            for k,(u,v) in enumerate(zip(split,split[1:])):
                gap=min(.0015,.05*(v-u));lo=u+gap;hi=v-gap;mid=(u+v)/2
                line=lambda p,q,h,t:p*(1-t)+q*t+normal*h
                verts=[line(a,c,.015,lo),line(a,c,.025,mid),line(a,c,.015,hi),
                       line(aa,cc,.003,lo),line(aa,cc,.012,mid),line(aa,cc,.003,hi)]
                # Side closures and the back are joined to the preceding course by the roof bed.
                verts.extend([point-normal*.017 for point in verts])
                triangles=[(0,1,4,3),(1,2,5,4),(6,9,10,7),(7,10,11,8),(0,6,7,1),
                           (1,7,8,2),(2,8,11,5),(5,11,10,4),(4,10,9,3),(3,9,6,0)]
                builder.add(verts,triangles,PALE if (j*5+k+idx)%7==0 else TILE,name+'/tile course '+str(j+1))
        edge=np.linspace(first,top,6 if lod else 12)
        for j,(a,b) in enumerate(zip(edge,edge[1:])):
            builder.tube([a+[0,0,.045],b+[0,0,.045]],.059,LIP,7 if lod else 12,label=name+'/hip caps')
