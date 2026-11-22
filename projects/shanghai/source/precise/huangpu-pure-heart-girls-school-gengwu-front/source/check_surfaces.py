"""Trace the source photograph’s fifteen windows, ten spandrels, shafts and keyed oculus on each signed GLB."""
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


    def at(name,x,z,material,y):
        test(name,[x,-2,z],[0,1,0],[material],[2+y-.003,2+y+.003])
    stone='weathered pale stone'
    grey='grey exposed brick'
    glass='grey purple glazing'
    frame='painted dark window metal'
    for bay,x in enumerate((-6.48,-3.24,0,3.24,6.48)):
        for k,(lo,hi) in enumerate(((.81,2.8),(5.31,6.72),(8.71,10.28))):
            name=f'bay {bay+1} window row {k+1}'
            for j,offset in enumerate((-.82,-.39,.217,.39,.83)):
                if k==2 and abs(offset)==.39:continue
                at(name+f' glass {j+1}',x+offset,lo+.29,glass,.263)
            at(name+' left jamb',x-.943,lo+.35,frame,.182)
            at(name+' transom',x+.217,lo+(hi-lo)*(.56 if k==0 else .39 if k==1 else .49),frame,.182)
            at(name+' projecting sill',x+.16,lo-.052,stone,-.243)
        for j in (-.47,.47):
            at(f'{bay} stone field {j}',x+j,4.06,stone,-.033)
            at(f'{bay} incised diamond {j}',x+j+.335,4.06,'shadow in recessed stone carving',-.043)
    for i,x in enumerate((-4.86,-1.62,1.62,4.86)):
        test(f'full column {i+1} at lower window',[x,-2,1.3],[0,1,0],[stone],[1.45,1.50])
        test(f'full column {i+1} at upper window',[x,-2,5.7],[0,1,0],[stone],[1.48,1.52])
        at(f'full column {i+1} abacus',x,6.813,stone,-.62)
    for x in (-8.1,8.1):
        test('engaged edge shaft '+str(x),[x,-2,5.7],[0,1,0],[stone],[1.82,1.85])
    for x in (-8.86,8.86):
        at('outer pier '+str(x),x,2.2,stone,-.3875)
    for i in range(4):
        ang=i*pi/2
        at('oculus stone key '+str(i),.65*cos(ang),12.43+.65*sin(ang),stone,-.31)
    at('ring between keys',.63*cos(pi*.25),12.43+.63*sin(pi*.25),stone,-.19)
    for i in (-5,-2,0,2,5):
        at('horizontal louvre '+str(i),.065,12.43+i*.062,frame,.29)
        at('recessed dark grille '+str(i),.065,12.458+i*.062,'dark oculus grille',.37)
    for x,z in ((-2,12.13),(2,12.11),(0,14.02),(-5.76,11.78),(5.76,11.78)):
        at(f'brick pediment {x} {z}',x,z,grey,0)
    for x in (-4,-1.5,1.5,4):
        at('attic masonry '+str(x),x,10.52,grey,0)
    for z,y in ((7.39,-.13),(7.99,-.37),(10.87,-.20),(11.11,-.32)):
        at('central moulded course '+str(z),.18,z,stone,y)
    failed=[r for r in results if not r['passed']]
    if failed:raise ValueError(failed)
    return {'distant':bool(distant),'triangle_count':len(faces),'rays':results}
