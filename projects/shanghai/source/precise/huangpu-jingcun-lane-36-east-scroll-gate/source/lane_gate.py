"""One documented leaf of the Jingcun lane gate, reconstructed from the 2013 and 2020 frontage."""
from math import cos, pi, sin

def finish(srgb, rough, metal):
    return dict(color=[(v/255/12.92 if v/255<=.04045 else ((v/255+.055)/1.055)**2.4) for v in srgb],
                roughness=rough, metallic=metal)
PALETTE={'black painted frame':finish((48,48,43),.61,.31),
         'aged gilding':finish((171,143,91),.61,.41),
         'bronze scroll':finish((116,99,68),.65,.31),
         'dark iron strip':finish((68,65,54),.64,.34)}
def block(b,name,l,r,z0,z1,depth,mat='black painted frame',offset=0.):
    b.box(((l+r)/2,offset,(z0+z1)/2),(r-l,depth,z1-z0),mat,label=name)
def swept(b,name,path,rad,mat,lod,offset=0.):
    b.tube([(x,offset,z)for x,z in path],rad,mat,4 if lod else 7,label=name)
def ring(b,name,x,z,rx,rz,radius,mat,lod,offset,start=0.,end=2*pi):
    count=12 if lod else 23
    sides=4 if lod else 7
    vertices=[];faces=[]
    for i in range(count):
        a=start+(end-start)*i/count
        dx,dz=rz*cos(a),rx*sin(a)
        n=(dx*dx+dz*dz)**.5
        for j in range(sides):
            bangle=2*pi*j/sides
            vertices.append((x+rx*cos(a)+radius*cos(bangle)*dx/n,
                             offset+radius*sin(bangle),z+rz*sin(a)+radius*cos(bangle)*dz/n))
    for i in range(count):
        for j in range(sides):
            k=(i+1)%count; t=(j+1)%sides
            faces.append((i*sides+j,i*sides+t,k*sides+t,k*sides+j))
    b.add(vertices,faces,mat,name)
def add_building(b,lod):
    for x,name in [(-.8,'meeting stile'),(.8,'east hinge stile')]:
        block(b,name,x-.028,x+.028,.025,2.335,.09)
    for name,z,d in [('bottom edge',.055,.07),('base frieze cap',.272,.047),
                     ('lower panel head',1.155,.037),('middle horizontal',1.292,.024),
                     ('upper panel sill',1.431,.035),('upper panel head',2.078,.049),
                     ('top edge',2.302,.054)]:
        block(b,name,-.775,.775,z-d/2,z+d/2,.064)
    for ix in range(4):
        x=-.59+.392*ix
        for j,(za,zb) in enumerate([(.29,1.14),(1.453,2.052)]):
            for s in [-1,1]:
                xx=x+s*.107
                block(b,f'borders {ix} {j} {s}',xx-.012,xx+.012,za,zb,.038,'dark iron strip')
            for k in range(3 if j else 4):
                zz=za+(k+.52)*(zb-za)/(3 if j else 4)
                ring(b,f'open eye {ix} {j} {k}',x,zz,.045,.055,.0062,'bronze scroll',lod,-.008)
                for side in [-1,1]:
                    sx=x+side*.065
                    path=[(x+side*.027,zz-.041),(sx,zz-.019),(x+side*.084,zz+.005),
                          (x+side*.077,zz+.038),(x+side*.053,zz+.040)]
                    swept(b,f'paired curved stems {ix} {j} {k}',path,.0055,'bronze scroll',lod,-.005)
    # The top and foot have much shallower, wider ornaments than the vertical insert grilles.
    for k in range(6):
        x=-.6375+.255*k
        for z,mat in [(2.19,'aged gilding'),(.16,'bronze scroll')]:
            ring(b,f'frieze ring {k} {mat}',x,z,.075,.077,.008,mat,lod,-.015)
            for side in [-1,1]:
                swept(b,f'frieze scroll {k} {mat}',[(x+side*.069,z-.03),(x+side*.095,z-.061),
                    (x+side*.12,z-.039),(x+side*.12,z+.015),(x+side*.091,z+.033)],.007,mat,lod,-.010)
    for k in range(7):
        x=-.654+.218*k
        block(b,f'spear neck {k}',x-.008,x+.008,2.322,2.378,.019,'dark iron strip')
        root,tip=2.368,2.496
        vertices=[(x,-.010,root-.008),(x-.021,0,root+.021),(x,.016,root+.027),
                  (x+.021,0,root+.021),(x,-.014,root+.023),(x,0,tip)]
        faces=[(0,2,1),(0,3,2),(0,4,3),(0,1,4),(5,1,2),(5,2,3),(5,3,4),(5,4,1)]
        b.add(vertices,faces,'dark iron strip',f'pointed finial {k}')
