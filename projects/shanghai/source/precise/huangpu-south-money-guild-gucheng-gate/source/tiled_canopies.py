"""Three short, upturned hoods of the park gateway, surveyed from two elevated views."""
from math import cos, pi, sin
import numpy as np

PAN = 'Grey fired pan tiles'
ROLL = 'Weathered cylindrical cover tiles'
RIDGE = 'Pale grey raised tile coping'
SOFFIT = 'Dark timber soffit'
EAVE = 'Dull end grain of projecting rafters'
PALETTE = {k: {'color':c,'roughness':.91} for k,c in [
    (PAN,[.19,.208,.212]), (ROLL,[.285,.303,.303]),
    (RIDGE,[.48,.49,.47]), (SOFFIT,[.19,.165,.135]),(EAVE,[.298,.274,.227])]}


def upward(builder, rows, material, label):
    count=len(rows[0]);pts=[tuple(v)for row in rows for v in row];faces=[]
    for j in range(len(rows)-1):
        for i in range(count-1):
            a=j*count+i;face=(a,a+1,a+1+count,a+count)
            av,bv,cv=(np.asarray(pts[k])for k in face[:3])
            faces.append(face if np.cross(bv-av,cv-av)[2]>0 else face[::-1])
    builder.add(pts,faces,material,label)


def canopy(builder, x0, x1, eave, height, ends, tier, lod):
    """At the side wings only the exposed end rises. Both central hips turn up."""
    fore,back,mid=-.61,1.42,.43
    def roof(u,t,rear):
        line=x0+(x1-x0)*u
        left=(max(0,1-2*u)**5 if ends[0] else 0.)
        right=(max(0,2*u-1)**5 if ends[1] else 0.)
        lift=left+right
        # The ridge ends cut in from the eaves. At the rising edges the concave
        # hip tile retains a visible crest between eaves and ridge in the side view.
        x=line+.39*t*(left-right)
        y=(back if rear else fore)*(1-t)+mid*t
        z=eave+height*(.51*t+.49*t*t)+lift*(.68+.43*t-.20*sin(pi*t))
        return np.array([x,y,z])
    names=('rear','south')
    for rear in [True,False]:
        label=tier+' '+names[int(not rear)]
        nx=18 if lod else 34;nt=5 if lod else 9
        rows=[[roof(i/nx,t/nt,rear)for i in range(nx+1)]for t in range(nt+1)]
        upward(builder,rows,PAN,label+' clay tile bed')
        under=[[v+np.array([0.,0.,-.11])for v in row]for row in rows]
        count=len(rows[0]);ps=[tuple(v)for row in under for v in row];faces=[]
        for j in range(nt):
            for i in range(nx):
                idx=j*count+i;f=(idx,idx+1,idx+1+count,idx+count)
                a,b,c=(np.asarray(ps[k])for k in f[:3]);faces.append(f if np.cross(b-a,c-a)[2]<0 else f[::-1])
        builder.add(ps,faces,SOFFIT,label+' underside')
        edge=[roof(i/nx,0,rear) for i in range(nx+1)]
        builder.tube([p-[0,0,.057]for p in edge],.066,SOFFIT,6 if lod else 8,label+' eaves purlin')
        n=max(8,round((x1-x0)/(.39 if lod else .215)))
        for i in range(n+1):
            u=(i+.12)/(n+.24);along=range(6 if lod else 10)
            path=[roof(u,t/(len(along)-1),rear)for t in along]
            radius=.077 if lod else .080
            shell=[]
            for t,p in enumerate(path):
                # Round upper half of a clay cover tile. It sits above the flat pan.
                t0=t/(len(path)-1);tangent=roof(u,min(1,t0+.0001),rear)-roof(u,max(0,t0-.0001),rear)
                side=roof(u+.0001,t0,rear)-roof(u-.0001,t0,rear);side/=np.linalg.norm(side)
                normal=np.cross(side,tangent);normal*=1 if normal[2]>0 else -1;normal/=np.linalg.norm(normal)
                shell.append([p+radius*cos(pi*k/(4 if lod else 6))*side+radius*sin(pi*k/(4 if lod else 6))*normal+[0,0,.014]for k in range(5 if lod else 7)])
            upward(builder,shell,ROLL,label+' round tile rolls')
            if not lod:
                for index in (3,6):
                    band=np.array(shell[index])+[0.,0.,.014]
                    builder.tube(band,.012,ROLL,4,label+' tile overlap lips')
            if i%2==0:
                b=path[0]-[0,0,.115];builder.box(b,(.10,.24,.108),EAVE,label=label+' exposed rafter ends')
        for side,on in enumerate(ends):
            if not on:continue
            line=[roof(float(side),j/nt,rear)+[0,0,.054]for j in range(nt+1)]
            builder.tube(line,.092,RIDGE,6 if lod else 10,label+' raised hip')
    ridge=[roof(i/30,1,False)+[0,0,.088]for i in range(31)]
    builder.tube(ridge,.099,RIDGE,7 if lod else 12,tier+' curved main ridge')
    for side,on in enumerate(ends):
        if not on:continue
        # The exposed end closes with a pitched, swept hip, seen in Fayhoo's 2015 west view.
        u=float(side);rows=[]
        for j in range(8):
            t=j/7;f=roof(u,t,False);r=roof(u,t,True)
            line=[]
            for i in range(13):
                v=i/12;p=f*(1-v)+r*v;p[2]-=(1-t)*.58*sin(pi*v)
                p[0]+=(1 if side else -1)*.24*(1-t)*sin(pi*v);line.append(p)
            rows.append(line)
        upward(builder,rows,PAN,tier+' upturned end tiles')
        builder.tube([v+[0,0,.05]for v in rows[0]],.083,RIDGE,7 if lod else 10,tier+' swept end coping')


def roofs(builder,lod):
    canopy(builder,-8.17,-2.50,6.48,.74,(True,False),'West hood',lod)
    canopy(builder,2.50,8.17,6.48,.74,(False,True),'East hood',lod)
    canopy(builder,-4.20,4.20,7.56,.78,(True,True),'Raised central hood',lod)
