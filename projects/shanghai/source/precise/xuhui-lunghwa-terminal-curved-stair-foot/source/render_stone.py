"""Render the actual decoded model, sampling the same embedded stone image as in the viewer."""
from pathlib import Path
from PIL import Image
import numpy as np
from paint_uv import read_uv,render as shade
def render(path,scene,palette,name,out):
    direction=[-.44,.82,-.43]if name=='oblique'else[0.,1.,-.43]
    names=np.asarray(scene.materials)[scene.mi]
    shade(path,scene.tri,names,{k:np.asarray(v['color']) for k,v in palette.items()},read_uv(path),direction,[0.,.80,.86],5.95 if name=='oblique'else 5.98,out)
