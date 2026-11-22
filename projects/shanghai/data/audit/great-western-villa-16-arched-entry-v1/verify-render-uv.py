"""Check the actual UV registration of WQL's embossed panel and the small bilingual plaque."""
import argparse,hashlib,json,runpy
from pathlib import Path
import numpy as np
AUDIT=Path(__file__).absolute().parent.parent
SOURCE=AUDIT.parents[1]/'source/precise/changning-great-western-villa-16-arched-entry'
reader=runpy.run_path(AUDIT/'postal-office-v1/independent-glb-review-helpers.py')['load_triangles']
textures=runpy.run_path(AUDIT/'fifth-textile-warehouse-river-front-v1/inspect-export.py')['load_textures']
def inspect(path):
    tri,index,names,_=reader(path);loaded,embedded,uv,_=textures(path,index)
    reg=json.loads((SOURCE/'measurements/entrance-camera.json').read_bytes());plate=json.loads((SOURCE/'measurements/letterbox-relief.json').read_bytes())
    m=names.index('Relief plaque from WQL photograph');assert set(embedded)=={m}
    info=embedded[m];digest=hashlib.sha256((SOURCE/'source/letterbox-relief-atlas.png').read_bytes()).hexdigest();assert info['embedded_sha256']==digest and info['texture_dimensions']==[352,624]
    c=np.array(reg['plaque_corners_enu']);t=c[1]-c[0];w=np.linalg.norm(t);t/=w;h=c[0,2]-c[3,2];n=np.cross(t,[0,0,1.])
    selected=tri[index==m];coords=uv[index==m]
    mask=coords[:,:,1].max(axis=1)<.85;xyz=selected[mask]-c[0];u=(xyz@t)/w;v=-xyz[:,:,2]/h
    expected=np.stack([(16.5+u*319)/352,(12.5+v*511)/624],axis=2)
    error=float(np.max(abs(coords[mask]-expected)));assert error<.00016,error
    labelcoords=coords[~mask].reshape(-1,2);assert len(labelcoords)==36
    assert np.isclose(labelcoords.min(axis=0),[18.5/352,548.5/624],atol=.0001).all()
    assert np.isclose(labelcoords.max(axis=0),[333.5/352,609.5/624],atol=.0001).all()
    depth=xyz@n;assert depth.min()<-.033 and depth.max()>.017
    return dict(triangles=len(selected),panel_triangles=int(mask.sum()),nameplate_triangles=int((~mask).sum()),physical_relief_depth_range_m=[float(depth.min()),float(depth.max())],maximum_uv_error=error,embedded_texture_sha256=digest,
        source_author='WQL',photo_sha256=plate['photo_sha256'],license='CC BY-SA 4.0',atlas_size=info['texture_dimensions'],sampler=loaded[m][1])
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ['raw','full','lod','output']:p.add_argument(k,type=Path)
    a=p.parse_args();r={k:inspect(getattr(a,k))for k in ('raw','full','lod')};a.output.write_text(json.dumps(r,indent=2)+'\n')
