"""Measure only surfaces visible along rays through the six photographed upper arches."""
from math import cos, pi, sin
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

    bricks=['terracotta brick '+str(i+1) for i in range(3)]
    glass='muted blue grey glass'; wood='oxidised red window joinery';stone='cream dressed stone'
    for tier,(sill,spring) in enumerate(((.63,2.47),(4.29,6.16))):
        for bay,x in enumerate((-3.18,0.,3.18)):
            label=f'Tier {tier+1} bay {bay+1} '
            for dx in (-.84,0.,.84):
                straight(label+'glass',x+dx,sill+1.03,[glass],[.722,.726])
            for dx in (-.405,.405):
                straight(label+'timber mullion',x+dx,sill+1.03,[wood],[.652,.658])
            straight(label+'transom',x+.16,spring,[wood],[.652,.658])
            count=23 if distant else 47
            for i in (1,count//4,count//2,3*count//4,count-2):
                a=(i+.48)*pi/count
                straight(label+'radial brick',x+1.354*cos(a),spring+1.354*sin(a),
                         [bricks[(5*i+i//5)%3]],[-.038,-.034])
            for side in (-1,1):
                straight(label+'projecting impost',x+side*1.337,spring-.040,[stone],[-.182,-.178])
            test(label+'brick soffit behind wall face',(x,.24,spring+.05),(0.,0.,1.),
                 bricks,[1.192,1.210])
            if (tier,bay) in ((0,0),(1,2)):
                straight(label+'fanlight spoke',x+.51*cos(pi*2/7),
                         spring+.51*sin(pi*2/7),[wood],[.652,.658])
            else:
                straight(label+'fanlight vertical',x+.405,spring+.47,[wood],[.652,.658])
            if tier==0:
                for i in range(11):
                    straight(label+'carved baluster',x-1.12+i*.224,sill+.329,[stone],[-.083,-.079])
                    straight(label+'baluster medallion',x-1.12+i*.224+.034,sill+.285,[stone],[-.090,-.086])
                for i in range(10):
                    between=x-1.12+(i+.50)*.224
                    straight(label+'open railing gap',between,sill+.329,[glass,wood],[.652,.726])
                straight(label+'coping',x+.20,sill+.624,[stone],[-.212,-.208])
            else:
                straight(label+'projecting sill',x+.15,sill+.07,[stone],[-.208,-.202])
    straight('plain upper spandrel',.1,3.92,['warm stucco'],[-.002,.002])
    straight('continuous inter-floor sill',.0,4.249,[stone],[-.131,-.125])
    straight('lower carved cornice',.11,.60,[stone],[-.542,-.538])
    failed=[r for r in results if not r['passed']]
    if failed:raise ValueError(failed)
    return {'distant':bool(distant),'triangle_count':len(faces),'rays':results}
