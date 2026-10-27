"""Explicit planar roof intersections. Hidden north hip is an estimate, not a survey."""
import math
import numpy as np
from shapely.geometry import Polygon, box
from shapely.geometry.polygon import orient
from shapely import constrained_delaunay_triangles

def clip(poly, a,b,c, keep_negative=True):
    pts=list(poly.exterior.coords)[:-1]; out=[]
    sg=1 if keep_negative else -1
    for p,q in zip(pts,pts[1:]+pts[:1]):
        dp=sg*(a*p[0]+b*p[1]+c);dq=sg*(a*q[0]+b*q[1]+c)
        if dp<=1e-10:out.append(p)
        if (dp<-1e-10 and dq>1e-10) or (dp>1e-10 and dq<-1e-10):
            t=dp/(dp-dq);out.append((p[0]+t*(q[0]-p[0]),p[1]+t*(q[1]-p[1])))
    if len(out)<3:return Polygon()
    return Polygon([(round(x,10),round(y,10)) for x,y in out])

def prepare_roof(W,D,H):
    h=W/2;oh=H['roof_overhang'];k=H['roof_knee_x'];nf=D/2+H['entry_bay_projection']
    xs=[-h-oh,-h,-k,0,k,h,h+oh]
    zs=[H['garden_eave']-.15,H['garden_eave'],H['garden_roof_knee'],H['garden_ridge'],H['garden_roof_knee'],H['garden_eave'],H['garden_eave']-.15]
    def south_profile(x):return float(np.interp(x,xs,zs))
    hp=(0.,-.6,H['entry_eave']+.6*nf)
    def height(x,y):return min(south_profile(x),hp[1]*y+hp[2])
    patches=[]
    for i,(x0,x1,z0,z1) in enumerate(zip(xs,xs[1:],zs,zs[1:])):
        a=(z1-z0)/(x1-x0);gp=(a,0.,z0-a*x0);p=box(x0,-D/2-oh,x1,D/2+oh)
        diff=np.array(gp)-np.array(hp)
        for iship,negative in [(False,True),(True,False)]:
            q=clip(p,*diff,keep_negative=negative)
            if q.area>1e-9:
                patches.append({'id':f'{"north-hip" if iship else "gambrel"}-{i}', 'plane':hp if iship else gp,'polygon':q,'is_hip':iship})
    return {'patches':patches,'height':height,'south_profile':south_profile,'bounds':(-h-oh,-D/2-oh,h+oh,D/2+oh),'half':h,'depth':D,'northfront':nf}

def add_roof(b, roof):
    contract={'schema':'bajin-roof-planar-v1','hidden_north_hip':'Estimated intersection; not surveyed','formula':'min(piecewise gambrel(x), 9.6 - .6*(y-northfront))','northfront_m':roof['northfront'],'patches':[],'tiles':{'width_m':.28,'pitch_m':.30,'length_m':.36,'seam_m':.006,'thickness_m':.018,'overlap_wedge_slope':.06,'not_measured_tile_dimensions':True}}
    for p in roof['patches']:
        a,bb,c=p['plane'];poly=orient(p['polygon'],sign=1);pid=p['id']
        for tri in constrained_delaunay_triangles(poly).geoms:
            xy=list(orient(tri,sign=1).exterior.coords)[:3]
            top=[(x,y,a*x+bb*y+c) for x,y in xy]
            bot=[(x,y,a*x+bb*y+c-.08) for x,y in xy]
            b.add(top,[(0,1,2)],'estimated plain tile roof',f'roof-structure/{pid}/top')
            b.add(bot,[(2,1,0)],'white trim',f'roof-structure/{pid}/soffit')
        # Only the roof's outside perimeter is capped. No duplicated seam caps.
        xy=list(poly.exterior.coords)
        for q,r in zip(xy,xy[1:]):
            xmin,ymin,xmax,ymax=roof['bounds']
            if any(abs(q[axis]-val)<1e-8 and abs(r[axis]-val)<1e-8 for axis,val in [(0,xmin),(0,xmax),(1,ymin),(1,ymax)]):
                verts=[(q[0],q[1],a*q[0]+bb*q[1]+c-.08),(r[0],r[1],a*r[0]+bb*r[1]+c-.08),(r[0],r[1],a*r[0]+bb*r[1]+c),(q[0],q[1],a*q[0]+bb*q[1]+c)]
                b.add(verts,[(0,1,2,3)],'green painted frame',f'roof-structure/{pid}/outside-fascia')
        n=np.array([-a,-bb,1.]);n/=np.linalg.norm(n)
        u=np.array([1.,0,0]) if p['is_hip'] else np.array([0.,-1. if a<0 else 1.,0.])
        v=np.cross(n,u);origin=np.array([0.,0.,c])
        surface=[np.array([x,y,a*x+bb*y+c]) for x,y in xy[:-1]]
        uv=Polygon([(np.dot(q-origin,u),np.dot(q-origin,v)) for q in surface]);uv=orient(uv,sign=1)
        ux,vy,ux1,vy1=uv.bounds;count=0
        for row in range(math.floor(vy/.30)-1,math.ceil(vy1/.30)+1):
            rowv=row*.30
            for col in range(math.floor(ux/.28)-1,math.ceil(ux1/.28)+1):
                shape=uv.intersection(box(col*.28+.003,rowv,(col+1)*.28-.003,rowv+.36))
                if shape.is_empty or shape.area<.00004:continue
                polys=[shape] if shape.geom_type=='Polygon' else list(shape.geoms)
                for si,pp in enumerate(polys):
                    if pp.geom_type!='Polygon' or pp.area<.00004:continue
                    pp=orient(pp,sign=1);coords=list(pp.exterior.coords)[:-1]
                    verts=[]
                    for dh in [0,.018]:
                        for uu,vv in coords:
                            verts.append(origin+u*uu+v*vv+n*(.001+.06*(vv-rowv)+dh))
                    countv=len(coords);faces=[tuple(reversed(range(countv))),tuple(range(countv,2*countv))]
                    faces += [(i,(i+1)%countv,(i+1)%countv+countv,i+countv) for i in range(countv)]
                    tone=(row*31+col*17+len(pid))%5
                    b.add(verts,faces,f'flat tile tone {tone}',f'flat-tiles/{pid}/{row}/{col}/{si}')
                    count+=1
        contract['patches'].append({'plane_id':pid,'equation_z_ax_by_c':list(p['plane']),'polygon_architecture_XY':list(poly.exterior.coords)[:-1],'normal_architecture_XYZ':n.tolist(),'course_u':u.tolist(),'downhill_v':v.tolist(),'tile_count':count,'all_surface_triangles_coplanar':True})
    return contract
