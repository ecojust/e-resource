"""Curved projecting balcony, moulded slab, two stone brackets and open iron balustrade."""
import numpy as np
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient
from photo_plane import pixel,position
from frontage import CREAM,SHADOW,IRON

# Sampled from the corrected photograph. The middle bows toward the street and
# the short side on the right runs back to the wall. Z is read anew at each assumed Y.
FRONT=[(132,260,-.64),(171,259,-.65),(191,251,-.78),(219,244,-.92),(250,244,-.98),
       (279,248,-.974),(309,254,-.89),(338,259,-.738),(373,258,-.65)]
def read_vertex(u,v,y):
    u=468+u*322/560;v=390+v*222/386
    original=pixel((u/60-10.4,0,22.35-v/60))
    return position(*original,y)
def slab(b,label,boundary,top,bottom,mat):
    pts=np.asarray(orient(Polygon(boundary),sign=1).exterior.coords[:-1]);n=len(pts)
    verts=[[*p,z] for z in (bottom,top) for p in pts];faces=[list(reversed(range(n))),list(range(n,2*n))]
    faces.extend([[i,(i+1)%n,n+(i+1)%n,n+i]for i in range(n)])
    b.add(verts,faces,mat,label)
def add_balcony(b,lod):
    front=np.asarray([read_vertex(*pt)for pt in FRONT])
    z=np.median(front[:,2]);xy=front[:,:2]
    left,right=xy[0,0],xy[-1,0]
    boundary=[*xy,[right,.024],[left,.024]]
    for j,(inset,lo,hi,mat) in enumerate(((.018,-.175,-.105,SHADOW),(0,-.105,-.037,CREAM),(.03,-.037,0,CREAM))):
        outer=Polygon(boundary).buffer(inset,join_style='mitre')
        slab(b,'Balcony curved ledge '+str(j+1),list(outer.exterior.coords)[:-1],z+hi,z+lo,mat)
    path=np.asarray([[left,-.05],*xy,[right,-.05]])
    dv=np.diff(path,axis=0);norms=np.linalg.norm(dv,axis=1);s=np.r_[0.,np.cumsum(norms)]
    def point(dist,height):
        i=min(max(0,np.searchsorted(s,dist,side='right')-1),len(dv)-1)
        return np.r_[path[i]+dv[i]*(dist-s[i])/norms[i],height]
    top=z+.82
    for h,r in [(z+.065,.021),(top-.082,.017),(top,.034)]:
        b.tube([np.r_[p,h] for p in path],r,IRON,6 if lod else 10,'Balcony continuous rails')
    divisions=max(15,round(s[-1]/.128))
    for i in range(divisions+1):
        at=i*s[-1]/divisions
        b.tube([point(at,z+.016),point(at,top)],.018 if i%4==0 else .012,IRON,5 if lod else 8,'Balcony railing stiles')
        if i%2==0 and i<divisions:
            extent=s[-1]/divisions
            for half in (1,-1):
                curve=[point(at+extent*(.50+.42*half*np.sin(t)),z+.411+.30*np.cos(t))for t in np.linspace(0,np.pi,7 if lod else 13)]
                b.tube(curve,.009,IRON,4 if lod else 6,'Balcony pierced iron loops')
    for i,x in enumerate((left+.17,right-.16)):
        outline=[[-.652,z-.145],[-.48,z-.34],[-.18,z-.51],[-.02,z-.57],[.015,z-.16]]
        poly=orient(Polygon(outline),sign=1)
        p=np.array(poly.exterior.coords[:-1]);n=len(p);vs=[[u,*q] for u in (x-.08,x+.08)for q in p]
        faces=[list(reversed(range(n))),list(range(n,2*n))]+[[j,(j+1)%n,n+(j+1)%n,n+j]for j in range(n)]
        b.add(vs,faces,SHADOW,'Balcony curved stone bracket '+str(i+1))
