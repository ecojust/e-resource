"""Compare the model's first visible surfaces to four independent exterior photographs."""
import argparse
import hashlib
import runpy
import tempfile
import json
from pathlib import Path
import sys
import numpy as np
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
# The shared renderer casts rays into the delivered GLB and samples its real PBR materials.
RAY=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
SerialScene=runpy.run_path(str(RAY))['SerialScene']
def test_mesh(scene,signature,matrix,picks):
    inv=np.linalg.inv(matrix[:,:3]);eye=-inv@matrix[:,3];rows=[]
    for expected,points in picks.items():
        for uv in points:
            direction=inv@[*uv,1]
            hit=scene.ray(eye,direction/np.linalg.norm(direction),200)
            material=None if hit is None else hit['material']
            rows.append(dict(uv=uv,from_photo=expected,first_hit=material,matched=material is not None and expected in material))
    return dict(asset_sha256=signature,points=rows,count=len(rows),direct=sum(v['matched']for v in rows))
def render(path,out,matrix,crop):
    model_dir=PROJECT/'source/precise/xuhui-huaihai-1230-rear-courtyard-entrance/measurements'
    sys.path.insert(0,str(model_dir))
    import render_registered_entrance as runtime
    engine=runtime.ENGINE;raster=runtime.RASTER;model=raster.read_glb(path)
    with tempfile.TemporaryDirectory(dir=out.parent)as t:
        lib=engine['make_library'](Path(t));painter=engine['MaterialPass'](lib,model[1],model[2])
        transforms,ranges,depths=engine['sky_maps'](model[0],lib,raster)
        lib.set_sky(engine['SAMPLES'],engine['DEPTH_RESOLUTION'],raster.ptr(transforms),raster.ptr(ranges),raster.ptr(depths))
        projection=matrix.copy();projection[:2]+=.5*projection[2]
        width=round(690*(crop[2]-crop[0])/max(crop[2]-crop[0],crop[3]-crop[1]))
        im,_,stats=runtime.sample_view(path,model,painter,lib,projection,crop,width,np.array([-.38,-.70,.61],dtype='float32'),None,2)
        im.save(out,quality=90)
    return dict(sha256=hashlib.sha256(out.read_bytes()).hexdigest(),size=list(im.size),foreground=stats['zbuffer_foreground_pixels'])
WALL='ochre stippled roughcast';SLATE='weathered grey vents';STONE='brown dressed masonry'
FLASH='dark cornice metal';UPPER='cream lantern roughcast';SHADE='deep belfry shadow'
MEMORIAL='polished dark stone';IRON='dark cross iron'
POINTS={
 'june-court':{WALL:[(1054,459),(1141,502),(1094,595),(1030,746),(1089,876)],SLATE:[(1024,311),(1063,317),(1103,322)],SHADE:[(1035,554),(1084,707),(1135,854)],STONE:[(1067,363)],FLASH:[(1050,202)],UPPER:[(1055,173)],MEMORIAL:[(1099,1023)]},
 'may-court':{WALL:[(541,430),(654,457),(649,632),(539,751)],SLATE:[(555,301),(595,315),(634,322)],SHADE:[(552,552),(629,824)],FLASH:[(603,185)],UPPER:[(606,155)],MEMORIAL:[(584,977)]},
 'may-river':{WALL:[(1234,211),(1269,283),(1182,180)],SLATE:[(1169,235),(1187,232),(1205,223),(1251,230),(1272,233),(1293,237)],FLASH:[(1279,144)],UPPER:[(1252,104)]},
 'winter-river':{WALL:[(573,162),(590,174),(559,188)],SLATE:[(552,128),(557,126),(561,126),(576,125),(584,124),(594,126)],SHADE:[(580,192),(590,227)],UPPER:[(579,85)]}}
CROPS={'june-court':[884,62,1250,1092],'may-court':[395,3,766,1040],'may-river':[1063,1,1397,575],'winter-river':[515,35,645,275]}
def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('mesh',type=Path);cli.add_argument('out',type=Path);cli.add_argument('--render',action='store_true')
    a=cli.parse_args();a.out.mkdir(exist_ok=True,parents=True)
    scene=SerialScene(a.mesh);signature=hashlib.sha256(a.mesh.read_bytes()).hexdigest()
    stations=json.loads((HERE/'tower-stations.json').read_bytes())['stations'];results={}
    for key,c in stations.items():
        m=np.asarray(c['projection']);q=test_mesh(scene,signature,m,POINTS[key]);results[key]=q
        if a.render:q['render']=render(a.mesh,a.out/(key+'-model.jpg'),m,CROPS[key])
        print(key,q['direct'],q['count'],[(p['uv'],p['from_photo'],p['first_hit'])for p in q['points']if not p['matched']],flush=True)
    (a.out/(a.mesh.stem+'-four-stations.json')).write_text(json.dumps(results,indent=2)+'\n')
if __name__=='__main__':main()
