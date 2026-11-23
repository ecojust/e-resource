"""Test interior strokes and the open counter of 9 at eight independently read 2017 pixels."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

from check_photographic_surfaces import Camera, HERE, LOAD, Projected

def top_enamel_components(data, cam):
    tri, ids, names, _ = data
    enamel = 'Wukang street plaque | pale enamel lettering'
    if enamel not in names:
        return []
    points = (tri[ids == names.index(enamel)] - cam.origin) @ cam.basis
    vertices,index = np.unique(np.round(points.reshape(-1,3),5),axis=0,return_inverse=True)
    faces=index.reshape(-1,3)
    graph=coo_matrix((np.ones(faces.size), (faces.ravel(), np.roll(faces,-1,axis=1).ravel())),
                     shape=(len(vertices),len(vertices))).tocsr()
    n,labels=connected_components(graph,directed=False)
    parts=[]
    for i in range(n):
        subset=vertices[labels==i,:2]
        low,high=subset.min(axis=0),subset.max(axis=0)
        parts.append({'u_min':float(low[0]),'z_min':float(low[1]),'u_max':float(high[0]),'z_max':float(high[1])})
    # The three highest separate pale solids are the upper number row. Reading
    # left to right distinguishes the hits without using authored glyph outlines.
    top=sorted(parts,key=lambda v:v['z_max'],reverse=True)[:3]
    for k,component in zip('129',sorted(top,key=lambda v:v['u_min'])):
        component['numeral']=k
    return top

def inspect(mesh):
    data=LOAD(mesh)
    camera=Camera(2017)
    scene=Projected(data,camera)
    controls=HERE/'plaque-numeral-visibility-pixels.json'
    observations=json.loads(controls.read_bytes())
    parts=top_enamel_components(data,camera)
    pixels=[s['original_pixel'] for s in observations['samples']]
    checks=[]
    for sample,hit in zip(observations['samples'],scene.profile(pixels)):
        material=hit['material'] if hit else None
        role=sample['role']
        glyph=None
        if role=='pale' and hit:
            u,z,_=hit['u_z_d']
            glyph=next((p['numeral'] for p in parts if p['u_min']<=u<=p['u_max'] and p['z_min']<=z<=p['z_max']),None)
        passed=(role=='pale' and material=='Wukang street plaque | pale enamel lettering' and glyph==sample['name'][0]
                or role=='green' and material=='address green'
                or role=='wood' and material is not None and ('wood' in material or 'joinery' in material))
        checks.append({**sample,'first_hit':hit,'connected_enamel_solid':glyph,'matched':passed})
    return {'model':data[3],'control_sha256':hashlib.sha256(controls.read_bytes()).hexdigest(),'source':observations['source'],
            'top_connected_glyph_bounds_uz_m':parts,'checks':checks,'exact_hits':sum(s['matched'] for s in checks),'tested':len(checks),
            'limits':observations['limits']}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mesh',type=Path)
    parser.add_argument('report',type=Path)
    args=parser.parse_args()
    args.report.write_text(json.dumps(inspect(args.mesh),ensure_ascii=False,indent=2)+'\n')
