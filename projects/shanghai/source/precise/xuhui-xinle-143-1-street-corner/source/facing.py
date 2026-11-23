"""Running-bond facing and cream roughcast on the street facade of Xinlefang No. 143-1."""
from pathlib import Path
import hashlib
import importlib.util
import json
import struct
import numpy as np
from PIL import Image
from street_portal import BRICK
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
spec=importlib.util.spec_from_file_location('xinle_pbr_export',PROJECT/'source/precise/xuhui-wanping-42-brick-window-bays/source/brick_finishes.py')
shared=importlib.util.module_from_spec(spec);spec.loader.exec_module(shared)
OBS=json.loads((HERE.parent/'measurements/brickwork-observations.json').read_bytes())
UNIT,COURSE=OBS['median_module_m']
CREAM='Xinlefang | coarse cream finish above brick'
STEMS={BRICK:'xinle-red-facing',CREAM:'xinle-cream-roughcast'}
REPEAT={BRICK:[4*UNIT,10*COURSE],CREAM:[.70,.70]}
def phase(values,pitch):
    z=np.exp(2j*np.pi*np.asarray(values)/pitch).mean()
    return (np.angle(z)*pitch/(2*np.pi))%pitch
beds=[z for p in OBS['patches'].values()for z in p['measured_bed_z_m']]
Z_PHASE=phase(beds,COURSE)
joints=[]
for p in OBS['patches'].values():
    for row in p['head_joints_by_course']:
        row_no=int(np.floor((row['z']-Z_PHASE)/COURSE))
        joints.extend(x+(row_no%2)*UNIT/2 for x in row['x'])
X_PHASE=phase(joints,UNIT)
PALETTE={name:{'color':[1.,1.,1.],'roughness':.89 if name==BRICK else .95,
               'texture':str(HERE/(stem+'.png')),'normal':str(HERE/(stem+'-normal.png'))}for name,stem in STEMS.items()}
shared.HERE=HERE;shared.STEMS=STEMS
shared.REPEAT_METRES=REPEAT
shared.NORMAL_FILENAMES={k:stem+'-normal.png'for k,stem in STEMS.items()}
def finish_materials(path,palette):
    """Bind the two normal maps and preserve the cool emission of the small shop sign."""
    report=shared.embed_normals(path)
    data=path.read_bytes()
    size=struct.unpack_from('<I',data,12)[0]
    doc=json.loads(data[20:20+size])
    for mat in doc['materials']:
        spec=palette[mat['name']]
        if 'emissive' in spec:
            mat['emissiveFactor']=spec['emissive']
    header=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode()
    header+=b' '*(-len(header)%4)
    payload=data[20+size:]
    content=struct.pack('<4sIIII',b'glTF',2,20+len(header)+len(payload),len(header),0x4e4f534a)+header+payload
    if content!=data:
        temp=path.with_suffix('.writing')
        temp.write_bytes(content)
        temp.replace(path)
        report.update(bytes=len(content),sha256=hashlib.sha256(content).hexdigest())
        path.with_suffix('.geometry.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report

def set_metric_uv(part):
    name=part['material']
    # CrownBuilder first unfolds each triangle around its actual directed wall normal.
    uv=np.asarray(part['texcoords'])/.78
    if name==BRICK:uv-=np.array([X_PHASE,Z_PHASE])
    part['texcoords']=(uv/np.asarray(REPEAT[name])).tolist()

def normal_map(height,w,h):
    rows,cols=height.shape
    dx=(np.roll(height,-1,1)-np.roll(height,1,1))*cols/(2*w)
    down=(np.roll(height,-1,0)-np.roll(height,1,0))*rows/(2*h)
    n=np.stack((-dx,down,np.ones_like(dx)),axis=-1)
    n/=np.linalg.norm(n,axis=-1,keepdims=True)
    return Image.fromarray(np.uint8(np.rint((n+1)*127.5)))

def generate():
    for mat,stem in STEMS.items():
        nx,ny=(512,352)if mat==BRICK else (224,224)
        iy,ix=np.indices((ny,nx));u=(ix+.5)/nx;v=(ny-iy-.5)/ny
        w,h=REPEAT[mat];rng=np.random.default_rng(840 if mat==BRICK else 1840)
        fine=shared.field(u,v,nx//2,ny//2,rng);mottle=shared.field(u,v,34,27,rng)
        if mat==BRICK:
            x,z=u*w,v*h;row=np.floor(z/COURSE).astype(int);shifted=x+(row%2)*UNIT/2
            dx=shifted%UNIT;dz=z%COURSE
            edge=np.minimum(np.minimum(dx,UNIT-dx),np.minimum(dz,COURSE-dz))
            edge+=.00065*mottle
            mix=np.clip((edge-.0031)/.0028,0,1);relief=mix*.0027+.00021*fine
            # Brick values come from the two well-exposed samples beside the
            # lower service pipe. Individual units carry slow baked colour variation.
            unit=(np.floor(shifted/UNIT).astype(int)%4)+(row%10)*4
            variation=rng.normal(0,3.2,40)[unit]+1.9*mottle+2.1*fine
            body=np.array([145,88,82])+variation[:,:,None]*[1,.93,.88]
            joint=np.array([199,171,165])+(1.8*fine)[:,:,None]
            rgb=joint*(1-mix[:,:,None])+body*mix[:,:,None]
        else:
            rough=np.tanh(1.25*fine)
            rgb=np.array([206,187,158])+(5.3*rough+2.4*mottle)[:,:,None]
            relief=.0009*rough+.0006*mottle
        Image.fromarray(np.uint8(np.clip(np.rint(rgb),0,255))).save(HERE/(stem+'.png'),optimize=True)
        normal_map(relief,w,h).save(HERE/(stem+'-normal.png'),optimize=True)
if __name__=='__main__':generate()
