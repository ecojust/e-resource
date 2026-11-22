"""Generate the original facing-brick tile used only on the arched storey (MIT)."""
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter
from PIL import Image


def make(path):
    rng = np.random.default_rng(596)
    height,width = 512,576
    y,x = np.mgrid[:height,:width]
    row = y//32
    unit = 32
    # In the visible long faces, short brick ends interrupt longer stretchers.
    # Vary the modules on alternate courses and keep the pattern tileable.
    xx = (x + (row%2)*unit) % width
    section = xx//(3*unit)
    phase = xx%(3*unit)
    header = phase>=2*unit
    index = section*2+header.astype(int)
    u = np.where(header,phase-2*unit,phase)
    cell_width = np.where(header,unit,2*unit)
    dy = np.minimum(y%32,31-y%32)
    dx = np.minimum(u,cell_width-1-u)
    distance = np.minimum(dy*.69,dx)
    levels = rng.normal(0,11,(16,12))
    warm = rng.normal(0,4,(16,12))[row,index]
    mottling = gaussian_filter(rng.normal(0,1,(height,width)),2.8,mode='wrap')*31
    grain = rng.normal(0,3.3,(height,width))+mottling
    tone = (levels[row,index]+grain)[:,:,None]
    face = np.array([123,110,106])[None,None,:]+tone+warm[:,:,None]*[1,.10,-.43]
    mortar = np.array([149,139,131])[None,None,:]+grain[:,:,None]*.53
    # Soft dusty joints still read at the full-city LOD.
    joint = np.clip((3.1-distance)/1.35,0,1)[:,:,None]
    out = np.clip(face*(1-joint)+mortar*joint,0,255).astype('uint8')
    Image.fromarray(out).save(path,optimize=True)


if __name__=='__main__':
    make(Path(__file__).with_name('daren-grey-brick.png'))
