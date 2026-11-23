"""Test all three bays, distinct balcony structures, pierced railing and the supported front entrance."""

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



    from guild_front import AXES, WALL,TRIM,WOOD,DARK,IRON,GLASS
    def front(name,x,z,materials,depth):
        test(name,[x,-3.,z],[0,1,0],materials,[3-depth[1],3-depth[0]])
    for x in AXES:
        for z in (5.78,7.39,9.88,10.36,13.18,13.80):
            for off in (-1.10,0,1.10):
                front('independently recessed triple window',x+off+.19,z,{GLASS},(-.342,-.338))
                front('rebated wood window jamb',x+off+.422,z,{WOOD},(-.227,-.223))
        for dx in (-1.80,-.64,.70,1.80):
            front('each balcony has a separate front deck',x+dx,8.66,{TRIM},(1.105,1.115))
            front('separate balcony handrail',x+dx,9.61,{IRON},(1.076,1.083))
        for dx in (-1.62,-.81,0,.81,1.62):
            front('fretwork retains a narrow picket',x+dx,9.42,{IRON},(1.055,1.064))
        for dx in (-1.22,-.16,.16,1.22):
            front('a genuine iron opening reaches the recessed balcony glass',x+dx,9.29,{GLASS},(-.342,-.338))
        for dx in (-1.70,0,1.70):
            front('stone console projects from the wall below deck',x+dx,8.13,{TRIM},(.20,.45))
        for dx in (-1.02,0,1.02):
            front('draped stone swag has a separate first surface',x+dx,11.695,{TRIM},(.12,.145))
        for dx in (-1.53,-.51,.51,1.53):
            front('four attachment bosses per swag band',x+dx,12.04,{TRIM},(.155,.160))
        front('cornice above the narrow upper lights',x+.13,14.94,{TRIM},(.545,.555))
    for x in (-1.45,1.45):
        for z in (.11,.26,.87,1.72,2.79,3.02):
            front('the two entrance shafts remain forward of the doors',x,z,{TRIM},(.395,.49))
    for x in (-.54,.54):
        for z in (.81,1.62,2.33,3.32):
            front('recessed door glazing below the arch',x,z,{GLASS},(-.342,-.338))
    front('central entrance crown stone',0,4.35,{TRIM},(.342,.348))
    for x in (-7.2,-2.44,2.44,7.2):
        for z in (2.21,6.07,11.16,14.40):front('separate rusticated masonry pier',x,z,{TRIM},(.138,.143))
    for x in (-4.88,4.88):
        for z in (1.64,2.35,3.02):front('each side window recess',x+.24,z,{GLASS},(-.342,-.338))
    for x in (-8.05,8.05):front('no treatment beyond documented street wall',x,7.70,set(),(0,0))
    front('no invented added-storey mass',0,16.42,set(),(0,0))
    failed=[r for r in results if not r['passed']]
    if failed:raise ValueError(f'{len(failed)} incorrect contacts: {failed}')
    return dict(distant=bool(distant),triangle_count=len(faces),rays=results,passed=True)
