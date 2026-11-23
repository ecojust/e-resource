"""Procedural coloured and normal maps for lime render, casting, blue-black metal and red tile."""
import importlib.util,json
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter
from PIL import Image
HERE=Path(__file__).absolute().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
common=PROJECT/'source/precise/xuhui-wanping-42-brick-window-bays/source/brick_finishes.py'
spec=importlib.util.spec_from_file_location('gallery_material_writer',common);writer=importlib.util.module_from_spec(spec);spec.loader.exec_module(writer)
STEMS={'scored pale render':'lime-render','off-white cast moulding':'pale-cast-line','blue-black canopy metal':'canopy-metal','warm red entrance tile':'red-entrance-tile'}
NORMAL_FILENAMES={k:v+'-normal.png'for k,v in STEMS.items()}
REPEAT_METRES=dict(zip(STEMS,[(.46,.46),(.42,.42),(.61,.61),(.86,.63)]))
writer.HERE=HERE;writer.STEMS=STEMS;writer.NORMAL_FILENAMES=NORMAL_FILENAMES;writer.REPEAT_METRES=REPEAT_METRES
PALETTE={k:dict(color=[1,1,1],texture=str(HERE/(v+'.png')),normal=str(HERE/NORMAL_FILENAMES[k]),roughness=r)for (k,v),r in zip(STEMS.items(),[.92,.79,.63,.87])}
def metric_uv(part):
    part['texcoords']=(np.asarray(part['texcoords'])/(.78*np.asarray(REPEAT_METRES[part['material']]))).tolist()
def generate():
    readings=json.loads((HERE.parent/'measurements/finish-readings.json').read_bytes())['materials']
    n=192;v,u=np.meshgrid(np.arange(n)/n,np.arange(n)/n,indexing='ij')
    for i,(key,name)in enumerate(STEMS.items()):
        rng=np.random.default_rng(740871+i)
        fleck=gaussian_filter(rng.normal(size=(n,n)),.48,mode='wrap')
        cloud=gaussian_filter(rng.normal(size=(n,n)),4.2,mode='wrap');cloud/=cloud.std()
        rgb=np.asarray(readings[key]['median_srgb'])+np.zeros((n,n,3))
        if name=='red-entrance-tile':
            ix=(u*3)%1;iy=(v*3)%1;edge=np.minimum(np.minimum(ix,1-ix)*.287,np.minimum(iy,1-iy)*.21)
            joint=np.clip((.0041-edge)/.0026,0,1)
            value=(9*fleck+3*cloud+np.repeat(np.repeat(rng.uniform(-7,7,(3,3)),n//3,axis=0),n//3,axis=1))
            rgb+=value[:,:,None]*[1,.72,.62];rgb=rgb*(1-joint[:,:,None])+[108,97,86]*joint[:,:,None]
            h=.0004*fleck-.0025*joint
        elif name=='canopy-metal':
            brush=gaussian_filter(fleck,(.55,3.8),mode='wrap');value=6*fleck+2.5*cloud+6*brush
            rgb+=value[:,:,None];h=.00020*fleck+.00025*brush
        else:
            grain=gaussian_filter((rng.random((n,n))>.90).astype(float),.57,mode='wrap')
            k=1 if name=='lime-render' else .57
            rgb+=(k*(12*fleck+3.0*cloud+15*(grain-grain.mean())))[:,:,None]
            h=k*(.00063*fleck+.00065*grain+.00015*cloud)
        size=REPEAT_METRES[key]
        dx=(np.roll(h,-1,1)-np.roll(h,1,1))/(2*size[0]/n);dy=(np.roll(h,-1,0)-np.roll(h,1,0))/(2*size[1]/n)
        normal=np.stack([-dx,dy,np.ones_like(dx)],axis=-1);normal/=np.linalg.norm(normal,axis=-1,keepdims=True)
        Image.fromarray(np.rint(np.clip(rgb,0,255)).astype('uint8')).save(HERE/(name+'.png'),optimize=True)
        Image.fromarray(np.rint((normal*.5+.5)*255).astype('uint8')).save(HERE/NORMAL_FILENAMES[key],optimize=True)
if __name__=='__main__':generate()
