"""Cast independent material rays from the frontal visitor-agency photograph."""
import argparse,json,sys,hashlib,runpy,tempfile
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[3]
from frontage import matrix
RAY=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
CROPS={'lawn':[1,103,1149,459]}
CHECKS={'grey ashlar':[(162,249),(342,272),(484,278),(647,255),(810,271),(980,277),(1050,361)],
        'smoky casement glass':[(57,261),(132,264),(204,258),(251,268),(312,259),(362,263),(425,268),(449,262),(528,263),(582,259),(610,258),(687,267),(741,264),(780,261),(845,262),(901,266),(936,262),(1016,260),(1090,260),(1016,327),(1088,327)],
        'rust red pantile':[(339,147),(462,156),(684,154),(790,151),(905,160)],
        'dark oak':[(551,403),(575,412),(606,408)],
        'deep blue stained glass':[(575,359)],
        'muted violet glazing':[(547,359),(607,360)]}
def render(path,out,m,crop):
    measure=PROJECT/'source/precise/xuhui-huaihai-1230-rear-courtyard-entrance/measurements'
    sys.path.insert(0,str(measure));import render_registered_entrance as engine
    lit=engine.ENGINE;raster=engine.RASTER;model=raster.read_glb(path)
    with tempfile.TemporaryDirectory(dir=out.parent)as t:
        lib=lit['make_library'](Path(t));painter=lit['MaterialPass'](lib,model[1],model[2])
        transforms,ranges,depth=lit['sky_maps'](model[0],lib,raster);lib.set_sky(lit['SAMPLES'],lit['DEPTH_RESOLUTION'],raster.ptr(transforms),raster.ptr(ranges),raster.ptr(depth))
        # The sky shader reconstructs world positions from crop-local pixels.
        # Apply the crop to the principal point before both rasterization and its inverse.
        proj=m.copy();proj[0]+=(.5-crop[0])*proj[2];proj[1]+=(.5-crop[1])*proj[2]
        local_crop=(0,0,crop[2]-crop[0],crop[3]-crop[1])
        pixels=800 if crop[2]-crop[0]>crop[3]-crop[1]else 450
        im,_,stats=engine.sample_view(path,model,painter,lib,proj,local_crop,pixels,np.array([-.38,-.68,.62],dtype=np.float32),None,2);im.save(out,quality=91)
        return dict(size=list(im.size),sha256=hashlib.sha256(out.read_bytes()).hexdigest(),foreground=stats['zbuffer_foreground_pixels'])
def measure(scene,m,checks):
    inv=np.linalg.inv(m[:,:3]);eye=-inv@m[:,3];rows=[]
    def first(uv):
        direction=inv@[*uv,1];v=scene.ray(eye,direction/np.linalg.norm(direction),350)
        return v['material'] if v else None
    for material,points in checks.items():
        for u,v in points:
            actual=first((u,v));direct=actual is not None and material in actual
            nearest=0. if direct else None
            if not direct:
                for d,dx,dy in sorted((a*a+b*b,a,b)for a in range(-4,5)for b in range(-4,5)if 0<a*a+b*b<=16):
                    q=first((u+dx,v+dy))
                    if q and material in q:nearest=float(np.sqrt(d));break
            rows.append(dict(pixel=[u,v],expected=material,first_hit=actual,direct=direct,nearest_px=nearest))
    return dict(points=rows,direct=sum(x['direct']for x in rows),count=len(rows))
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mesh',type=Path);ap.add_argument('out',type=Path);ap.add_argument('--render',action='store_true');a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=True);scene=runpy.run_path(str(RAY))['SerialScene'](a.mesh);m=np.array(matrix()['projection']);rows=measure(scene,m,CHECKS)
    if a.render:rows['render']=render(a.mesh,a.out/'lawn-model.jpg',m,CROPS['lawn'])
    (a.out/(a.mesh.stem+'-lawn-rays.json')).write_text(json.dumps(rows,indent=2)+'\n');print(rows['direct'],rows['count'],[(v['pixel'],v['first_hit'],v['nearest_px'])for v in rows['points']if not v['direct']])
