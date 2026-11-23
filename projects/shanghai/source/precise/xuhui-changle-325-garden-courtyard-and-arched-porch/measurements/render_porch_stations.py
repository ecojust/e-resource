"""Render the courtyard and porch mesh at two registered photographic stations without reading source photograph pixels."""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import runpy
import sys
import tempfile
import numpy as np
from PIL import Image,ImageDraw

HERE=Path(__file__).resolve().parent
SHARED=HERE.parents[1]/'xuhui-huaihai-1230-rear-courtyard-entrance/measurements'
sys.path.insert(0,str(SHARED))
engine=runpy.run_path(str(SHARED/'render_registered_entrance.py'))
lighting,raster=engine['ENGINE'],engine['RASTER']
class PorchMaterialPass(lighting['MaterialPass']):
    """Composite the single sheet of door glass over the geometry drawn behind it."""
    def paint(self,*args):
        material=self.materials[args[8]]
        if material.get('alphaMode') != 'BLEND':
            return super().paint(*args)
        width,height=int(args[3]),int(args[4])
        count=width*height
        depth=np.ctypeslib.as_array(ctypes.cast(args[5],ctypes.POINTER(ctypes.c_float)),shape=(count,))
        label=np.ctypeslib.as_array(ctypes.cast(args[6],ctypes.POINTER(ctypes.c_uint16)),shape=(count,))
        rgb=np.ctypeslib.as_array(ctypes.cast(args[7],ctypes.POINTER(ctypes.c_uint8)),shape=(count*3,)).reshape(count,3)
        old_depth=depth.copy()
        backdrop=rgb.copy()
        super().paint(*args)
        changed=(label==args[8]+1)&(depth!=old_depth)
        if changed.any():
            alpha=material['pbrMetallicRoughness']['baseColorFactor'][3]
            scale=np.arange(256,dtype=float)/255
            linear=np.where(scale<=.04045,scale/12.92,((scale+.055)/1.055)**2.4)
            values=alpha*linear[rgb[changed]]+(1-alpha)*linear[backdrop[changed]]
            srgb=np.where(values<=.0031308,12.92*values,1.055*values**(1/2.4)-.055)
            rgb[changed]=np.clip(np.rint(srgb*255),0,255).astype(np.uint8)
            self.blended_samples+=int(changed.sum())


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()
def render(mesh,out,width,grid,stations=('fayhoo','3-1504-171')):
    out.mkdir(exist_ok=True,parents=True)
    path=HERE/'wing-cameras.json';cameras=json.loads(path.read_bytes())['cameras']
    parts,mats,textures=raster.read_glb(mesh)
    parts=sorted(parts,key=lambda p:mats[p[4]].get('alphaMode')=='BLEND')
    model=(parts,mats,textures)
    info={'mesh_sha256':digest(mesh),'camera_sha256':digest(path),'photos_embedded':False,'views':{}}
    panels=[]
    with tempfile.TemporaryDirectory(dir=out) as tmp:
        lib=lighting['make_library'](Path(tmp));painter=PorchMaterialPass(lib,model[1],model[2])
        painter.blended_samples=0
        views,ranges,depth=lighting['sky_maps'](model[0],lib,raster)
        lib.set_sky(lighting['SAMPLES'],lighting['DEPTH_RESOLUTION'],raster.ptr(views),raster.ptr(ranges),raster.ptr(depth))
        for key in stations:
            start_samples=painter.blended_samples
            cam=cameras[key];w,h=cam['size']
            projection=np.array(cam['P'],dtype=float)
            projection[:2]+=.5*projection[2]
            pic,flat,stats=engine['sample_view'](mesh,model,painter,lib,projection,(0,0,w,h),width,
                                 np.array([.15,-.72,.68],dtype='float32'),None,grid)
            label={'fayhoo':'Courtyard, 4 April 2015','3-1504-171':'Street, April 2015'}.get(key,key)
            name={'fayhoo':'courtyard-2015-model.jpg','3-1504-171':'street-april-2015-model.jpg'}[key]
            pic.save(out/name,quality=94,subsampling=0,optimize=True)
            info['views'][key]={'file':name,'sha256':digest(out/name),'source_dimensions':[w,h],
                                'dimensions':list(pic.size),'foreground':stats['zbuffer_foreground_pixels'],
                                'visible_materials':stats['materials_visible_samples'],
                                'door_glass_composited_samples':painter.blended_samples-start_samples}
            tile=pic.copy();tile.thumbnail((500,315));panels.append((label,tile))
    sheet=Image.new('RGB',(510*len(panels),346),'#e6e1d8');d=ImageDraw.Draw(sheet)
    for i,(label,im) in enumerate(panels):
        sheet.paste(im,(i*510+(510-im.width)//2,4+(315-im.height)//2))
        d.text((i*510+12,324),'Registered model view / '+label,fill='#282724')
    f=out/'courtyard-stations-model.jpg';sheet.save(f,quality=94,subsampling=0)
    info['sheet']={'file':f.name,'sha256':digest(f)}
    (out/'registered-renders.json').write_text(json.dumps(info,indent=2,ensure_ascii=False)+'\n')
    return info
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mesh',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--width',default=900,type=int);p.add_argument('--grid',choices=[1,2,3],default=2,type=int)
    p.add_argument('--stations',nargs='+',default=['fayhoo','3-1504-171']);a=p.parse_args();r=render(a.mesh,a.output,a.width,a.grid,a.stations)
    print(r['mesh_sha256'],r['sheet']['sha256'])
