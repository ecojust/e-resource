"""Render the two contractor photograph stations from the delivered model without using photo pixels."""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import runpy
import sys
import tempfile
from unittest.mock import patch

import numpy as np
from PIL import Image,ImageDraw
from register_courtyard import Camera

HERE=Path(__file__).resolve().parent
PRECISE=HERE.parents[1]
SOURCE=PRECISE/'xuhui-jianguo-336-lane-one-villa/measurements/render_registered_court.py'
sys.path.insert(0,str(SOURCE.parent))
engine=runpy.run_path(str(SOURCE))
raster=engine['RASTER']
COLOURS=np.arange(256,dtype='float32')/255
LINEAR=np.where(COLOURS<=.04045,COLOURS/12.92,((COLOURS+.055)/1.055)**2.4)
SOURCE_PICTURES={'case1':'7ad4ed0d72a12e59155b97b88f7a71fe21dce7599e34c5cfa8ef49d899c9997c','case2':'3edf3374b870eaa12ba49d2c1f0f8f47781e3402fbc946701ec2114bb2dde2a1'}

def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def paint_pass(mesh,model,painter,projection):
    image_labels=[]
    original_ptr=raster.ptr
    def observe(array):
        if array.dtype==np.uint16 and array.shape==(380,580) and not image_labels:
            image_labels.append(array)
        return original_ptr(array)
    with patch.object(raster,'ptr',side_effect=observe),patch.object(raster,'read_glb',return_value=model):
        image,stats=raster.raster(mesh,painter,580,projection,(0,0,580,380),np.array([0.,-.8,.6],dtype='float32'),None)
    assert len(image_labels)==1
    return np.asarray(image,dtype='uint8'),image_labels[0],stats

def model_view(mesh,model,key,transform,lib,painter,grid):
    camera=Camera(key)
    proj=camera.P@np.linalg.inv(transform)
    # Source points index pixel centres. The shared rasterizer indexes pixel boundaries.
    screen=proj.copy();screen[:2]+=.5*screen[2]
    fields=engine['BACKEND']['projected_parts'](model,screen)
    glass={n+1:m['pbrMetallicRoughness'].get('baseColorFactor',[1,1,1,1])[3]
           for n,m in enumerate(model[1]) if m.get('alphaMode')=='BLEND'}
    opaque=([p for p in fields[0] if p[4]+1 not in glass],fields[1],fields[2])
    sums=np.zeros((380,580,3),np.float32)
    active_counts={}
    foreground=[]
    for iy in range(grid):
        for ix in range(grid):
            q=screen.copy()
            q[0]-=((ix+.5)/grid-.5)*q[2];q[1]-=((iy+.5)/grid-.5)*q[2]
            inv=np.linalg.inv(q[:,:3]);back=np.ascontiguousarray(np.c_[inv,-inv@q[:,3]],np.float32)
            shadow=np.full((380,580),-1,np.float32)
            lib.set_photo(raster.ptr(back),ctypes.c_float(1),False,raster.ptr(shadow))
            painted,ids,stats=paint_pass(mesh,fields,painter,q);rgb=LINEAR[painted]
            if any(np.any(ids==mid) for mid in glass):
                behind,_,_=paint_pass(mesh,opaque,painter,q)
                for mid,alpha in glass.items():
                    mask=(ids==mid)
                    if mask.any():
                        rgb[mask]=rgb[mask]*alpha+LINEAR[behind[mask]]*(1-alpha)
                        material=model[1][mid-1]['name']
                        active_counts[material]=active_counts.get(material,0)+int(mask.sum())
            sums+=rgb;foreground.append(stats['zbuffer_foreground_pixels'])
    mean=sums/(grid*grid)
    srgb=np.where(mean<=.0031308,12.92*mean,1.055*mean**(1/2.4)-.055)
    output=Image.fromarray(np.clip(np.rint(255*srgb),0,255).astype('uint8'))
    eye=(transform@[*camera.c,1])[:3]
    world_pts=np.array([camera.wall(p)for p in [[100,140],[240,320],[470,100],[385,165]]])
    hom=np.c_[world_pts,np.ones(len(world_pts))]@transform.T@screen.T
    projected=hom[:,:2]/hom[:,2,None]-.5
    difference=np.linalg.norm(projected-np.array([[100,140],[240,320],[470,100],[385,165]]),axis=1)
    assert difference.max()<1e-8
    return output,{'source_photo_sha256':SOURCE_PICTURES[key],'source_size':[580,380],'output_size':list(output.size),
        'model_from_photo_local':transform.tolist(),'camera_centre_model_xyz_m':eye.tolist(),'source_pixel_centre_projection':proj.tolist(),
        'raster_boundary_projection':screen.tolist(),'same_pixels_roundtrip_max_error':float(difference.max()),
        'alpha_composited_foreground_samples':active_counts,'samples_per_pixel':grid*grid,'foreground_pixels_min_max':[min(foreground),max(foreground)],
        'materials_visible_samples_one_subframe':stats['materials_visible_samples']}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mesh',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    p.add_argument('--plan',type=Path,help='3304-local-footprint.json containing both real local-to-ENU transforms')
    p.add_argument('--local',choices=['case1','case2'],help='test a single isolated fragment in its documented author coordinates')
    p.add_argument('--grid',choices=[1,2,3],default=2,type=int);args=p.parse_args()
    assert bool(args.plan)!=bool(args.local)
    out=args.output;out.mkdir(parents=True,exist_ok=True)
    plan=json.loads(args.plan.read_bytes()) if args.plan else {}
    model=raster.read_glb(args.mesh)
    records={}
    with tempfile.TemporaryDirectory(dir=out)as temp:
        lib=engine['make_library'](Path(temp));painter=engine['MaterialPass'](lib,model[1],model[2])
        # Transparent roofs tint the surfaces underneath. Their opaque metal bars
        # and all structural geometry participate in diffuse sky occlusion.
        opaque=[p for p in model[0] if model[1][p[4]].get('alphaMode')!='BLEND']
        views,ds,depth=engine['sky_maps'](opaque,lib,raster)
        lib.set_sky(engine['SAMPLES'],engine['DEPTH_RESOLUTION'],raster.ptr(views),raster.ptr(ds),raster.ptr(depth))
        for key in ([args.local] if args.local else ['case1','case2']):
            transform=np.eye(4) if args.local else np.array(plan['facade_frames'][key]['local_to_ENU'])
            image,record=model_view(args.mesh,model,key,transform,lib,painter,args.grid)
            f=out/(key+'-model.jpg');image.save(f,quality=95,subsampling=0,optimize=True)
            record.update(file=f.name,sha256=sha(f));records[key]=record
    report={'model':args.mesh.name,'sha256':sha(args.mesh),'camera_sha256':sha(HERE/'courtyard-cameras.json'),'plan_sha256':sha(args.plan) if args.plan else None,
       'source_page':'http://www.shwfjz.com/showcase/3/','image_content':'Original model-only renders. Source photographs were not read by this program. Diffuse sky lighting approximates observation conditions. The cyan canopy sheets use the linear-space alpha value encoded in the actual GLB.','views':records}
    if not args.local:
        sheet=Image.new('RGB',(1168,420),'#eeeae3');d=ImageDraw.Draw(sheet)
        for i,key in enumerate(records):
            with Image.open(out/records[key]['file'])as im:sheet.paste(im,(4+584*i,4))
            d.text((10+584*i,391),'Contractor view '+str(i+1)+' / registered model',fill='#24272a')
        target=out/'courtyard-model-views.jpg';sheet.save(target,quality=94,subsampling=0);report['sheet']={'file':target.name,'sha256':sha(target)}
    (out/'registered-renders.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(report['sha256'],list(records))
if __name__=='__main__':main()
