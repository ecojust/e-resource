"""Verify the first actual streetward surface and depth at architectural sections."""
import numpy as np

SECTIONS = [('left shaft', -2.12, 3.5, 'Pale granite columns', -0.3401), ('right shaft', 2.12, 6.7, 'Pale granite columns', -0.3013), ('capital abacus', 2.12, 8.61, 'Pale stone frames', -0.42), ('left square plinth', -2.12, 0.9, 'Pale granite columns', -0.5), ('balustrade cap', 0.08, 5.84, 'Pale stone frames', 0.13), ('stone baluster', 0, 5.45, 'Pale stone frames', 0.2539), ('balustrade clear gap', 0.153, 5.45, 'Shaded casement glass', 2.806), ('central door stile', 0, 2.28, 'Stained mahogany', 2.711), ('door glazing', 0.2, 2.32, 'Shaded casement glass', 2.806), ('door timber lower panel', 0.2, 1.24, 'Stained mahogany', 2.772), ('left bay spandrel', -8.0, 4.55, 'Grey stone panels', -0.605), ('right bay spandrel', 8.15, 4.55, 'Grey stone panels', -0.605), ('ground floor bay glazing', 8.0, 2.11, 'Shaded casement glass', -0.384), ('upper bay glazing', 8.0, 6.65, 'Shaded casement glass', -0.384), ('rusticated outer pier', 10.54, 3.04, 'Warm grey dressed stucco', 0.0), ('left outer pier', -10.53, 3.04, 'Warm grey dressed stucco', 0.0), ('cornice field', 0.02, 8.93, 'Warm grey dressed stucco', -0.27), ('dentil level', 0.03, 9.46, 'Pale stone frames', -0.53), ('west upper sash', -8.4, 10.28, 'Shaded casement glass', 0.936), ('east upper sash', 8.4, 10.28, 'Shaded casement glass', 0.936), ('rear door far from stair', 3.35, 3.11, 'Stained mahogany', 2.711), ('inner left wall', -3.2, 7.12, 'Shaded casement glass', 2.806), ('stone step', 0, 0.12, 'Pale stone frames', -2.373), ('stone step nosing', 0, 0.139, 'Pale stone frames', -2.373), ('left threshold plinth', -1.37, 0.91, 'Brown grey entrance granite', -0.61)]

def hit(t,m,o,d):
 v1=t[:,1]-t[:,0];v2=t[:,2]-t[:,0];p=np.cross(np.broadcast_to(d,v2.shape),v2);det=(v1*p).sum(1);ok=np.abs(det)>1e-9;iv=np.zeros_like(det);iv[ok]=1/det[ok];s=o-t[:,0];u=iv*(s*p).sum(1);q=np.cross(s,v1);v=iv*(q*d).sum(1);r=iv*(v2*q).sum(1);ok&=(u>=-1e-9)&(v>=-1e-9)&(u+v<=1+1e-9)&(r>1e-6);ix=np.flatnonzero(ok)
 if len(ix)==0:return None
 i=ix[np.argmin(r[ix])];return str(m[i]),(o+d*r[i]).tolist()

def check_triangles(triangles, materials, distant):
    records = []
    for name, x, z, material, depth in SECTIONS:
        origin = np.array([x, -5.0, z])
        result = hit(triangles, materials, origin, np.array([0., 1., 0.]))
        assert result and result[0] == material and abs(result[1][1] - depth) < .045, (name, result, material, depth)
        records.append(dict(feature=name, x_m=x, z_m=z, first_material=material, first_y_m=result[1][1], reference_y_m=depth))
    return dict(triangles=len(triangles), far=distant, rays=records)
