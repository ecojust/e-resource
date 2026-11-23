"""Render the model from the same camera and crop as the institutional and newspaper photographs."""
from pathlib import Path
import argparse
import json
import hashlib
import sys
import tempfile
import numpy as np
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').exists())
RENDER=PROJECT/'source/precise/xuhui-huaihai-1230-rear-courtyard-entrance/measurements'
sys.path.insert(0,str(RENDER))
import render_registered_entrance as engine
CROPS={'court':[0,0,1000,745],'street':[0,0,1080,810],'school-court':[0,0,639,426]}
def draw(mesh,directory,views):
    lit=engine.ENGINE;raster=engine.RASTER;geometry=raster.read_glb(mesh)
    stations=json.loads((HERE/'tower-stations.json').read_bytes())['stations']
    if 'school-court' in views:stations['school-court']=json.loads((HERE/'school-court-station.json').read_bytes())
    directory.mkdir(parents=True,exist_ok=True);report={}
    with tempfile.TemporaryDirectory(dir=directory)as tmp:
        lib=lit['make_library'](Path(tmp));paint=lit['MaterialPass'](lib,geometry[1],geometry[2])
        transforms,ranges,depth=lit['sky_maps'](geometry[0],lib,raster)
        lib.set_sky(lit['SAMPLES'],lit['DEPTH_RESOLUTION'],raster.ptr(transforms),raster.ptr(ranges),raster.ptr(depth))
        for key in views:
            station=stations[key]
            m=np.array(station['P'],float);x,y,r,b=CROPS[key]
            m[0]+=(.5-x)*m[2];m[1]+=(.5-y)*m[2]
            # Camera and crop both use pixel centres. The shadow shader unprojects these same coordinates.
            light=np.asarray([-.42,.54,.73] if key=='court' else [-.45,-.50,.74],np.float32)
            img,_,stats=engine.sample_view(mesh,geometry,paint,lib,m,(0,0,r-x,b-y),800,light,None,2)
            dest=directory/(key+'-model.jpg');img.save(dest,quality=94)
            report[key]=dict(sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),size=img.size,foreground=stats['zbuffer_foreground_pixels'],photo_crop_xyxy=CROPS[key],source_pixel_projection=station['P'])
    return report
if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('mesh',type=Path);cli.add_argument('directory',type=Path);cli.add_argument('views',nargs='+',choices=list(CROPS))
    a=cli.parse_args();result=draw(a.mesh,a.directory,a.views)
    dest=a.directory/('daylight-'+'-'.join(a.views)+'.json')
    dest.write_text(json.dumps(dict(mesh_sha256=hashlib.sha256(a.mesh.read_bytes()).hexdigest(),views=result),indent=2)+'\n')
