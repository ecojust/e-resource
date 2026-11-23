"""Compute nine z-buffer views and verify the three authoring cameras against their registered matrices."""
import argparse
import ctypes
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from unittest.mock import patch

import numpy as np
from PIL import Image, ImageChops, ImageDraw

HERE=Path(__file__).absolute().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
adapter=PROJECT/'source/precise/changning-hongji-yuyuan-garden-houses-8-and-9/measurements/render-garden-stations.py'
spec=importlib.util.spec_from_file_location('garden_projected_faces',adapter)
raster=importlib.util.module_from_spec(spec)
spec.loader.exec_module(raster)
C_SOURCE=PROJECT/'source/precise/huangpu-old-jiefu-nanjing-road-shopfront/measurements/northwest_raster.c'


def camera(view):
    centre=np.array(view['eye'])
    forward=np.array(view['target'])-centre
    distance=np.linalg.norm(forward)
    forward/=distance
    up=np.asarray(view.get('world_up',[0.,0.,1.]))
    right=np.cross(forward,up)
    right/=np.linalg.norm(right)
    down=np.cross(forward,right)
    rotation=np.stack((right,down,forward))
    w,h=view['width'],view['height']
    fx=w*distance/view['width_m'];fy=fx/view.get('pixel_aspect_y',1.)
    intrinsic=np.array([[fx,0,w*.5],[0,fy,h*.5],[0,0,1.]])
    return intrinsic@rotation@np.column_stack((np.eye(3),-centre))


def verify(model,output,pixels):
    output.mkdir(exist_ok=True,parents=True)
    proof={'model_sha256':hashlib.sha256(model.read_bytes()).hexdigest(),'views':{}}
    views=json.loads((HERE.parent/'source/cameras.json').read_bytes())
    stations=json.loads((HERE/'court-cameras.json').read_bytes())['views']
    geom=raster.renderer.read_glb(model)
    targets=np.array([(x,y,z,1.) for x in [-5,-1,1,5] for y in [0,.7] for z in [1,4,7,10]])
    tile_w,tile_h=255,207
    sheet=Image.new('RGB',(3*tile_w,3*tile_h),(244,244,241))
    label=ImageDraw.Draw(sheet)
    with TemporaryDirectory() as temp:
        lib=Path(temp)/'depth-raster.so'
        subprocess.run(['cc','-O2','-shared','-fPIC',C_SOURCE,'-lm','-o',lib],check=True)
        gpu=ctypes.CDLL(str(lib))
        for index,view in enumerate(views):
            matrix=camera(view);w,h=view['width'],view['height'];name=view['name']
            sun=np.asarray([-.46,-.52,.72],dtype='float32');sun/=np.linalg.norm(sun)
            with patch.object(raster.renderer,'read_glb',return_value=raster.projected_parts(geom,matrix)):
                im,details=raster.renderer.raster(model,gpu,pixels,matrix,[0,0,w,h],sun,[221.5,46.])
            common={'camera':view,'image_px':im.size,'drawn_pixels':details['zbuffer_foreground_pixels'],
                    'material_pixel_counts':details['materials_visible_samples']}
            if 'world_up' in view:
                r=stations[view['reference'].split()[-1]]
                p=np.array(r['K'])@np.array(r['R'])@np.column_stack((np.eye(3),-np.array(r['C'])))
                predicted=targets@matrix.T;original=targets@p.T
                error=np.max(np.linalg.norm(predicted[:,:2]/predicted[:,2,None]-original[:,:2]/original[:,2,None],axis=1))
                if error>.00005:raise ValueError((name,error))
                common.update(registered_points=len(targets),maximum_interprojection_error_px=float(error))
            diff=ImageChops.difference(im,Image.new('RGB',im.size,(230,231,226)))
            bounds=diff.getbbox()
            if not bounds or common['drawn_pixels']<100:raise ValueError('Empty '+name)
            common['rendered_extent_left_top_right_bottom_px']=bounds
            if name=='overview':
                mw,mh=im.size
                margin=[bounds[0]/mw,bounds[1]/mh,(mw-bounds[2])/mw,(mh-bounds[3])/mh]
                if min(margin)<.035:raise ValueError('Overall view clips the building')
                common['overview_margins']=margin
            proof['views'][name]=common
            im.thumbnail((tile_w,tile_h-20))
            x,y=index%3*tile_w,index//3*tile_h
            sheet.paste(im,(x+(tile_w-im.width)//2,y))
            label.text((x+8,y+tile_h-16),name,fill=(45,45,40))
    sheet.save(output/'nine-camera-model-views.jpg',quality=91,subsampling=0)
    (output/'framing.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('glb',type=Path);ap.add_argument('output',type=Path)
    ap.add_argument('--pixels',type=int,default=450)
    args=ap.parse_args();verify(args.glb,args.output,args.pixels)
