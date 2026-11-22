"""Check the three released museum meshes against the portal photograph and inscription measurements."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys
import numpy as np

def measured_letters(project, source, mesh):
    sys.path[:0]=[str(source),str(project/"source/precise/hongkou-general-post-office/source/common")]
    from photo_plane import CAMERAS
    from museum_sign import METAL
    tools=runpy.run_path(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py')
    triangles,indices,names,_=tools['load_triangles'](mesh)
    metal=triangles[indices==names.index(METAL)]
    points=metal.reshape(-1,3)
    # Front-face vertices of the cast lettering, excluding the rear where
    # perspective shifts the edge slightly sideways on a thick character.
    yfront=points[:,1].min()
    points=points[points[:,1]<yfront+.002]
    q=np.column_stack((points,np.ones(len(points))))@CAMERAS['close'].T
    pixels=q[:,:2]/q[:,2,None]
    sheet=json.loads((source.parent/'measurements/museum-sign-layout.json').read_bytes())
    by_glyph=[];centres=[np.mean(np.array(g['source_quad_px'])[:,0])for g in sheet['characters']]
    index=np.argmin(abs(pixels[:,0,None]-np.array(centres)),axis=1)
    for i,g in enumerate(sheet['characters']):
        ps=pixels[index==i];target=np.array(g['source_quad_px'])
        actual=np.r_[ps.min(axis=0),ps.max(axis=0)];expected=np.r_[target.min(axis=0),target.max(axis=0)]
        off=(actual-expected).round(2)
        by_glyph.append({'character':g['character'],'source_box':expected.round(2).tolist(),'projected_box':actual.round(2).tolist(),'edge_errors_source_px':off.tolist(),'max_error_source_px':float(np.max(abs(off)))})
    return by_glyph

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('project','source','packaged','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();verify=runpy.run_path(Path(__file__).with_name('check-portal-carvings.py'))['check']
    result={}
    for role,name in [('raw','raw'),('full','decoded-full'),('lod','decoded-lod')]:
        mesh=a.packaged/(name+'.glb');r=verify(a.project,a.source,mesh,False)
        with (a.packaged/(role+'.glb')).open('rb')as f:r['delivered_sha256']=hashlib.file_digest(f,'sha256').hexdigest()
        r['museum_name_positions']=measured_letters(a.project,a.source,mesh)
        result[role]=r
        print(role,sum(s['passed']for s in r['points']),sum(s['passed']for s in r['hollows']),[q['max_error_source_px']for q in r['museum_name_positions']],flush=True)
    a.output.write_text(json.dumps({'roles':result,'photo':'Architectural archive, south entrance, 16 August 2014','scope':'40 visible inscription, ribbon and open backing locations; four visible fruit hollows compared to their rims; projected extents of the seven editable substitute glyphs.'},ensure_ascii=False,indent=1)+'\n')
    for r in result.values():
        if not all(s['passed']for s in r['points']+r['hollows']) or max(q['max_error_source_px']for q in r['museum_name_positions'])>3.5:raise SystemExit(1)
