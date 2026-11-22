"""Check the embedded, project-authored mineral atlas on every modelled terrace tile."""
import hashlib,json,runpy,sys
from pathlib import Path
import numpy as np
A=Path(__file__).resolve().parent.parent
S=A.parents[1]/'source/precise/changning-hongqiao-sanatorium-sun-terraces'
reader=runpy.run_path(A/'postal-office-v1/independent-glb-review-helpers.py')['load_triangles']
textures=runpy.run_path(A/'fifth-textile-warehouse-river-front-v1/inspect-export.py')['load_textures']

def check(path):
    tri,indices,names,_=reader(path);raw,embedded,uv,_=textures(path,indices);m=names.index('Jointed two-tone terrace paving');assert set(embedded)=={m}
    texture=embedded[m];assert texture['embedded_sha256']==hashlib.sha256((S/'source/terrace-mineral-tiles.png').read_bytes()).hexdigest() and texture['texture_dimensions']==[192,192]
    measured=json.loads((S/'measurements/terrace-frame.json').read_bytes());p=measured['estimated_tile_pitch_m'];t=tri[indices==m];tex=uv[indices==m]
    mask=(np.ptp(t[:,:,2],axis=1)<.00001)&(np.abs(t[:,:,2].mean(axis=1)-measured['floor_to_roof_z_m'][3]-.009)<1e-4)
    top=t[mask];v=tex[mask];center=top.mean(axis=1)
    ii=np.floor(center[:,0]/p+measured['grid_i_at_post_row']).astype(int);jj=np.floor(center[:,1]/p+measured['longitudinal_bounds_grid_j'][0]).astype(int)
    zone=np.column_stack([((17*ii+23*jj)//4)%2,(ii+jj)%2]);decoded=np.floor(v.mean(axis=1)*2).astype(int)
    assert np.array_equal(zone,decoded)
    corners=(v-zone[:,None,:]*.5);delta=np.minimum(abs(corners-.021),abs(corners-.478));err=float(delta.max());assert err<.00005
    from collections import Counter
    counts=Counter(zip(ii.tolist(),jj.tolist()));assert all(n==2 for n in counts.values())
    return dict(textured_triangles=len(t),textured_corners=3*len(t),top_faces=len(top),individually_jointed_tiles=len(counts),alternating_cells_all_correct=True,maximum_uv_error=err,texture_sha256=texture['embedded_sha256'],atlas_pixels=[192,192],photos_embedded=False)
if __name__=='__main__':
    files=list(map(Path,sys.argv[1:]));roles=['raw','full','lod']if len(files)==4 else['model'];assert len(files)==len(roles)+1
    r={name:check(f)for name,f in zip(roles,files)};files[-1].write_text(json.dumps(r,indent=2)+'\n');print(r)
