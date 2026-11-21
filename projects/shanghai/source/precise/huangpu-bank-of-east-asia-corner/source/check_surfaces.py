"""Trace measured street-facing features in detached, decoded triangles for each distributed mesh."""
import json
from math import asin, cos, sin
from pathlib import Path
import numpy as np

def check_triangles(triangles,materials,distant):
    root=Path(__file__).resolve().parent
    geometry=json.loads((root/'frontage-registration.json').read_bytes())
    v=np.asarray(triangles,dtype=float)
    materials=np.asarray(materials)
    if v.shape!=(len(materials),3,3):
        raise ValueError('One triangle and one material ID per face are required')
    bands=[(7.05,10.06),(10.98,13.64),(14.69,17.36),(18.35,20.97),(21.94,24.47)]
    stone='grey aggregate stone';trim='smooth grey stringcourse';metal='blackened window metal'
    blue='muted street glass';pale='upper storey glass';marble='BEA ivory veined marble'
    rays=[]
    def frame(a,b):
        a=np.array(a);b=np.array(b);t=(b-a)/np.linalg.norm(b-a);n=np.array([t[1],-t[0]])
        delta=v[:,:,:2]-(a+b)/2
        u=delta@t;z=v[:,:,2];d=delta@n
        dx=u[:,1:]-u[:,0,None];dz=z[:,1:]-z[:,0,None]
        det=dx[:,0]*dz[:,1]-dx[:,1]*dz[:,0]
        def probe(name,x,h,desired,low,high):
            b1=(x-u[:,0])*dz[:,1]-(h-z[:,0])*dx[:,1]
            b2=(h-z[:,0])*dx[:,0]-(x-u[:,0])*dz[:,0]
            # Use the first outward-facing material. This also catches inverted veneer normals.
            ids=np.flatnonzero((det>1e-8)&(b1>=-1.e-9)&(b2>=-1.e-9)&(b1+b2<=det+1e-9))
            hit=None;depth=None
            if len(ids):
                de=d[ids,0]+(b1[ids]*(d[ids,1]-d[ids,0])+b2[ids]*(d[ids,2]-d[ids,0]))/det[ids]
                near=de<=2.1;ids=ids[near];de=de[near]
                if len(ids):
                    j=de.argmax();hit=str(materials[ids[j]]);depth=float(de[j])
            allowed=desired if isinstance(desired,tuple)else(desired,)
            ok=hit in allowed and (depth is None or low-.003<=depth<=high+.003)
            rays.append(dict(detail=name,local_xz_m=[float(x),float(h)],expected_materials=list(allowed),actual=hit,
                             depth_m=depth,expected_depth_m=None if desired is None else [low,high],passed=bool(ok)))
        return probe
    reg=geometry['visible_edges_local_m'];r=geometry['arc_radius_m'];half=geometry['arc_half_chord_m']
    def arc(a,retreat):
        return ((r-retreat)*sin(a),r-(r-retreat)*cos(a))
    def arcs(w,retreat):
        angle=asin(w/(r-retreat))
        return [arc(angle*(i/2-1),retreat)for i in range(5)]
    def offices(a,b,wing):
        probe=frame(a,b)
        for j,(lo,hi)in enumerate(bands):
            paint=blue if wing or j%2==0 else pale
            u=0 if not wing else -.88*wing
            probe('office glass',u+.26,lo+.87,paint,-.31,-.306)
            probe('metal meeting stile',u,lo+.82,metal,-.152,-.148)
            probe('horizontal transom',u+.22,lo+(hi-lo)*.67,metal,-.152,-.148)
            probe('stone sill',u+.19,lo-.052,trim,.112,.137)
        if wing:
            u=wing*1.29
            for lo,hi in bands:
                probe('single side light',u+.16,lo+.94,blue,-.31,-.306)
            gx=wing*1.18
            probe('clipped ground window',gx+.15,4.93,blue,-.31,-.306)
            probe('stone crossbar',gx+.15,3.11,stone,.055,.064)
            probe('clip in the top corner',gx+.477,5.61,stone,-.003,.003)
            probe('rooftop rail',.43,26.18,'weathered zinc',-.33,-.32)
            probe('air between rooftop rails',.53,26.43,None,0,0)
    for a,b in zip(arcs(half,0),arcs(half,0)[1:]):
        offices(a,b,0)
    offices(reg[0],reg[1],1);offices(reg[2],reg[3],-1)
    for w,retreat,lo,top in ((3.83,.62,25.30,27.08),(2.82,1.31,27.23,29.77)):
        pts=arcs(w,retreat)
        for a,b in zip(pts,pts[1:]):
            test=frame(a,b);test('setback window',.17,lo+.63,blue,-.31,-.306)
            test('setback frame',.18,lo+.34+(top-.31-lo-.34)*.67,metal,-.152,-.148)
    probe=frame((-.79,1.95),(.79,1.95))
    for u in (-.39,0,.39):
        probe('small crown dark slit',u+.04,31.34,metal,-.223,-.218)
    probe('crown side pier',.71,31.16,stone,-.002,.002)
    probe('sky above side shoulder',1.27,31.34,None,0,0)
    portal=frame((-3.12,.26),(3.12,.26))
    for side in (-1,1):
        for x in (.320,.423):
            for z in (1.07,2.89,3.76):
                portal('variegated marble column',side*x*6.15,z,(marble,'BEA grey gold vein','BEA smoke marble veins'),.275,.375)
        portal('door leaf',side*.84,1.4,('BEA dark timber door','BEA recessed timber panel'),-.61,-.085)
        portal('marble lintel',side*.42,2.52,(marble,'BEA grey gold vein','BEA smoke marble veins'),.176,.193)
        portal('shoulder of pediment',side*1.12,4.52,'BEA light entrance stone',.165,.18)
    portal('recess behind open door',.02,1.37,'BEA unlit door interior',-.962,-.958)
    portal('recessed red square',.1,3.21,'BEA oxblood entrance plaque',.176,.184)
    portal('square frame around red plaque',.397,3.20,'BEA warm cap stone',.14,.153)
    # Raised signage: select a point inside each independent contour and cast through the fully assembled wall.
    glyph_samples = [[(0.1948, -0.014), (0.23315, -0.0111), (-0.19015, 0.0051), (-0.2076, 0.23705)], [(0.1948, -0.014), (0.23315, -0.0111), (-0.1928, 0.00305), (-0.2078, 0.2381)]]
    for i,ch in enumerate('東亞銀行'):
        angle=asin((i-1.5)*1.05/r)
        t=frame(arc(angle-.02,0),arc(angle+.02,0))
        px,pz=glyph_samples[int(distant)][i]
        t('raised bank name '+ch,px,pz+6.23,'raised bronze characters',.219,.226)
    bad=[q for q in rays if not q['passed']]
    if bad:
        raise ValueError(bad)
    return {'distant':bool(distant),'triangles':len(v),'rays':rays}
