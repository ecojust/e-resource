"""Raycast the named door hood, distinct column orders and both tiers of windows."""

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
        passed=material in expected and interval[0]-.004<=length<=interval[1]+.004 if length is not None else False
        results.append({'name':name,'origin':list(start),'direction':list(direction),'material':material,
                        'distance_m':length,'expected':sorted(expected),'interval_m':interval,'passed':passed})


    def at(name,x,z,material,y):
        test(name,[x,-2,z],[0,1,0],[material],[2+y-.003,2+y+.003])

    from entrance import WALL, TRIM, LIGHT, DARK, FRAME, GLASS, COPPER, METAL
    def front(name,x,z,allowed,depth):
        test(name,[x,-2,z],[0,1,0],allowed,[2-depth[1],2-depth[0]])
    for sign in (-1,1):
        for top in (False,True):
            bottom=10.38 if top else 7.53
            for offset in (-.45,.45):
                for rise in ([.45,1.47] if top else [1.25,1.53]):
                    front('separate recessed window pane',sign*1.02+offset,bottom+rise,{GLASS},(-.325,-.315))
            front('inset central stile',sign*1.02,bottom+1.40,{FRAME},(-.166,-.154))
            if top:front('projecting upper sill',sign*1.02,bottom-.07,{TRIM},(.39,.41))
        for z in (.18,.27,2.,3.8,4.40):
            front('lower round shaft and moulded base',sign*2.38,z,{WALL},(1.17,1.355))
        for dx in (-.23,0.,.23):
            for z in (1.91,4.17,9.91,11.47):
                front('tall recessed fluted order',sign*3.05+dx,z,{WALL},(.50,.645))
        front('upper rounded capital',sign*3.05,12.72,{TRIM},(.74,.78))
        front('square upper impost',sign*3.05,13.04,{TRIM},(.48,.52))
        for z in (5.32,5.44,6.60):
            front('stepped lower-order abacus and die',sign*2.38,z,{TRIM},(1.22,1.32))
        for x in (-.35,.35):
            front('lower paired volutes',sign*2.38+x,5.10,{TRIM,LIGHT},(1.23,1.31))
    for x in (-1.58,-.67,.38,1.57):
        for z in (.54,1.40,2.64):front('deep portal behind the grille',x,z,{DARK},(-.66,-.64))
    for x in (-1.75,-.875,0,.875,1.75):
        front('five narrow transom uprights',x,3.49,{METAL},(-.56,-.52))
    for z in (3.03,3.20,3.37,3.54,3.70):front('grille rail',.65,z,{METAL},(-.54,-.51))
    for x in (-3.08,-1.69,-.56,.56,1.69,3.08):
        arch=7.13+1.15*(1-(x/3.38)**2)
        for dz,depth in ((.05,1.16),(.18,1.26),(.275,1.32)):
            front('three curved hood mouldings',x,arch+dz,{TRIM},(depth-.012,depth+.012))
    front('carved center cartouche',0,7.30,{WALL,LIGHT},(1.042,1.105))
    for x in (-2.95,-1.64,-.76,.76,1.64,2.95):
        front('upper doorsill cornice',x,13.55,{TRIM},(.60,.63))
    for x in (-1.55,1.55):
        front('shallow fascia flanking inscription',x,5.43,{TRIM},(.39,.405))
    for column in range(4):
        xmin=-1.44+.745*column
        hits=[]
        for xpos in np.linspace(xmin,xmin+.58,10):
            for z in (5.31,5.37,5.42,5.48,5.54):
                front('title outline sample',float(xpos),z,{COPPER,TRIM},(.395,.464))
                if results[-1]['material']==COPPER:hits.append(results[-1]['origin'])
        assert len(hits)>=4,(column,hits)
    failed=[r for r in results if not r['passed']]
    if failed:raise ValueError(failed)
    return {'distant':bool(distant),'triangle_count':len(faces),'rays':results}
