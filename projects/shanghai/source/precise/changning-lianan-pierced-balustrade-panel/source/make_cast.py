"""Generate the fine lime grains of the grey-cream cast screen material."""
from pathlib import Path
import numpy as np
from PIL import Image
rng=np.random.default_rng(461);h,w=270,320;base=rng.normal(0,3.3,(h,w))
for _ in range(1150):
 y=int(rng.integers(0,h));x=int(rng.integers(0,w));base[y,x]-=rng.uniform(4,29)
c=np.array([186,178,160],dtype=float)+base[:,:,None];Image.fromarray(np.uint8(np.clip(c,0,255))).save(Path(__file__).with_name('cast-lime.png'),optimize=True)
