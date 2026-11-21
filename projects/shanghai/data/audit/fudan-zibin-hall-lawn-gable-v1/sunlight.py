"""Cast a second depth buffer through the serialized gable, piers, rail and turned balusters."""
import ctypes,hashlib,math,runpy,subprocess,tempfile
from pathlib import Path
import numpy as np
from PIL import Image

HERE=Path(__file__).absolute().parent
SHARED=runpy.run_path(HERE.parent/'fifth-textile-warehouse-river-front-v1/inspect-export.py')
unit=SHARED['unit']


def cast_shadows(mesh,output,report):
    reader,raster=SHARED['helpers']()
    tri,_,_,_=runpy.run_path(reader)['load_triangles'](mesh)
    width,height=report['image_size'];tags=np.arange(1,len(tri)+1,dtype=np.int32)
    clips=np.zeros(len(tri),np.int32);mask=np.zeros(4)
    light=unit(np.array([.65,-.83,1.15]));target=(tri.min(axis=(0,1))+tri.max(axis=(0,1)))*.5
    light_eye=target+65*light
    with tempfile.TemporaryDirectory(prefix='zibin-hall-sky-')as tmp:
        so=Path(tmp)/'raster.so';subprocess.run(['c++','-O2','-shared','-fPIC',raster,'-o',so],check=True)
        draw=ctypes.CDLL(str(so)).draw;vp=ctypes.c_void_p;draw.restype=None
        draw.argtypes=[ctypes.c_int,ctypes.c_int,ctypes.c_double,ctypes.c_double,ctypes.c_double,ctypes.c_int,vp,vp,vp,vp,ctypes.c_int,vp,vp]
        def project(eye,focus,res,span):
            w,h=res;ray=unit(focus-eye);right=unit(np.cross(ray,[0.,0.,1.]));up=np.cross(right,ray)
            focal=w*np.linalg.norm(focus-eye)/span;axes=np.stack([right,up,ray],axis=1)
            coord=np.zeros((len(tri),3,5));coord[:,:,:3]=(tri-eye)@axes
            depth=np.zeros((h,w),np.float32);hits=np.zeros((h,w),np.int32)
            draw(w,h,w/2,h/2,focal,len(tri),coord.ctypes.data,tags.ctypes.data,clips.ctypes.data,mask.ctypes.data,0,depth.ctypes.data,hits.ctypes.data)
            return depth,hits,axes,focal
        side=1280;shadow,light_faces,axes,fl=project(light_eye,target,(side,side),29.)
        for view in report['views']:
            eye=np.array(view['eye']);dest=np.array(view['target'])
            depth,camera_faces,camera,f=project(eye,dest,(width,height),view['width_m_at_target'])
            yy,xx=np.nonzero(depth>0)
            cam=np.stack([(xx+.5-width/2)/f,(height/2-yy-.5)/f,np.ones(len(xx))],axis=1)
            world=eye+(cam@camera.T)/depth[yy,xx,None]
            lp=(world-light_eye)@axes
            x=side/2+fl*lp[:,0]/lp[:,2];y=side/2-fl*lp[:,1]/lp[:,2]
            assert np.min(x)>2 and np.min(y)>2 and np.max(x)<side-3 and np.max(y)<side-3
            receiving=camera_faces[yy,xx]-1
            edges=tri[receiving]
            normal=np.cross(edges[:,1]-edges[:,0],edges[:,2]-edges[:,0])@axes
            plane=np.sum(normal*lp,axis=1)
            visible=np.zeros(len(x))
            for dx,dy in ((0,0),(-1,-1),(1,-1),(-1,1),(1,1)):
                ix=(x+dx).astype(int);iy=(y+dy).astype(int)
                nearest=shadow[iy,ix];sample_dir_x=(ix+.5-side/2)/fl;sample_dir_y=(side/2-iy-.5)/fl
                divisor=normal[:,0]*sample_dir_x+normal[:,1]*sample_dir_y+normal[:,2]
                expected=np.divide(plane,divisor,out=lp[:,2].copy(),where=abs(divisor)>1e-12)
                expected=np.clip(expected,lp[:,2]-.18,lp[:,2]+.18)
                visible+=((nearest*(expected-.008)<=1.)|(light_faces[iy,ix]==receiving+1))
            visible/=5
            path=output/view['image'];initial=path.read_bytes()
            pix=np.asarray(Image.open(path).convert('RGB')).copy()
            color=SHARED['srgb_to_linear'](pix[yy,xx]/255)
            multiplier=.60+.40*visible
            pix[yy,xx]=np.rint(255*np.clip(SHARED['linear_to_srgb'](color*multiplier[:,None]),0,1)).astype('uint8')
            Image.fromarray(pix).save(path,quality=93)
            view['unshadowed_image_sha256']=hashlib.sha256(initial).hexdigest()
            view['image_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
            view['occluded_visible_surface_pixels']=int(np.sum(visible<.5))
            view['shadow_factor_sha256']=hashlib.sha256(visible.astype('f4').tobytes()).hexdigest()
    report['studio_sun']=dict(direction_enu=light.tolist(),shadow_map_resolution=side,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),method='Five light-depth comparisons using the receiving triangle plane at each tested pixel centre, 8 mm bias and 60 percent ambient fill.')
    assert sum(i['occluded_visible_surface_pixels']for i in report['views'])>500
