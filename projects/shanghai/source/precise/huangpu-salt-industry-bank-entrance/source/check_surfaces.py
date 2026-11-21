"""Check the stone portico, glazing, capital depth and openings of the two-panel rails."""

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
        passed=material in expected and interval[0]-.004<=length<=interval[1]+.004 if length is not None else not expected
        results.append({'name':name,'origin':list(start),'direction':list(direction),'material':material,
                        'distance_m':length,'expected':sorted(expected),'interval_m':interval,'passed':passed})


    from portal import STONE, MOULD, LIGHT, GLASS, DOOR
    def front(name,x,z,materials,depth):
        test(name,[x,-3.,z],[0,1,0],materials,[3-depth[1],3-depth[0]])
    for sign in [-1,1]:
        for z in (.05,.24,.98,2.09,3.43,4.06,4.18):
            front('inner round column axis',sign*2.34,z,{MOULD},(1.20,1.396))
        for inward in [-.14,.14]:
            for z in (.98,2.11,3.31):
                front('separate curved Tuscan shaft',sign*2.34+inward,z,{MOULD},(1.15,1.24))
        front('inner square abacus',sign*2.34,4.30,{MOULD},(1.345,1.355))
        for x in [-.29,0,.29]:
            for z in (.40,1.50,2.60,3.93):
                front('outer rectangular pier',sign*3.48+x,z,{STONE},(1.094,1.096))
        for z,depth in [(4.10,1.245),(4.23,1.30),(4.40,1.265),(4.56,1.33)]:
            front('outer stepped stone capital',sign*3.48,z,{MOULD},(depth-.005,depth+.005))
        for lower,upper,n,z in [(.53,2.70,5,6.02),(2.84,3.86,2,5.97)]:
            for i in range(n):
                x=sign*(lower+(i+.5)*(upper-lower)/n)
                for delta in (-.06,0,.06):
                    front('genuine rail opening',x,z+delta,set(),(0,0))
                front('stone above opening',x,z+.194,{MOULD},(1.905,1.915))
                front('projected ring lip',x,z+.149,{LIGHT},(1.945,1.955))
            for z0,d in [(z-.255,1.98),(z+.254,2.015)]:
                front('rail sill or cap',sign*(lower+upper)/2,z0,{LIGHT},(d-.003,d+.003))
        front('unfilled space between round shaft and pier',sign*2.88,2.0,{STONE},(.295,.305))
    for x in [-1.7,-.7,0,.7,1.7]:
        front('continuous junction between the porch ceiling and backing wall',x,4.32,{STONE},(.295,.305))
    for x,hw in [(-1.67,.57),(0,.77),(1.67,.57)]:
        for xx in (-.25,.25):
            for z in (.78,1.49,1.95,2.51):
                front('recessed door-light glazing',x+xx*hw,z,{GLASS},(.021,.03))
        for z in (1.01,2.05):front('separate central muntin',x,z,{DOOR},(.094,.096))
        for z in (.59,1.17,1.72,2.24):front('door glazing rail',x+.26*hw,z,{DOOR},(.094,.096))
    for z,d in [(4.49,1.57),(4.66,1.63),(4.995,1.70),(5.33,1.80),(5.46,1.91),(5.56,2.01)]:
        for x in [-1.30,0.,1.30]:front('front of cornice and frieze',x,z,{MOULD,STONE},(d-.003,d+.003))
    for x in [-.53,-.28,0,.28,.53]:
        front('central stone medallion',x,6.31,{MOULD,LIGHT},(1.969,2.03))
    for sign in (-1,1):
        front('upper space beside shield',sign*1.25,6.61,set(),(0,0))
        front('space above low side panels',sign*3.25,6.45,set(),(0,0))
    failed=[x for x in results if not x['passed']]
    if failed:raise ValueError(f'{len(failed)} unexpected surface hits, first {failed[:5]}')
    return dict(distant=bool(distant),triangle_count=len(faces),rays=results,passed=True)
