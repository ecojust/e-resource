"""Tiled front roof planes, two small dormers and the asymmetric gable over the stair bay."""
import math
import numpy as np
from shapely.geometry import Polygon,box
from photo_architecture import Facade,opening
from villa_joinery import DARK,WOOD,SECOND,BRICK,GLASS,LIMESTONE
from mineral_render import CAST
from projecting_bays import TILE,WORN_TILE,EAVE


def panel(b,quad,thick,mat,label):
    pts=[np.asarray(p,float)for p in quad]
    if np.cross(pts[1]-pts[0],pts[2]-pts[0])[2]<0:pts.reverse()
    bottom=[p-[0.,0.,thick]for p in pts];n=len(pts)
    faces=[tuple(range(n)),tuple(reversed(range(n,2*n)))]
    faces.extend((i,n+i,n+(i+1)%n,(i+1)%n)for i in range(n))
    b.add(pts+bottom,faces,mat,label)


def tiled_plane(b,at,width,run,lod,label):
    panel(b,[at(0,0),at(1,0),at(1,1),at(0,1)],.115,EAVE,label+'/support under boarding')
    rows=max(3,round(run/(.53 if lod else .365)))
    cols=max(4,round(width/(.45 if lod else .267)))
    for k in range(rows):
        offset=.48 if k%2 else 0
        v0=k/rows;v1=min(1,(k+1.105)/rows)
        for j in range(-1 if offset else 0,cols):
            u0=max(0,(j+offset+.012)/cols);u1=min(1,(j+1+offset-.012)/cols)
            if u1-u0<.004:continue
            grid=2 if lod else 4
            ts=np.linspace(u0,u1,grid+1)
            p=[];q=[]
            for i,t in enumerate(ts):
                curvature=.036*math.sin(math.pi*(i/grid))**2
                p.append(np.asarray(at(t,v0))+[0,0,.054+curvature])
                q.append(np.asarray(at(t,v1))+[0,0,.025+curvature*.76])
            hi=p+q;lo=[v-[0.,0.,.036]for v in hi];n=len(ts);faces=[]
            for i in range(n-1):
                faces.extend([(i,i+1,n+i+1,n+i),(2*n+i,3*n+i,3*n+i+1,2*n+i+1),
                              (i,2*n+i,2*n+i+1,i+1),(n+i+1,3*n+i+1,3*n+i,n+i)])
            faces.extend([(0,n,3*n,2*n),(n-1,3*n-1,4*n-1,2*n-1)])
            verts=hi+lo
            if np.cross(hi[1]-hi[0],hi[n]-hi[0])[2]<0:faces=[tuple(reversed(f))for f in faces]
            b.add(verts,faces,WORN_TILE if (j*3+k)%8==0 else TILE,label+'/overlapping pan tiles')


def small_dormer(b,x,w,ybase,lod,label):
    f=Facade(b,(x-w/2,ybase),(x+w/2,ybase),label);base=7.91;soff=8.45;ridge=8.98
    hole=box(-.39,base+.065,.39,soff-.055)
    gable=Polygon([(-w/2,base),(w/2,base),(w/2,soff),(0,ridge),(-w/2,soff)])
    f.prism(gable.difference(hole),-.23,0,CAST,'Small triangular dormer face')
    f.prism(hole,-.21,-.19,SECOND,'Recessed dark sash')
    f.prism(hole.difference(hole.buffer(-.044,join_style=2)),-.144,-.105,WOOD,'Window edge')
    f.box(0,base+.218,.031,.30,.045,-.111,WOOD,'Window division')
    f.box(0,base+.020,.93,.061,.14,.004,LIMESTONE,'Window sill')
    for side in (-1,1):
        xx=x+side*w/2
        panel(b,[(xx,ybase,soff),(x,ybase,ridge),(x,ybase+1.39,ridge),(xx,ybase+1.39,soff)],.115,TILE,label+'/pitched tiled hood')
        f.builder.tube([f.point(side*(w/2+.08),soff-.027,.091),f.point(0,ridge+.050,.091)],.077,
                       EAVE,6 if lod else 10,label+'/protruding verge')


def roof(b,d,lod,cross_face):
    x0=-7.61;x1=1.50;y0=-.23;y1=d['section_depth_m'];eave=d['flat_eave']
    def valley_x(z):
        return .85+(4.05-.85)*(z-7.60)/(d['cross_gable_ridge']-7.60)
    def flat(u,v):
        z=eave+(d['main_section_ridge']-eave)*v
        return (x0+(valley_x(z)+.045-x0)*u,y0+(y1-y0)*v,z)
    tiled_plane(b,flat,x1-x0,y1-y0,lod,'Roof/street slope')
    b.tube([(valley_x(eave),y0,eave+.079),(valley_x(d['main_section_ridge']),y1,d['main_section_ridge']+.08)],
           .044,EAVE,8 if lod else 12,'Roof/street slope valley')
    # The front cut ends at the first roof bay. The two little sashes remain independent.
    small_dormer(b,-3.82,1.53,1.07,lod,'Roof/left dormer')
    small_dormer(b,-.32,1.58,1.14,lod,'Roof/right dormer')
    a=.85;ridge=4.05;c=d['measured_u']['right_wall_under_front_eave']+.42
    y=-.41;front_eaves=[7.60,6.82];crest=d['cross_gable_ridge']
    for side,(edge,zedge)in enumerate(zip((a,c),front_eaves)):
        def pitch(u,v):
            return (edge+(ridge-edge)*v,y+(y1-y)*u,zedge+(crest-zedge)*v)
        tiled_plane(b,pitch,y1-y,math.hypot(ridge-edge,crest-zedge),lod,'Roof/cross gable '+str(side+1))
        xx=[edge,ridge];zz=[zedge,crest];dir=np.array([xx[1]-xx[0],zz[1]-zz[0]])
        length=np.linalg.norm(dir);nx,nz=(-dir[1]/length,dir[0]/length)
        points=[(xx[0],zz[0]),(xx[1],zz[1]),(xx[1]+.112*nx,zz[1]+.112*nz),(xx[0]+.112*nx,zz[0]+.112*nz)]
        # The roof verge extends beyond the plaster of the gable and casts a shadow.
        pf=Facade(b,(-.5,y),(.5,y),'Roof/cross gable')
        pf.prism(Polygon(points),-.061,.068,EAVE,'Dark under-verge')
        if not lod:
            n=round(length/.31)
            for j in range(n):
                t=(j+.5)/n
                pf.box(edge+(ridge-edge)*t,zedge+(crest-zedge)*t-.094,.091,.134,.13,.008,EAVE,'Rafter tails')
    vent=opening(ridge,7.78,1.28,.54,.50,20 if lod else 46)
    cross_face.prism(vent,-.22,-.205,DARK,'Attic/half-round glazing')
    cross_face.prism(vent.difference(vent.buffer(-.045,join_style=2)),-.157,-.106,WOOD,'Attic/arched bead')
    cross_face.box(ridge,8.035,.073,.51,.104,-.12,CAST,'Attic/centre pier')

