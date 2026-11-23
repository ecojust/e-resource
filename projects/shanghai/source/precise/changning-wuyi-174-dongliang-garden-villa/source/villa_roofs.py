"""Intersecting clay roofs, three dormers and brick stacks of the Wuyi villa."""
from math import hypot, pi
from pathlib import Path
import sys

import numpy as np
from shapely import set_precision
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

from wuyi_fabric import BRICK, FRAME, SOFFIT, STONE, TIMBER, WALL, CrownBuilder, PROJECT, SOURCE, glazing, paint, wall
sys.path.insert(0,str(PROJECT/'source/precise/changning-hongji-yuyuan-garden-houses-8-and-9/source'))
from hongji_roof_geometry import halfplane, pieces, roof_envelope, surface, triangular
from photo_architecture import Builder

TILE='174 | weathered interlocking clay tiles'
VERGE='174 | slate brown fascia'
GUTTER='174 | painted rainwater goods'
RIDGE='174 | ridge clay'
MORTAR='174 | stack mortar'
POT='174 | dark flue lining'
PALETTE={TILE:{'color':[1,1,1],'texture':str(SOURCE/'wuyi-clay-tiles.png'),'roughness':.88},
         VERGE:paint((101,89,86)),GUTTER:paint((68,68,67),.57,.18),
         RIDGE:paint((139,85,70)),MORTAR:paint((153,119,105)),POT:paint((52,47,44))}


class VillaBuilder(CrownBuilder):
    def add(self,vertices,faces,material='limestone',label='detail'):
        # The tile-course builder calculates UVs in the slope plane.
        if material==TILE:
            Builder.add(self,vertices,faces,material,label)
        else:
            super().add(vertices,faces,material,label)


def clay_finish(path):
    from PIL import Image
    size=256
    v,u=np.mgrid[0:size,0:size]
    rng=np.random.default_rng(5174)
    row=v//64
    across=u/64+(row%2)*.0625
    col=np.floor(across).astype(int)%4
    wave=across%1.
    phase=v%64/64.
    firing=np.array([[3,10,-2,6],[-5,4,7,-3],[4,-12,2,8],[3,-4,4,-7]])
    roll=9*np.cos(2*pi*wave)-8*np.exp(-((wave-.77)/.075)**2)
    lip=np.where(phase>.949,-25.,np.where(phase<.052,8.,0.))
    mineral=rng.normal(0,2.8,(size,size))+1.8*np.cos(2*pi*(u*2-v*5)/size)
    tone=roll+lip+mineral+firing[row,col]
    photo=np.clip(np.array([145,89,72])+tone[:,:,None]*np.array([1,.85,.74]),0,255).astype('uint8')
    Image.fromarray(photo).save(path,optimize=True)


NORTH_WING=[(7.12,1.62),(11.68,1.62),(12.82,2.94),(15.13,2.94)]
WALL_PLAN=Polygon([(0,0),(7.184,0),*NORTH_WING,(15.13,13.60),(0,13.60)])
RIDGE_X=3.57
NORTH_EAVE=-1.21

def clipped(plane,other):
    return halfplane(other[0]-plane[0],other[1]-plane[1],other[2]-plane[2])


def hip(zone,shape,planes):
    # At a hipped end, the lowest of the intersecting slopes forms the roof.
    faces=[]
    for i,p in enumerate(planes):
        area=shape
        for j,q in enumerate(planes):
            if i!=j:area=area.intersection(clipped(p,q))
        for part in pieces(area):
            if part.area>.002:faces.append((zone,part,p))
    return faces


def plane_skin(b,area,low,high,plane,material,label):
    a,c,k=plane
    for poly in pieces(set_precision(area,1e-6)):
        if poly.area>.0003:
            b.prism(poly,low,high,lambda x,y,t:(x,y,a*x+c*y+k+t),material,label)


def installed_roofs(b,facets,footprint,lod):
    panels=roof_envelope(facets)
    outline=unary_union([p for _,p,_ in panels])
    for name,patch,slope in panels:
        surface(b,patch,slope,TILE,name+' lapped clay courses',lod)
        plane_skin(b,patch.difference(footprint.buffer(-.012,join_style=2)),-.167,-.077,slope,SOFFIT,name+' continuous soffit boards')
        a,c,k=slope
        perimeter=patch.boundary.intersection(outline.boundary)
        for line in getattr(perimeter,'geoms',[perimeter]):
            if line.geom_type!='LineString':continue
            pts=list(line.coords)
            for p,q in zip(pts,pts[1:]):
                dx=q[0]-p[0];dy=q[1]-p[1];length=hypot(dx,dy)
                if length<.08:continue
                nx,ny=-dy/length,dx/length
                if outline.covers(Point((p[0]+q[0])/2+.02*nx,(p[1]+q[1])/2+.02*ny)):
                    nx,ny=-nx,-ny
                rim=Polygon([(x+s*nx,y+s*ny)for (x,y),s in [(p,.025),(q,.025),(q,-.05),(p,-.05)]])
                plane_skin(b,rim,-.178,.02,slope,VERGE,name+' fascia')
                if abs(a*dx+c*dy)<.05*length:
                    b.tube([(x+nx*.04,y+ny*.04,a*x+c*y+k-.137)for x,y in (p,q)],.055,GUTTER,7 if lod else 12,name+' gutter')
    for i,(_,first,p) in enumerate(panels):
        for _,second,q in panels[i+1:]:
            common=first.boundary.intersection(second.boundary)
            for line in getattr(common,'geoms',[common]):
                if line.geom_type!='LineString' or line.length<.18:continue
                v,w=line.coords[0],line.coords[-1]
                xm,ym=(v[0]+w[0])/2,(v[1]+w[1])/2
                if abs((p[0]-q[0])*xm+(p[1]-q[1])*ym+p[2]-q[2])>.025:continue
                t=second.representative_point()
                ridge=(p[0]-q[0])*(t.x-xm)+(p[1]-q[1])*(t.y-ym)>0
                b.tube([(x,y,p[0]*x+p[1]*y+p[2]+.018)for x,y in (v,w)],.074 if ridge else .036,
                       RIDGE if ridge else GUTTER,8 if lod else 12,'ridge tile joint' if ridge else 'folded valley flashing')


def dormer(b,x0,x1,front,back,sill,head,groups,hipped,lod,name):
    # Positive inward distance always points into the dormer, including on its garden side.
    north=back>front
    a,c=((x0,front),(x1,front)) if north else ((x1,front),(x0,front))
    width=x1-x0;edge=.215;gap=.19
    span=(width-2*edge-gap*(len(groups)-1))/len(groups)
    cuts=[box(edge+i*(span+gap),sill,edge+i*(span+gap)+span,head)for i in range(len(groups))]
    wall(b,box(0,sill-.20,width,head+.18).difference(unary_union(cuts)),a,c,0,.16,WALL,name+' window wall')
    for i,(opening,cols) in enumerate(zip(cuts,groups)):
        glazing(b,opening,a,c,.065,name+' sash '+str(i+1),cols,2)
    iy=1 if north else -1
    for ix in (x0,x1):
        lengths=abs(back-front)
        height_back=head+.04 if hipped else head+.12
        cheek=Polygon([(0,sill-.18),(lengths,head-.17),(lengths,height_back),(.001,head+.15)])
        pivot=(ix,front);end=(ix,back)
        wall(b,cheek,pivot,end,-.064,.064,TIMBER,name+' boarding return')
    if hipped:
        cap=box(x0-.26,min(front-.32*iy,back),x1+.26,max(front-.32*iy,back));lo,fy,hi,by=cap.bounds
        h=head+.18;s=.77
        planes=[(s,0.,h-s*lo),(-s,0.,h+s*hi),(0.,s*iy,h-s*iy*(front-.32*iy))]
        installed_roofs(b,hip(name+' hip cap',cap,planes),box(x0,min(back,front),x1,max(front,back)),lod)
    else:
        cap=box(x0-.28,min(front-.36*iy,back),x1+.28,max(front-.36*iy,back))
        plane=(0.,.085*iy,head+.24-.085*iy*front)
        plane_skin(b,cap,-.14,-.055,plane,SOFFIT,name+' pale dormer soffit')
        plane_skin(b,cap,-.055,.04,plane,VERGE,name+' shallow projecting cap')
        for x in (x0+.08,x1-.08,(x0+x1)/2):
            b.tube([(x,front-.015*iy,head-.17),(x,front-.28*iy,head+.10)],.035,TIMBER,6,name+' exposed eave stay')


def chimney(b,x,y,width,depth,low,top,count,lod,name):
    # Surface bonds on four walls, a stepped shoulder, and open square throats.
    shaft=box(x-width/2,y-depth/2,x+width/2,y+depth/2)
    b.plan_prism(shaft,low,top-.59,MORTAR,name+' brick core')
    for side,(a,c) in enumerate(zip(list(shaft.exterior.coords),list(shaft.exterior.coords)[1:])):
        length=hypot(c[0]-a[0],c[1]-a[1]);course=.126 if lod else .086
        rows=int((top-.59-low)/course)
        if rows<1:continue
        step=(top-.59-low)/rows
        for r in range(rows):
            z=low+r*step;offset=-.112 if r%2 else 0.
            rects=[]
            while offset<length:
                l=max(.003,offset+.003);right=min(length-.003,offset+.219)
                if right>l+.008:rects.append(box(l,z+.005,right,z+step-.003))
                offset+=.225
            wall(b,unary_union(rects),a,c,-.009,.003,BRICK,name+' stretcher bond')
    b.plan_prism(shaft.buffer(.057,join_style=2),top-.59,top-.48,BRICK,name+' stepped collar')
    spacing=width/count
    for i in range(count):
        mid=x-width/2+spacing*(i+.5)
        outer=box(mid-spacing*.45,y-depth*.45,mid+spacing*.45,y+depth*.45)
        throat=outer.buffer(-.082,join_style=2)
        b.plan_prism(outer.difference(throat),top-.48,top-.11,BRICK,name+' flue wall')
        b.plan_prism(outer.buffer(.033,join_style=2).difference(throat),top-.11,top,BRICK,name+' projecting flue cap')
        b.plan_prism(throat,top-.49,top-.46,POT,name+' recessed flue')


def add_roofs(b,lod):
    facets=triangular('north and garden gables','x',(-.71,RIDGE_X,7.66),(NORTH_EAVE,14.30),5.84,10.54)
    wing=box(5.08,-.65,15.78,14.24)
    north_eave=6.32;south_eave=5.10;crest=9.99;spine=7.52
    s=(crest-north_eave)/(spine+.65);t=(crest-south_eave)/(14.24-spine)
    facets+=hip('west cross wing',wing,[(0,s,north_eave+s*.65),(0,-t,south_eave+t*14.24),
                                        (-.98,0,north_eave+.98*15.78)])
    # The garden dormers cut through the common slope. In front of each sash
    # a short tiled apron connects its lower sill to the uninterrupted eave.
    # Their visible fronts and aprons are separately identifiable in photo 00.
    apron_faces=[]
    for lo,hi,front,back,sill in [(11.10,12.91,11.98,9.29,6.37),(6.82,9.93,12.05,9.04,6.10)]:
        cut=box(lo-.018,back,hi+.018,14.24+.002)
        facets=[(n,shape.difference(cut),plane) if n=='west cross wing' else (n,shape,plane)
                for n,shape,plane in facets]
        slope=(sill-.075-south_eave)/(14.24-front)
        apron_faces.append(('garden dormer apron',box(lo-.018,front,hi+.018,14.24),
                            (0.,-slope,south_eave+slope*14.24)))
    installed_roofs(b,facets+apron_faces,WALL_PLAN,lod)
    dormer(b,8.13,12.39,.57,5.00,7.18,8.35,[2,3],False,lod,'street dormer')
    dormer(b,11.10,12.91,11.98,9.29,6.37,7.34,[3],False,lod,'small garden dormer')
    dormer(b,6.82,9.93,12.05,9.04,6.10,7.07,[2,2],True,lod,'hipped garden dormer')
    chimney(b,3.54,1.28,.55,.58,10.14,11.63,1,lod,'gable ridge chimney')
    chimney(b,8.34,7.30,1.49,.70,9.26,11.35,3,lod,'triple flue wing chimney')
    chimney(b,14.17,8.76,.43,.48,7.20,9.04,1,lod,'garden west chimney')


if __name__=='__main__':
    clay_finish(SOURCE/'wuyi-clay-tiles.png')
