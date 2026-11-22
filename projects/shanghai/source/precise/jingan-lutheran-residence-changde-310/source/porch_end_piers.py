"""Two freestanding masonry piers at the street end of the Changde Road entrance.

The rectangular profiles and masonry beds are fitted separately to Nina's 2021
image 3. The back edges are partially hidden. The three-dimensional petal
grooves follow the two clefts that can be seen from the street.
"""
from math import cos, exp, pi, sin
from porch_columns import GRANITE, CUT, RELIEF, ASH, MORTAR

PALETTE = {}
BRICK_SHADES = (ASH, 'Porch pier | grey green brick', 'Porch pier | smoke brick')
for name, rgb in zip(BRICK_SHADES[1:], [(113,117,107),(100,104,99)]):
    PALETTE[name] = dict(color=[((c/255+.055)/1.055)**2.4 for c in rgb], roughness=.92)

def stack(b,frame,levels,mat,label):
    vertices=[]
    for z,width,depth in levels:
        for u,v in [(-1,-1),(1,-1),(1,1),(-1,1)]:
            vertices.append(frame(.5*width*u,.5*depth*v,z))
    faces=[(3,2,1,0)]
    for i in range(len(levels)-1):
        for k in range(4):
            j=(k+1)%4
            faces.append((i*4+k,i*4+j,(i+1)*4+j,(i+1)*4+k))
    faces.append(tuple(range(len(vertices)-4,len(vertices))))
    b.add(vertices,faces,mat,label)

def block(b,frame,u0,u1,v0,v1,z0,z1,mat,label):
    if min(u1-u0,v1-v0,z1-z0)<=.0004:return
    def shifted(u,v,z):return frame(u+(u0+u1)/2,v+(v0+v1)/2,z)
    stack(b,shifted,[(z0,u1-u0,v1-v0),(z1,u1-u0,v1-v0)],mat,label)

def masonry(b,frame,width,depth,beds,panel,label):
    h,d=width/2,depth/2
    p0,p1,z0,z1=panel
    back=-d+.022
    block(b,frame,-h,h,back,d,beds[0],beds[-1],MORTAR,label+' mortar core')
    for ua,ub,za,zb in [(-h,p0,beds[0],beds[-1]),(p1,h,beds[0],beds[-1]),
                           (p0,p1,beds[0],z0),(p0,p1,z1,beds[-1])]:
        block(b,frame,ua,ub,-d,back,za,zb,MORTAR,label+' shallow panel return')
    for row,(low,high) in enumerate(zip(beds,beds[1:])):
        zb,zt=low+.0028,high-.0028
        # Running bond continues onto the side facing the garden walk. Each
        # face closes independently so an individual brick can be edited.
        x=-h-.150*(row%2);idx=0
        while x<h:
            u0,u1=max(-h,x+.003), min(h,x+.298)
            for start,end in [(-h,p0),(p0,p1),(p1,h)]:
                a,c=max(start,u0),min(end,u1)
                if c<=a:continue
                front=back if start==p0 and z0<=(zb+zt)/2<=z1 else -d
                col=BRICK_SHADES[(idx+row*2)%3]
                block(b,frame,a,c,front-.005,front+.001,zb,zt,col,label+' front brick')
            idx+=1;x+=.301
        v=-d-.146*((row+1)%2);idx=0
        while v<d:
            va,vb=max(-d+.003,v+.003),min(d-.002,v+.291)
            for sign in (-1,1):
                u=sign*h
                block(b,frame,min(u-sign*.001,u+sign*.004),max(u-sign*.001,u+sign*.004),
                      va,vb,zb,zt,BRICK_SHADES[(idx+row+int(sign==1))%3],label+' return brick')
            v+=.294;idx+=1

def stone_bud(b,center,base,top,radius,angle,lod,label):
    # Broad lower shoulder and curved, pointed upper outline. Each petal cleft
    # dies into the stone before reaching the tip.
    meridian=[(0,.61),(.04,.73),(.11,.86),(.21,.95),(.33,1.),(.45,.994),
              (.55,.934),(.66,.823),(.77,.662),(.85,.50),(.92,.325),(.974,.151),(1.,.016)]
    if lod:meridian=[p for i,p in enumerate(meridian) if i not in (1,5,11)]
    sides=36 if lod else 72;vertices=[];faces=[]
    for t,r in meridian:
        for j in range(sides):
            a=2*pi*j/sides
            # Alternating seams curl to opposite sides as they ascend, making
            # the exposed front leaf taper at the top.
            depression=0
            for k in range(4):
                seam=angle+k*pi/2+(-1 if k%2 else 1)*(.05+.41*t*t)
                delta=(a-seam+pi)%(2*pi)-pi
                fade=(1-t**2)*min(1,.40+t*7)
                depression+=.100*fade*exp(-.5*(delta/.067)**2)
            rr=radius*(r-depression*r)
            vertices.append((center[0]+rr*cos(a),center[1]+rr*sin(a),base+(top-base)*t))
    for i in range(len(meridian)-1):
        for k in range(sides):
            j=(k+1)%sides;faces.append((i*sides+k,i*sides+j,(i+1)*sides+j,(i+1)*sides+k))
    faces.extend((tuple(range(sides-1,-1,-1)),tuple(range(len(vertices)-sides,len(vertices)))))
    b.add(vertices,faces,RELIEF,label+' pointed four-petal stone bud')

def add_piers(b,lod=False):
    for side,record in MEASURED.items():
        label='Porch '+side+' end pier |'
        cx,cy=record['center'];dx,dy=record['front_axis']
        def frame(u,v,z):return (cx+u*dx-v*dy,cy+u*dy+v*dx,z)
        profile=record['profile']
        stack(b,frame,profile[:2],GRANITE,label+' plinth')
        stack(b,frame,profile[1:8],CUT,label+' bevelled foot and roll')
        height,width,depth=profile[7]
        masonry(b,frame,width,depth,record['beds'],record['panel'],label)
        def shifted(level,dz,dw):
            z,w,d=level
            return (z+dz,w+dw,d+dw)
        # At each projecting edge the cross-section turns back into a dark,
        # narrow groove visible in the photograph, before the next roll starts.
        stack(b,frame,[profile[8],shifted(profile[9],-.009,-.004),
                       shifted(profile[9],-.005,.006),profile[9],
                       shifted(profile[9],.006,-.004),
                       shifted(profile[10],-.009,-.009),profile[10]],
              CUT,label+' square bed moulding')
        stack(b,frame,[profile[10],shifted(profile[10],.004,-.013),
                       shifted(profile[11],-.004,-.001),profile[11],
                       shifted(profile[11],.008,.002),
                       shifted(profile[12],-.005,.003),profile[12],
                       shifted(profile[12],.005,-.014)],
              CUT,label+' projecting second roll')
        stack(b,frame,[shifted(profile[12],.005,-.014),
                       shifted(profile[13],-.007,-.024),profile[13],profile[14]],GRANITE,label+' rectangular crown slab')
        stack(b,frame,profile[14:16],GRANITE,label+' hip cap and slopes')
        stack(b,frame,profile[15:],CUT,label+' stone pad under finial')
        bud=record['bud'];stone_bud(b,bud[:2],bud[2],bud[3],bud[4],record['angle'],lod,label)

MEASURED = {'left': {'center': [-0.96931, -1.99886],
          'front_axis': [0.99786741, -0.06527351],
          'profile': [(-2.29, 0.7768, 0.6544),
                      (-2.1348, 0.7582, 0.6417),
                      (-2.1254, 0.7584, 0.6149),
                      (-2.1043, 0.7611, 0.6194),
                      (-2.0774, 0.7419, 0.6045),
                      (-2.0655, 0.7223, 0.606),
                      (-2.0038, 0.6065, 0.5151),
                      (-1.9873, 0.5826, 0.4994),
                      (-1.2751, 0.5912, 0.4874),
                      (-1.2439, 0.6285, 0.5101),
                      (-1.2024, 0.6759, 0.5293),
                      (-1.1827, 0.6955, 0.5361),
                      (-1.1526, 0.7039, 0.5331),
                      (-1.1245, 0.7275, 0.5718),
                      (-1.0172, 0.733, 0.5854),
                      (-0.9134, 0.3034, 0.3009),
                      (-0.8926, 0.298, 0.2837),
                      (-0.8662, 0.2461, 0.2152),
                      (-0.8326, 0.236256, 0.206592)],
          'beds': [-1.9873,
                   -1.9276,
                   -1.8635,
                   -1.7936,
                   -1.7265,
                   -1.6624,
                   -1.5925,
                   -1.5285,
                   -1.4615,
                   -1.3974,
                   -1.3334,
                   -1.2751],
          'panel': [-0.149, 0.1501, -1.8635, -1.3974],
          'bud': [-0.96204, -1.99878, -0.83265, -0.49029, 0.1454],
          'angle': -1.36},
 'right': {'center': [3.87948, -2.18907],
           'front_axis': [0.99718557, -0.07497286],
           'profile': [(-2.29, 0.7194, 0.646),
                       (-2.1069, 0.7193, 0.6465),
                       (-2.1005, 0.6984, 0.6294),
                       (-2.0803, 0.7041, 0.6122),
                       (-2.0512, 0.6673, 0.5968),
                       (-2.034, 0.6428, 0.6234),
                       (-1.9903, 0.5857, 0.5421),
                       (-1.984, 0.5689, 0.4971),
                       (-1.2668, 0.566, 0.4936),
                       (-1.2338, 0.5935, 0.521),
                       (-1.1879, 0.6719, 0.5947),
                       (-1.1769, 0.6852, 0.5922),
                       (-1.1341, 0.6878, 0.596),
                       (-1.1017, 0.7437, 0.6782),
                       (-1.0176, 0.7389, 0.6738),
                       (-0.9326, 0.337, 0.304),
                       (-0.9117, 0.306, 0.279),
                       (-0.893, 0.263, 0.243),
                       (-0.8596, 0.2525, 0.2333)],
           'beds': [-1.984,
                    -1.9143,
                    -1.837,
                    -1.774,
                    -1.711,
                    -1.6451,
                    -1.585,
                    -1.5221,
                    -1.4563,
                    -1.3876,
                    -1.3219,
                    -1.2668],
           'panel': [-0.139, 0.1464, -1.837, -1.3876],
           'bud': [3.8529, -2.18531, -0.8596, -0.51923, 0.15435],
           'angle': -1.83}}
