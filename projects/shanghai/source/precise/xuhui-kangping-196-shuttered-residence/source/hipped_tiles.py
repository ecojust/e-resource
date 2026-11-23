"""Streetward tile slopes and two hip margins constrained by the two red roof silhouettes."""
from math import pi,sin
from shapely.geometry import Polygon,box
from shapely.geometry.polygon import orient
from materials import RIDGE,ROOF

def tile(f,facet,axis,lo,hi,height,lod,material,label):
    sections=4 if lod else 8
    vertices=[];indices={};faces=[];edges={}
    def vertex(x,y):
        p=(round(x,8),round(y,8))
        if p not in indices:
            indices[p]=len(vertices)
            wave=.038*sin(pi*(p[axis]-lo)/(hi-lo))
            vertices.append(f.point(*p,height(*p)+wave))
        return indices[p]
    for j in range(sections):
        u,v=(lo+(hi-lo)*k/sections for k in (j,j+1))
        strip=box(u,-100,v,100) if axis==0 else box(-100,u,100,v)
        section=facet.intersection(strip)
        if section.area<1e-8:continue
        ring=[vertex(x,y) for x,y in list(orient(section,sign=1.).exterior.coords)[:-1]]
        faces.append(tuple(ring))
        for a,b in zip(ring,ring[1:]+ring[:1]):
            if (b,a) in edges:del edges[b,a]
            else:edges[a,b]=True
    n=len(vertices)
    if not n:return
    vertices.extend([(x,y,z-.035) for x,y,z in vertices[:]])
    faces+= [tuple(k+n for k in reversed(face)) for face in faces[:]]
    faces+= [(b,a,a+n,b+n) for a,b in edges]
    f.b.add(vertices,faces,material,label)

def tile_roof(f,x0,x1,d0,d1,z,slope,hip,lod,label):
    inset=(d1-d0)*hip
    if 2*inset>=x1-x0:raise ValueError('The two hip margins must meet behind the photographed pitch.')
    lf,rf=(x0,d0),(x1,d0);lr,rr=(x0+inset,d1),(x1-inset,d1)
    panels=[('front',0,Polygon([lf,rf,rr,lr]),lambda x,d:z+(d-d0)*slope),
            ('left hip',1,Polygon([lf,lr,(x0,d1)]),lambda x,d:z+(x-x0)*slope/hip),
            ('right hip',1,Polygon([rf,(x1,d1),rr]),lambda x,d:z+(x1-x)*slope/hip)]
    for name,axis,facet,height in panels:
        xmin,ymin,xmax,ymax=facet.bounds
        a,b=(xmin,xmax) if axis==0 else (ymin,ymax)
        n=max(1,round((b-a)/(.25 if lod else .192)))
        width=(b-a)/n
        for i in range(n):
            tile(f,facet,axis,a+i*width,a+(i+1)*width,height,lod,
                 RIDGE if i%9==4 else ROOF,label+' | '+name+' tile pans')
        for i in [1,2,3]:
            lo=d0+i*.62 if axis==0 else x0+i*.62*hip if name=='left hip' else x1-i*.62*hip
            strip=box(-100,lo,100,lo+.035) if axis==0 else box(lo,-100,lo+.035,100)
            clip=facet.intersection(strip)
            if clip.area>.0001:
                f.b.prism(clip,.032,.052,lambda x,d,t:f.point(x,d,height(x,d)+t),ROOF,label+' | '+name+' transverse overlap')
    for name,(x,d),(u,v) in [('left',lf,lr),('right',rf,rr)]:
        f.rail([(x,d,z+.037),(u,v,z+slope*(d1-d0)+.037)],.037,RIDGE,label+' | '+name+' hip cap',6 if lod else 10)
