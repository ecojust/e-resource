"""The two small upturned roofs read separately in the ground and aerial photographs."""
import math
import numpy as np

def add_hipped_eave(builder,cx,base,lod,box,tile,wood,underside):
    # Horizontal short ridge, four draining faces and a thin eave with two lifted fore corners.
    x0,x1=cx-2.61,cx+2.61;y0,y1=-.91,2.05;rows=np.array([0,.18,.40,.54,.70,1.]);cols=np.linspace(0,1,15 if lod else 29)
    def height(t,v):
        edge=abs(2*t-1);hip=min(v/.54,(1-v)/.46,(1-edge)/.41)
        curl=1.34*edge**5*max(0.,1-v/.54)**1.4+.28*edge**7*max(0.,(v-.54)/.46)
        return base+.55*v+1.07*hip+curl
    verts=[];faces=[]
    for down in [True,False]:
        for v in rows:
            for t in cols:
                verts.append((x0+(x1-x0)*t,y0+(y1-y0)*v,height(t,v)-(.14 if down else 0.)))
    nx=len(cols);ny=len(rows);cap=nx*ny
    for j in range(ny-1):
        for i in range(nx-1):
            a=j*nx+i
            # Use the same diagonal on both sides of each curved quad. Reversing a whole
            # nonplanar quad selects another diagonal and changes the local eave thickness.
            for face in [(a,a+1,a+nx+1),(a,a+nx+1,a+nx)]:
                faces.append(tuple(reversed(face)))
                faces.append(tuple(k+cap for k in face))
    border=list(range(nx))+[i*nx+nx-1 for i in range(1,ny)]+[(ny-1)*nx+i for i in range(nx-2,-1,-1)]+[j*nx for j in range(ny-2,0,-1)]
    for a,b in zip(border,border[1:]+border[:1]):faces.append((a,b,b+cap,a+cap))
    name='eyebrow roof at '+str(round(cx,2));builder.add(verts,faces,tile,name+' / four hipped planes and curled eave')
    # The support follows the red timber at the top of the window bay, inside the overhang.
    box(builder,cx-1.76,cx+1.76,-.30,1.43,underside-.07,base+.37,wood,name+' / exposed bearing above window')
    # Six-sided ridge covers are sectioned across the shallow horizontal ridge and curl at each end.
    xs=np.linspace(cx-1.57,cx+1.57,15 if not lod else 7);v=.54;yy=y0+(y1-y0)*v;r=.085;vs=[];fs=[]
    for xx in xs:
        end=abs((xx-cx)/1.57);h=height((xx-x0)/(x1-x0),v)+.055+.21*end**6
        for a in np.linspace(0,math.tau,6,endpoint=False):vs.append((xx,yy+r*math.cos(a),h+r*math.sin(a)))
    fs.append(tuple(reversed(range(6))));i0=(len(xs)-1)*6;fs.append(tuple(i0+i for i in range(6)))
    for j in range(len(xs)-1):
        for k in range(6):fs.append((6*j+k,6*j+(k+1)%6,6*(j+1)+(k+1)%6,6*(j+1)+k))
    builder.add(vs,fs,tile,name+' / horizontal rolled ridge with kicked ends')
