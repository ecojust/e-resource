"""Two brick rings, splayed cheeks and the stretcher-bond intrados in the No.16 porch."""
import numpy as np
from shapely.geometry import Polygon,box
from photo_architecture import Facade,opening
from registration import C,HERE,plane,wall
import json
V=json.loads((HERE.parent/'measurements/vault-profile.json').read_bytes())
CONIC=np.array(V['conic_parameters']);FRONT=C['outer_front_y_m']
FLOOR=-1.425
CX,CZ,RX,RZ,TILT=CONIC
BACK=float(plane([[390,153]],2,CZ+RZ)[0,1])
STONES=['Salmon facing brick','Dusty red brick','Weathered orange brick','Dark russet brick']
MORTAR='Lime mortar'
PLUM='Dark brick in the vault'
JOINT='Grey brown vault joint'
WOOD='Oxide red moulded timber'
def ellipse(t,rx,rz,cx=CX,cz=CZ,tilt=TILT):
    t=np.atleast_1d(t)
    return np.stack([cx+rx*np.cos(t),cz+rz*np.sin(t)+tilt*np.cos(t)],axis=1)
def sector(t0,t1,ri,ro,geom,count):
    cx,cz,rx,rz,slant=geom
    t=np.linspace(t0,t1,count)
    return Polygon(np.vstack([ellipse(t,rx+ro,rz+ro,cx,cz,slant),ellipse(t[::-1],rx+ri,rz+ri,cx,cz,slant)]))
def solid_arc(face,a,b,inside,outside,geom,count,back,front,material,label):
    shape=sector(a,b,inside,outside,geom,count)
    face.prism(shape,back,front,material,label)
def transverse(face,bottom,top,start,end,brick_height,length,materials,label,lod):
    """Brick courses with real recessed joints. Last brick in each row is cut at the cheek."""
    face.prism(box(start,bottom,end,top),-.135,-.009,MORTAR,label+' mortar bed')
    count=int(np.ceil((top-bottom)/brick_height))
    for j in range(count):
        z=bottom+j*brick_height;h=min(top,z+brick_height)-z
        if h<.006:continue
        pts=[start,*np.arange(start+length*(.5 if j%2 else 1),end-.01,length),end]
        for k,(a,c)in enumerate(zip(pts,pts[1:])):
            if c-a<.013:continue
            face.prism(box(a+.0028,z+.0026,c-.0028,z+h-.0026),-.012,.0015,materials[(j+2*k)%len(materials)],label+' brick course '+str(j+1))
def brickwork(b,lod):
    def facade(y,name):return Facade(b,(-.5,y),(.5,y),name)
    main=facade(FRONT,'Outer arch')
    joint=JOINT
    # Small mortar gaps in the vault leave a continuous, slightly recessed reveal surface.
    stone_depth=.232
    solid_arc(main,0,np.pi,.011,stone_depth-.009,CONIC,65 if lod else 145,-(BACK-FRONT),-.009,joint,'continuous arch bed')
    solid_arc(main,0,np.pi,.002,stone_depth-.010,CONIC,65 if lod else 145,-.036,-.003,'Pale face mortar','lime bed behind the front voussoirs')
    candidates=sorted([np.deg2rad(k['degrees'])for k in V['radial_mortar_observations']])
    posts=[0.]
    for t in candidates:
        if t-posts[-1] <np.deg2rad(2.0):continue
        while t-posts[-1]>np.deg2rad(5.1):posts.append(posts[-1]+np.deg2rad(3.1))
        posts.append(t)
    for t in [np.deg2rad(175.),np.deg2rad(177.6),np.pi]:
        if t-posts[-1]>.025:posts.append(t)
    posts[-1]=np.pi
    for j,(a,c)in enumerate(zip(posts[:-1],posts[1:])):
        mid=(a+c)/2
        # Four raised keys interrupt the extrados; the ridge at the crown spans three radial units.
        key=any(lo<np.degrees(mid)<hi for lo,hi in [(20,27),(57,66),(84.5,93.5),(118,127),(151,159)])
        outer=stone_depth+(.076 if key else 0.)
        ends=[0.,outer] if j%3 else [0.,outer*.52,outer]
        for k,(ri,ro)in enumerate(zip(ends[:-1],ends[1:])):
            solid_arc(main,a+.0034,c-.0034,ri+(.002 if k else 0),ro-.0015,CONIC,3 if lod else 5,
                      -.064,.015 if key else .001,STONES[(j//3+2*k)%4],'shaped facing brick '+str(j+1))
    # Staggered longitudinal joints visible on the shaded barrel.
    intervals=np.linspace(FRONT+.061,BACK,7)
    for row,(y0,y1)in enumerate(zip(intervals[:-1],intervals[1:])):
        f=facade(y0,'Vault soffit')
        t0=posts if row%2==0 else [0.,*[(a+c)/2 for a,c in zip(posts[:-1],posts[1:])],np.pi]
        for col,(a,c)in enumerate(zip(t0[:-1],t0[1:])):
            if c-a<.01:continue
            solid_arc(f,a+.0016,c-.0016,.0007,.016,CONIC,3 if lod else 4,-(y1-y0)+.002,-.002,
                      [PLUM,'Shaded salmon soffit','Muted brick soffit'][(row+col//4)%3],'soffit row '+str(row+1))
    # Rear wall and carved wooden architrave are separate from the leading masonry.
    back=facade(0,'Inner doorway')
    door=opening(0,FLOOR+.012,1.08,-FLOOR-.012+.562,.562,36 if lod else 72)
    surround=door.buffer(.116,join_style=2)
    shell=box(-.87,FLOOR,.875,1.125)
    back.prism(shell.difference(surround),-.17,-.012,'Mortar on inner wall','door wall with opening')
    # Carve each rectangular bed around the brick relieving arch.
    masonry=surround.buffer(.155,join_style=2)
    for j,z in enumerate(np.arange(FLOOR,1.125,.059)):
        pts=[-.87,*np.arange(-.87+.215*(.5 if j%2 else 1),.869,.215),.875]
        for i,(xa,xb)in enumerate(zip(pts[:-1],pts[1:])):
            if xb-xa<.01:continue
            shape=box(xa+.003,z+.003,xb-.003,min(z+.055,1.125)).difference(masonry)
            if shape.area>.00012:back.prism(shape,-.022,-.001,STONES[(j//4+i)%4],'cut running bond '+str(j+1))
    arch=(.0,.0,.54,.562,.0)
    for i in range(41):
        solid_arc(back,i*np.pi/41+.0024,(i+1)*np.pi/41-.0024,.118,.264,arch,3 if lod else 5,
                  -.051,.005,STONES[(i//4)%4],'inner brick voussoirs')
    for sign in [-1,1]:
        transverse(back,FLOOR,-.002,min(sign*.655,sign*.798),max(sign*.655,sign*.798),.059,.22,STONES,'inner jamb '+str(sign),lod)
    for j,(r0,r1,d,mat) in enumerate([(.0,.026,.030,'Red frame shadow'),(.024,.053,.049,WOOD),(.050,.073,.035,'Red frame shadow'),(.071,.095,.061,WOOD),(.092,.116,.039,'Red faded door trim')]):
        shape=door.buffer(r1,join_style=2).difference(door.buffer(r0,join_style=2)).intersection(box(-.80,FLOOR, .80,1))
        back.prism(shape,-.115,d,mat,'moulded wood ring '+str(j+1))
    origins=np.array(C['wall_corners_xy'])
    for side,(rear,front) in enumerate([(origins[0],origins[1]),(origins[2],origins[3])]):
        forward=(front,rear) if side==0 else (rear,front)
        cheek=Facade(b,*forward,'Left reveal'if side==0 else'Right reveal')
        transverse(cheek,FLOOR,.057,-cheek.length/2,cheek.length/2,.060,.207,STONES,'brick side wall',lod)
        # Above the impost the cheek continues back to the higher rear soffit.
        cut=Polygon([[0,.051],[1,.051],[1,1.16],[.0,.071]])
        def uz(t):return (-.5+t if side==0 else .5-t)*cheek.length
        wedge=Polygon([[uz(a),z]for a,z in cut.exterior.coords])
        cheek.prism(wedge,-.13,-.004,STONES[1],'side spandrel')
        # The outer piers are visibly wider than the sides of the vault.
        inner=ellipse(0 if side else np.pi,RX,RZ)[0][0];outer=inner+(.54 if side else -.51)
        cap=.034 if side else .077
        a,c=sorted([inner,outer]);pier=facade(FRONT,'Right pier'if side else'Left pier')
        transverse(pier,FLOOR,cap-.195,a,c,.059,.208,STONES,'horizontal beds',lod)
        pier.prism(box(a-.016,cap-.195,c+.016,cap-.150),-.20,.039,'Terracotta impost edge','lower impost slab')
        for i in range(6):
            pier.prism(box(a+i*(c-a)/6+.003,cap-.150,a+(i+1)*(c-a)/6-.003,cap-.040),-.185,.030,STONES[i%3],'upright impost bricks')
        pier.prism(box(a-.025,cap-.040,c+.025,cap),-.21,.046,'Terracotta impost edge','top impost slab')
    # The hidden soffit follows the measured front barrel and the narrower inner doorway.
    # A tapered shell encloses the top sightlines while keeping the raised front bricks in silhouette.
    sides=36 if lod else 72
    angles=np.linspace(0,np.pi,sides+1)
    stations=[(BACK-.016,CX,RX,CZ,RZ,TILT),(.081,.0,.871,.078,1.025,0.)]
    verts=[]
    for thick in [0.,.024]:
        for yy,xc,rw,zc,rh,slant in stations:
            verts += [[xc+(rw+thick)*np.cos(a),yy,zc+(rh+thick)*np.sin(a)+slant*np.cos(a)]for a in angles]
    ring=sides+1;faces=[]
    for k in range(sides):
        faces.extend([(k,k+1,ring+k+1,ring+k),(2*ring+k,3*ring+k,3*ring+k+1,2*ring+k+1),
                      (k,2*ring+k,2*ring+k+1,k+1),(ring+k,ring+k+1,3*ring+k+1,3*ring+k)])
    for k in [0,sides]:faces.append((k,ring+k,3*ring+k,2*ring+k))
    b.add(verts,faces,JOINT,'Vestibule/tapering soffit joint bed')
    for row in range(5):
        limits=[0.,*np.arange((.5 if row%2 else 1.)*np.pi/20,np.pi-.01,np.pi/20),np.pi]
        for col,(a,c) in enumerate(zip(limits,limits[1:])):
            verts=[]
            for offset in [-.011,-.001]:
                for frac in [(row+.027)/5,(row+.973)/5]:
                    yy,xc,rw,zc,rh,slant=(1-frac)*np.asarray(stations[0])+frac*np.asarray(stations[1]);
                    for ang in np.linspace(a+.0028,c-.0028,3):
                        verts.append([xc+(rw+offset)*np.cos(ang),yy,zc+(rh+offset)*np.sin(ang)+slant*np.cos(ang)])
            faces=[(0,1,4,3),(1,2,5,4),(6,9,10,7),(7,10,11,8),(0,6,7,1),(1,7,8,2),(3,4,10,9),(4,5,11,10),(0,3,9,6),(2,8,11,5)]
            b.add(verts,faces,[PLUM,'Shaded salmon soffit','Muted brick soffit'][(2*row+col//3)%3],f'Vestibule/rear soffit brick row {row+1}')
    plan=Polygon([origins[1],origins[3],origins[2],origins[0]])
    b.plan_prism(plan,FLOOR-.089,FLOOR,'Warm grey threshold','Vestibule/landing pavement')
