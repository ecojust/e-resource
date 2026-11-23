"""Raycast all eight upper windows, the numbered door and masonry directly on the delivery meshes."""

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

    from zili_front import (GREY,RED,RED2,STONE,WOOD,GLASS,IRON,DARK,GREEN,PLINTH,
                            HALF,MID,UP,u,z)
    for tier,spans,y1,y2 in [('middle',MID,181,252),('upper',UP,39,113)]:
        for i,(a,b) in enumerate(spans):
            x0,x1=u(a),u(b);high=z(y1);low=z(y2);width=x1-x0;height=high-low;label=f'{tier} window {i+1}'
            for fraction in (.26,.71):
                for rise in (.23,.76):
                    at(label+' inset pane',x0+width*fraction,low+height*rise,GLASS,.210)
            at(label+' center stile',(x0+x1)/2,low+height*.4,WOOD,.142)
            at(label+' transom',x0+width*.28,low+height*.56,WOOD,.142)
            at(label+' sill',x0+width*.43,low-.047,STONE,-.135)
    for i,(px,py) in enumerate(((716,315),(788,270),(823,279),(822,320),(802,201),(856,230),(973,263),(1067,313),(1106,309),(1045,75),(754,93),(869,93))):
        at('grey street wall '+str(i),u(px),z(py),GREY,0)
    for px in (720,825,853,979,1011,1142):
        at('mid red brick belt',u(px),z(206)+.039,RED,-.016)
    for px in (748,848,868,1004,1135):
        at('upper red brick belt',u(px),z(63)+.039,RED,-.016)
    for px in (705,793,991,1129):
        at('rendered plinth',u(px),z(415),PLINTH,-.025)
    for py,material in ((292,STONE),(145,STONE),(8,RED2)):
        for px in (718,805,916,1036,1124):at('projecting continuous belt',u(px),z(py)+.025,material,-.2445)
    at('small opening recessed back',u(762),z(344),DARK,.43)
    at('blind arch infill',u(1109),z(345),GREY,.013)
    ux=(u(855)+u(954))/2;spring=z(354);zmark=spring+.267+.18
    at('green 464 address plate corner',ux+.119,zmark+.077,GREEN,-.1)
    at('green 464 address plate lower corner',ux-.119,zmark-.078,GREEN,-.1)
    for frac in (.128,.43,.73):
        x0=u(855);x1=u(954);xx=x0+frac*(x1-x0)
        profile=spring+.267*(1-((xx-(x0+x1)/2)/((x1-x0)/2))**2)
        test('radial voussoir', [xx,-2,profile+.1],[0,1,0],{RED,RED2,'warm mortar'},[1.939,1.977])
    for j in (1,3,6):
        xx=(u(855)+.045)+(u(954)-u(855)-.09)*j/8
        test('folding gate steel upright',[xx,-2,.63],[0,1,0],{IRON},[2.165,2.26])
    for xx in (u(864)+.03,u(935)+.02):
        test('shaded entrance recess through the lattice',[xx,-2,.78],[0,1,0],{DARK,IRON},[2.16,2.36])
    failed=[r for r in results if not r['passed']]
    if failed:raise ValueError(failed)
    return {'distant':bool(distant),'triangle_count':len(faces),'rays':results}
