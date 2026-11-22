"""Measure the front and return of the two eastern window arches from the 2017 photograph."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import map_coordinates, gaussian_filter1d
from scipy.signal import find_peaks

# Points on the photographed outer rim and front edge of the intrados.
# The trace frame is a uniformly scaled crop of the upright original.
TIERS = {
 'lower': {
  'crop':[2450,1120,4390,1870], 'view_width':970,
  'outer':[(186,249),(226,219),(275,190),(325,165),(375,144),(427,124),(477,109),(542,96),(596,91),(646,89),(697,91),(747,96),(798,106),(848,117),(900,130)],
  'inner':[(225,284),(262,259),(305,233),(352,210),(397,188),(443,173),(484,164),(537,154),(583,150),(628,149),(676,150),(718,156),(763,164),(804,175),(843,190)],
  'back_ends':[(240,303),(846,212)], 'key':[(478,92),(542,84),(537,156),(484,165)],
  'key_return':[(492,190),(546,181)], 'rim':.16},
 'upper': {
  'crop':[2540,15,4375,795], 'view_width':910,
  'outer':[(206,256),(244,230),(283,204),(322,182),(363,161),(402,145),(442,129),(492,115),(534,105),(573,99),(612,95),(650,92),(688,93),(727,96),(763,102)],
  'inner':[(242,278),(277,255),(309,235),(344,215),(380,196),(414,180),(446,166),(489,151),(525,146),(557,141),(591,137),(622,134),(653,134),(684,137),(714,142)],
  'back_ends':[(255,297),(708,166)], 'key':[(441,118),(492,105),(489,151),(446,166)],
  'key_return':[(454,197),(497,181)], 'rim':.155}
}
def controls(row):
    return [PchipInterpolator(np.arange(len(row)),np.asarray(row)[:,i])for i in (0,1)]
def evaluate(spline,t):
    return np.stack([c(t)for c in spline],axis=-1)
def pull(rgb,x,y):
    return np.stack([map_coordinates(rgb[:,:,i],[y,x],order=1,mode='nearest') for i in range(3)],axis=-1)
def registration(data):
    scale=(data['crop'][2]-data['crop'][0])/data['view_width']
    return np.asarray(data['crop'][:2]),scale
def strip(rgb,data):
    origin,scale=registration(data)
    t=np.linspace(0,14,2801); levels=np.linspace(-.15,1.42,158)
    a=evaluate(controls(data['outer']),t);b=evaluate(controls(data['inner']),t)
    samples=origin+(a[None,:,:]+levels[:,None,None]*(b-a)[None,:,:])*scale
    return t,levels,pull(rgb,samples[:,:,0],samples[:,:,1])
def preview(destination,t,levels,colors):
    bright=Image.fromarray(colors.clip(0,255).astype(np.uint8))
    bright=bright.resize((1120,158),Image.Resampling.LANCZOS)
    d=ImageDraw.Draw(bright)
    for value in range(15):
        x=round(value*80);d.line((x,0,x,8),fill='yellow');d.text((x+1,0),str(value),fill='yellow')
    bright.save(destination,quality=93)
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('photo',type=Path);ap.add_argument('out',type=Path);a=ap.parse_args()
    with Image.open(a.photo) as img:
        for name,data in TIERS.items():
            # Only the arch's rectangle is needed for sampling.
            original_photo=img.crop(data['crop'])
            reduced={**data,'crop':[0,0,original_photo.width,original_photo.height]}
            t,levels,colors=strip(np.asarray(original_photo,dtype=float),reduced)
            preview(a.out/(name+'-unwrapped.jpg'),t,levels,colors)
