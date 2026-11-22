"""Measure the five photographed bays, arched gallery, open rails, and deep sash reveals."""
from math import cos, pi, sin
BRICK, ARCH, BASE = "Russet field brick", "Red arch moulding", "Grey plinth stone"
FRAME, GLASS = "Brown timber joinery", "Garden glass"
INSIDE, STONE, TERRACOTTA = "Deep recess", "Warm ivory limestone", "Warm terracotta trim"
import numpy as np


def check_triangles(triangles, materials, distant):
    faces=np.asarray(triangles,dtype=np.float64)
    labels=np.asarray(materials)
    if faces.shape[1:]!=(3,3) or len(faces)!=len(labels):
        raise ValueError('Provide one material name per real triangle in author coordinates')
    edge_one=faces[:,1]-faces[:,0]
    edge_two=faces[:,2]-faces[:,0]
    results=[]

    def test(name,start,direction,expected,interval):
        d=np.asarray(direction,dtype=float);d/=np.linalg.norm(d)
        p=np.cross(d,edge_two)
        det=np.einsum('ij,ij->i',edge_one,p)
        front=det>1e-10
        inv=np.divide(1,det,where=front,out=np.zeros_like(det))
        delta=np.array(start)-faces[:,0]
        u=np.einsum('ij,ij->i',delta,p)*inv
        q=np.cross(delta,edge_one)
        v=q@d*inv
        t=np.einsum('ij,ij->i',edge_two,q)*inv
        valid=front & (u>=-1e-8) & (v>=-1e-8) & (u+v<=1+1e-8) & (t>=0.)
        hit=np.argmin(np.where(valid,t,np.inf))
        length=float(t[hit]) if valid.any() else None
        material=str(labels[hit]) if length is not None else None
        passed=material in expected and interval[0]<=length<=interval[1] if length is not None else False
        results.append({'name':name,'origin':list(start),'direction':list(direction),'material':material,
                        'distance_m':length,'expected':sorted(expected),'interval_m':interval,'passed':passed})

    def straight(label,x,z,acceptable,front_y):
        test(label,(x,-2.,z),(0.,1.,0.),acceptable,[2.+front_y[0],2.+front_y[1]])

    def frontal(label,x,z,accepted,face_y,local_y,epsilon=.009):
        y=face_y+local_y
        straight(label,x,z,accepted,[y-epsilon,y+epsilon])

    def glass_and_frame(label,x,sill,w,h,rise,cols,rows,depth,y):
        # Offset from both a transom and a vertical mullion for the pane.
        left=x-w/2
        frontal(label+' glass',left+.63*w/cols,sill+.49*(h-rise)/rows,
                [GLASS],y,depth-.003)
        frontal(label+' vertical frame',left+w/cols,sill+.58*(h-rise)/rows,
                [FRAME],y,depth-.106)
        frontal(label+' transom',left+.4*w/cols,sill+(h-rise)/rows,[FRAME],y,depth-.106)
        frontal(label+' stone sill',x,sill-.079,[BASE],y,-.215)

    def arcade(label,origin,y,base,spring,arches,railed):
        for k,(dx,w,rise) in enumerate(arches):
            x=origin+dx
            opening=label+f' arch {k+1}'
            frontal(opening+' gallery recess',x,base+1.47,[INSIDE],y,1.337)
            for fractional_angle in (.161,.328,.69):
                n=12 if distant else 23
                angle=(int(n*fractional_angle)+.44)*pi/n
                frontal(opening+' radial brick',x+(w/2+.081)*cos(angle),
                        spring+(rise+.081)*sin(angle),[ARCH,TERRACOTTA],y,-.076)
            if railed:
                start=x-w/2+.08;span=w-.16;n=max(2,round((span-.28)/.38))
                centres=[start+.18+(i+.5)*(span-.36)/n for i in range(n)]
                for i,u in enumerate(centres):
                    frontal(opening+f' baluster {i+1}',u,base+.329,[STONE],y,-.076,.025)
                    if i+1<n:
                        frontal(opening+f' opening {i+1}',(u+centres[i+1])*.5,
                                base+.329,[INSIDE],y,1.337)
                frontal(opening+' rail',x,base+.743,[STONE],y,-.2075)
        for i,((left,lw,_),(right,rw,_)) in enumerate(zip(arches,arches[1:])):
            u=origin+(left+lw/2+right-rw/2)/2
            frontal(label+f' column {i+1}',u,(base+spring)*.5,[STONE],y,-.20,.032)
            frontal(label+f' capital {i+1}',u,spring-.029,[STONE],y,-.29)

    centre=[(-2.40,1.24,.65),(0,2.94,1.31),(2.40,1.24,.65)]
    arcade('central ground tier',0,-.23,.075,3.05,centre,False)
    arcade('central upper tier',0,-.23,4.91,7.85,centre,True)
    glass_and_frame('gable half-round window',0,10.61,2.02,2.77,1.01,3,3,.43,-.23)
    for angle in (.17*pi,.28*pi,.75*pi,.86*pi):
        frontal('continuous pale arch hood',1.195*cos(angle),12.37+1.195*sin(angle),
                [STONE],-.23,-.215)
    for sign in (-1,1):
        frontal('horizontal hood shoulder',sign*1.45,12.38,[STONE],-.23,-.246)
        glass_and_frame('gable side lancet',sign*2.25,10.66,.85,2.09,.44,2,3,.31,-.23)
        wing=sign*6.775
        arcade('recessed wing',wing,.52,4.91,7.67,[(-1.50,2.57,.58),(1.50,2.57,.58)],True)
        for dx in (-1.52,1.52):
            glass_and_frame('wing ground sash',wing+dx,.61,1.63,2.70,.20,3,3,.31,.52)
        end=sign*12.47
        for dx in (-1.08,1.08):
            glass_and_frame('end ground sash',end+dx,.67,1.24,2.95,.18,3,3,.31,0)
            glass_and_frame('deep end sash',end+dx,5.79,1.70,2.95,.34,3,3,.655,0)
            frontal('pale end spandrel',end+dx,5.29,[STONE],0,-.0745)
        glass_and_frame('attic end sash',end,11.15,2.83,1.69,.23,4,2,.31,0)
        frontal('attic stone surround',end+1.64,12.03,[STONE],0,-.074)
        frontal('high flat capped end',end+.34,13.585,[STONE],0,-.17)
        # Opposing end returns can be read from the two oblique photographs.
        test('side return', (sign*17,.74,6.33),(-sign,0,0),[BRICK],[1.946,1.954])
    failed=[r for r in results if not r['passed']]
    if failed:
        raise ValueError(failed)
    return {'distant':bool(distant),'triangle_count':len(faces),'rays':results}
