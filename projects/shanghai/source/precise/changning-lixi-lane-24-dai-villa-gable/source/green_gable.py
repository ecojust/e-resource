"""The concave gable, recessed attic casements and adjoining tile courses."""
import json
import numpy as np
from scipy.interpolate import PchipInterpolator
from shapely.geometry import Polygon, LineString, box
from shapely.ops import unary_union
from photo_architecture import Facade
from registration import HERE, wall

PROFILE=json.loads((HERE.parent/'measurements/green-gable-profile.json').read_bytes())
TRANSFER=np.array(PROFILE['district_to_street_gable_only'])
FRONT=-.48
GREEN='Weathered green roughcast'
TRIM='Grey green edge flashing'
CREAM='Buff stonework'
SASH='Painted green timber'
GLASS=['Attic glass in shade','Blue grey glass','Dark reflected glass']
TILES=['Clay tile ochre','Clay tile russet','Clay tile faded']
def to_gable(uv):
    a=np.atleast_2d(uv)
    h=np.column_stack([a,np.ones(len(a))])@TRANSFER.T
    return wall(h[:,:2]/h[:,2,None],FRONT)
def curves(lod):
    left=PROFILE['manual_left_curve']
    right=PROFILE['right_terminal_limits']+[[c['u'],c['v']]for c in PROFILE['training']]
    result=[]
    for anchors in (left,right):
        points=np.asarray(sorted(anchors,key=lambda a:a[1]));y=points[:,1]
        sample=np.unique(np.r_[np.linspace(y[0],y[-1],18 if lod else 56),y])
        result.append(to_gable(np.c_[PchipInterpolator(y,points[:,0])(sample),sample]))
    return result
def arch_outline():
    pts=to_gable(PROFILE['upper_arch'])
    # Retain the surveyed points as knots while smoothing the head.
    t=np.r_[0,np.linalg.norm(np.diff(pts,axis=0),axis=1).cumsum()]
    return Polygon(PchipInterpolator(t,pts)(np.unique(np.r_[t,np.linspace(0,t[-1],60)])))
def clipped_grid(face,aperture,lod):
    x0,z0,x1,z1=aperture.bounds
    opening=aperture.buffer(-.075,join_style=2)
    face.prism(aperture.difference(opening),-.33,-.040,SASH,'outer green arch frame')
    positions=[.16,.335,.53,.72,.875]
    bars=[box(x0+p*(x1-x0)-.020,z0-.1,x0+p*(x1-x0)+.020,z1+.1)for p in positions]
    for v,w in [(.33,.036),(.64,.050)]:
        z=z0+v*(z1-z0);bars.append(box(x0,z-w,x1,z+w))
    frame=opening.intersection(unary_union(bars))
    face.prism(frame,-.305,-.245,'Faded attic sash','transoms and mullions')
    panes=opening.difference(unary_union(bars))
    for n,pane in enumerate(sorted(panes.geoms,key=lambda p:(round(p.centroid.x,1),p.centroid.y))):
        face.prism(pane.buffer(.006,join_style=2),-.344,-.333,GLASS[(n//2+n%2)%3],'fixed attic pane '+str(n+1))
    # A shallow sill and plaster apron lie immediately below the window.
    apron=Polygon(to_gable([[149,263],[439,274],[438,357],[145,323]]))
    face.prism(apron,-.018,.012,'Attic apron in shade','plastered attic apron')
    sill=LineString(to_gable([[148,265],[440,275]])).buffer(.047,cap_style=2)
    face.prism(sill,-.012,.14,CREAM,'attic casement sill')
    for i,points in enumerate(([[146,264],[157,264],[154,325],[143,323]],[[427,274],[439,275],[440,358],[428,356]])):
        face.prism(Polygon(to_gable(points)),.013,.069,CREAM,'apron end '+str(i+1))
def roof(b,lod,sides):
    # The photographs show short terracotta slopes. Their depth ends at the section cut.
    for side,xz in enumerate(sides):
        name=('Left'if side==0 else'Right')+' roof'
        length=np.r_[0,np.linalg.norm(np.diff(xz,axis=0),axis=1).cumsum()]
        sample=PchipInterpolator(length,xz)
        def loc(t,y,h):
            x,z=sample(t);dx,dz=sample.derivative()(t);normal=np.array([-dz,dx])/np.hypot(dx,dz)
            if normal[1]<0:normal=-normal
            return [x+h*normal[0],y,z+h*normal[1]]
        nx=15 if lod else 21
        interval=np.linspace(0,length[-1],nx+1)
        for row,(t0,t1) in enumerate(zip(interval[:-1],interval[1:])):
            high=t0;low=min(t1+.035,length[-1])
            # Moulded clay tile cross section is consistent across each row, with a raised nose.
            stations=np.linspace(high,low,3); n=3 if lod else 6
            for col in range(6):
                ya=FRONT+.075+col*.226;yb=ya+.224
                ycoords=np.linspace(ya,yb,n+1);verts=[]
                for under in (True,False):
                    for j,t in enumerate(stations):
                        for k,y in enumerate(ycoords):
                            h=.018 if under else .042+.029*np.cos(k*np.pi/n)**4+.018*j/2
                            verts.append(loc(t,y,h))
                stride=n+1;sheet=3*stride
                faces=[]
                for j in range(2):
                    for k in range(n):
                        i=j*stride+k
                        faces.extend([(sheet+i,sheet+i+1,sheet+i+stride+1,sheet+i+stride),
                                      (i,i+stride,i+stride+1,i+1)])
                border=[*range(stride),2*stride-1,*range(3*stride-1,2*stride-1,-1),stride]
                for i,k in zip(border,np.roll(border,-1)):faces.append((i,k,sheet+k,sheet+i))
                if side==1:faces=[tuple(reversed(f))for f in faces]
                b.add(verts,faces,TILES[(row//3+col+side)%3],name+'/clay course '+str(row+1))
        f=Facade(b,(-.5,FRONT),(.5,FRONT),name)
        rim=LineString(xz).buffer(.043,cap_style=2,join_style=2)
        f.prism(rim,.007,.057,TRIM,'curved sheet edge')
    l,r=sides[0][0],sides[1][0]
    low=np.array([[l[0]-.06,FRONT-.06,l[1]+.046],[r[0]+.06,FRONT-.06,r[1]+.046],
                  [r[0]+.06,.96,r[1]+.046],[l[0]-.06,.96,l[1]+.046]])
    h=np.mean(low[:,2])+.29
    ridge=[[(l[0]+.68),.27,h],[(r[0]-.68),.27,h]]
    b.add([*low,*ridge],[(3,2,1,0),(0,1,5,4),(1,2,5),(2,3,4,5),(3,0,4)],TILES[1],'Hipped cap/four shallow slopes')
    for a,c in [(0,4),(1,5),(2,5),(3,4),(4,5)]:
        v=np.asarray([*low,*ridge]);b.tube(v[[a,c]]+[0,0,.018],.044,TILES[0],6 if lod else 10,'Hipped cap/ridge tiles')
    for i in range(1,4 if lod else 6):
        t=i/(4 if lod else 6);a=low[0]*(1-t)+np.array(ridge[0])*t;c=low[1]*(1-t)+np.array(ridge[1])*t
        b.tube([a+[0,0,.01],c+[0,0,.01]],.014,TILES[i%3],6,'Hipped cap/eaves courses')
def gable(b,lod):
    face=Facade(b,(-.5,FRONT),(.5,FRONT),'Street gable')
    left,right=curves(lod)
    jamb=Polygon(np.vstack([left[::-1],right]))
    aperture=arch_outline()
    assert jamb.is_valid and jamb.covers(aperture)
    face.prism(jamb.difference(aperture),-.24,0,GREEN,'render enclosing arched opening')
    clipped_grid(face,aperture,lod)
    roof(b,lod,[left,right])
    cap=LineString([left[0],right[0]]).buffer(.086,cap_style=2)
    face.prism(cap,-.25,.066,TRIM,'horizontal eaves board')
    eave=LineString([left[-1],right[-1]]).buffer(.04,cap_style=2)
    face.prism(eave,-.52,.016,'Cream soffit','projecting soffit')

def apron_details(b,lod):
    """Two sill boxes and exposed bracket ends visible beneath the attic in the 2018 view."""
    from registration import wall
    f=Facade(b,(-.5,FRONT),(.5,FRONT),'Attic apron')
    for i,(u,v,e,h)in enumerate([(236,226,327,249),(422,232,487,257)]):
        lo,hi=wall([[u,h],[e,v]],FRONT-.026)
        x0,z0=lo;x1,z1=hi;z1=max(z1,z0+.12)
        label='sill box '+str(i+1)
        # Planted trough seen edge-on. The first trough is darker than the frame under it.
        f.box((x0+x1)/2,(z0+z1)/2,x1-x0,z1-z0,.074,.204,'Attic apron in shade',label+' front')
        f.box((x0+x1)/2,z1-.024,x1-x0+.044,.052,.114,.207,CREAM,label+' front lip')
        for x in (x0+.025,x1-.025):
            f.box(x,(z0+z1)/2,.049,z1-z0,.225,.129,CREAM,label+' end')
        f.box((x0+x1)/2,z1-.058,x1-x0-.065,.023,.136,.112,'Trough soil',label+' planted bed')
    for j,u in enumerate([251,315,413,501]):
        x,z=wall([[u,309+(u-251)*.075]],FRONT)[0]
        # A stepped timber or painted metal bracket projects beyond the recessed wall.
        side=Facade(b,(x,-.5),(x,.5),'Attic brackets')
        prof=Polygon([[-.58,z+.014],[-.04,z+.014],[-.04,z-.262],[-.16,z-.242],[-.34,z-.16],[-.58,z-.102]])
        side.prism(prof,-.045,.045,'Attic bracket in shade','exposed bracket '+str(j+1))
