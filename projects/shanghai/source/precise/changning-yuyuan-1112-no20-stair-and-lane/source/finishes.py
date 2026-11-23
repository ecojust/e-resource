"""Original periodic painted plaster, terrazzo, wood and grey plinth studies."""
from pathlib import Path
import importlib.util
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
HERE=Path(__file__).absolute().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
helper=PROJECT/'source/precise/xuhui-wanping-42-brick-window-bays/source/brick_finishes.py'
spec=importlib.util.spec_from_file_location('material_writer',helper);writer=importlib.util.module_from_spec(spec);spec.loader.exec_module(writer)
STEMS={'twenty | cream exterior plaster':'pale-render','twenty | grey granite terrazzo':'aggregate-step','twenty | dark stained timber':'handrail-wood','twenty | grey dressed coursing':'grey-plinth'}
NORMAL_FILENAMES={k:s+'-normal.png'for k,s in STEMS.items()}
REPEAT_METRES=dict(zip(STEMS,[(.54,.54),(.29,.29),(.61,.84),(.69,.54)]))
writer.HERE=HERE;writer.STEMS=STEMS;writer.NORMAL_FILENAMES=NORMAL_FILENAMES;writer.REPEAT_METRES=REPEAT_METRES
PALETTE={k:{'color':[1,1,1],'roughness':r,'texture':str(HERE/(s+'.png')),'normal':str(HERE/NORMAL_FILENAMES[k])} for (k,s),r in zip(STEMS.items(),[.93,.70,.58,.86])}
def metric_uv(p):p['texcoords']=(np.asarray(p['texcoords'])/(.78*np.asarray(REPEAT_METRES[p['material']]))).tolist()
def generate():
 N=128;v,u=np.mgrid[0:N,0:N]/N
 for idx,(key,stem)in enumerate(STEMS.items()):
  rng=np.random.default_rng(876042+idx);raw=rng.normal(size=(N,N));f=gaussian_filter(raw,.45,mode='wrap');m=gaussian_filter(raw,3.1,mode='wrap');m/=m.std()
  if idx==0:rgb=[198,194,171]+(3.8*f+1.65*m)[:,:,None]*np.array([1,.93,.78]);height=.00047*f+.00018*m
  elif idx==1:
   chips=gaussian_filter((rng.random((N,N))>.82).astype(float),.46,mode='wrap');chips-=chips.mean()
   rgb=[137,133,128]+(13.2*f+62*chips)[:,:,None]*np.array([1,.95,.89]);height=.00032*f+.00015*chips
  elif idx==2:
   grain=gaussian_filter(raw,(5.,.82),mode='wrap');grain/=grain.std()
   rgb=[89,67,53]+(4.6*grain+2.*m+1.3*f)[:,:,None]*np.array([1,.85,.69]);height=.00018*grain
  else:rgb=[139,139,126]+(4.*f+2.1*m)[:,:,None];height=.00038*f
  du=(np.roll(height,-1,1)-np.roll(height,1,1))/(2*REPEAT_METRES[key][0]/N);dv=(np.roll(height,-1,0)-np.roll(height,1,0))/(2*REPEAT_METRES[key][1]/N)
  nn=np.stack([-du,dv,np.ones_like(du)],axis=-1);nn/=np.linalg.norm(nn,axis=-1)[:,:,None]
  Image.fromarray(np.uint8(np.clip(np.rint(rgb),0,255))).save(HERE/(stem+'.png'),optimize=True)
  Image.fromarray(np.uint8(np.rint((nn*.5+.5)*255))).save(HERE/NORMAL_FILENAMES[key],optimize=True)
if __name__=='__main__':generate()
