"""Compare original metric painted-wood coordinates and test the underlying glazing coverage."""
from pathlib import Path
import hashlib,json,runpy,sys,numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).absolute().parent;BASE=HERE.parent;SRC=HERE.parents[2]/'source/precise/jingan-liang-residence-arched-iron-window'
read=runpy.run_path(BASE/'postal-office-v1/independent-glb-review-helpers.py')['load_triangles']
texture=runpy.run_path(BASE/'fifth-textile-warehouse-river-front-v1/inspect-export.py')['load_textures']
camera=json.loads((SRC/'measurements/window-camera.json').read_bytes())
def inspect(p):
    t,idx,materials,_=read(p);samplers,embed,uv,_=texture(p,idx)
    m=materials.index('Weathered red timber frame');assert set(embed)=={m};digest=hashlib.sha256((SRC/'source/liang-weathered-frame.png').read_bytes()).hexdigest();assert embed[m]['embedded_sha256']==digest and embed[m]['texture_dimensions']==[176,176]
    assert all(samplers[m][1].get(key,10497)==10497 for key in ['wrapS','wrapT'])
    points=t[idx==m];data=uv[idx==m];d=points[:,1:]-points[:,:1];norm=np.cross(d[:,0],d[:,1]);axis=np.argmax(abs(norm),axis=1)
    xu=np.where((axis==0)[:,None],d[:,:,1],d[:,:,0]);zv=np.where((axis==2)[:,None],d[:,:,1],d[:,:,2])
    err=float(max(abs(xu-(data[:,1:,0]-data[:,:1,0])*.49).max(),abs(zv+(data[:,1:,1]-data[:,:1,1])*.49).max()));assert err<.00012
    eye=np.asarray(camera['eye_xyz']);w=camera['nominal_outer_frame_width_m'];h=camera['derived_outer_frame_height_m']
    # Render the union of all non-iron triangles at twice the rectification
    # resolution. Openings in the iron must see a real rebate, glass or timber.
    skin=t[idx!=materials.index('Oxide on the window grille')];scale=-eye[1]/(skin[:,:,1]-eye[1]);x=eye[0]+(skin[:,:,0]-eye[0])*scale;z=eye[2]+(skin[:,:,2]-eye[2])*scale
    pix=np.stack([960*(x/w+.5),1750*(1-z/h)],axis=-1);im=Image.new('1',(960,1750));draw=ImageDraw.Draw(im)
    for tri in pix:draw.polygon([tuple(q)for q in tri],fill=1)
    coverage=np.array(im);counts={}
    for key,x0,y0,x1,y1 in [('tall',39,36,440,624),('lower',38,662,441,844)]:
        data=coverage[2*y0:2*y1,2*x0:2*x1];counts[key]={'sampled_pixels':data.size,'uncovered':int((~data).sum())};assert data.all(),counts
    return dict(textured_triangles=len(points),textured_corners=3*len(points),max_metric_error_m=err,physical_repeat_m=.49,texture_sha256=digest,coverage=counts)
if __name__=='__main__':
    files=list(map(Path,sys.argv[1:]));names=['raw','full','lod']if len(files)==4 else['model'];assert len(files)==len(names)+1
    r={k:inspect(p)for k,p in zip(names,files[:-1])};files[-1].write_text(json.dumps(r,indent=2)+'\n');print({k:v['coverage']for k,v in r.items()})
