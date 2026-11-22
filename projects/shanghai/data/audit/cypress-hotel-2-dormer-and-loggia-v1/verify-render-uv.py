"""Check the baked tile coordinates against the slope of the principal roof on each mesh."""
from pathlib import Path
import json,sys,runpy,hashlib
import numpy as np
AUDIT=Path(__file__).absolute().parent.parent
SRC=AUDIT.parents[1]/'source/precise/changning-cypress-hotel-2-dormer-and-loggia'
read=runpy.run_path(AUDIT/'postal-office-v1/independent-glb-review-helpers.py')['load_triangles']
texture=runpy.run_path(AUDIT/'fifth-textile-warehouse-river-front-v1/inspect-export.py')['load_textures']
def check(path):
    triangles,ids,names,_=read(path);samplers,ims,uv,_=texture(path,ids);m=names.index('Ochre roof pans with mineral speckle');assert set(ims)=={m}
    tex_sha=hashlib.sha256((SRC/'source/ochre-pan-clay.png').read_bytes()).hexdigest()
    assert ims[m]['embedded_sha256']==tex_sha and ims[m]['texture_dimensions']==[144,144]
    sampler=samplers[m][1];assert all(sampler.get(k,10497)==10497 for k in ['wrapS','wrapT'])
    points=triangles[ids==m];tex=uv[ids==m];slope=json.loads((SRC/'measurements/roof-tile-courses.json').read_bytes())['surface_slope']
    along=np.array([0.,1.,slope])/np.hypot(1.,slope);d=points[:,1:]-points[:,:1]
    err=float(max(abs(d[:,:,0]-(tex[:,1:,0]-tex[:,:1,0])*.59).max(),abs((d@along)+(tex[:,1:,1]-tex[:,:1,1])*.59).max()));assert err<.00008
    return dict(textured_triangles=len(points),textured_corners=3*len(points),embedded_sha256=tex_sha,maximum_metric_error_m=err,repeat_m=.59,texture_size=[144,144])
if __name__=='__main__':
    raw,full,lod,out=map(Path,sys.argv[1:]);out.write_text(json.dumps({r:check(f)for r,f in zip(['raw','full','lod'],[raw,full,lod])},indent=2)+'\n')
