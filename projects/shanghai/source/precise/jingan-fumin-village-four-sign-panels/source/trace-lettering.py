"""Trace the four visible claret sign faces in Antigng's photograph of Fumin Xincun."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage
from shapely.geometry import box, mapping, MultiPolygon, Polygon
from shapely.ops import unary_union

# Coordinates refer to the 880 by 215 detail described below, in photo order.
BOXES = [('邨',(153,55,231,133)),('新',(321,60,410,137)),
         ('民',(508,67,585,144)),('富',(671,72,743,150))]
def glyph(image,bounds):
    left,top,right,bottom=bounds
    crop=image.crop(bounds)
    pixels=np.asarray(crop,dtype=float)
    red,green,blue=pixels.transpose(2,0,1)
    mask=(green<83)&(red-green>6)&(blue-green>1)
    if bounds==BOXES[0][1]:
        # The thin service cable through the left edge is independent of the letter.
        mask[:15,:9]=False
        mask[35:,:7]=False
    mask=ndimage.binary_closing(mask,structure=np.ones((2,2)))
    components,count=ndimage.label(mask)
    clean=np.isin(components,np.flatnonzero(np.bincount(components.ravel())[1:]>10)+1)
    runs=[]
    for row,scan in enumerate(clean):
        edges=np.flatnonzero(np.diff(np.r_[False,scan,False].astype(int))).reshape(-1,2)
        for a,b in edges:
            runs.append(box(left+a,215-top-row-1,left+b,215-top-row))
    outline=unary_union(runs).buffer(.58,join_style=1).buffer(-.52,join_style=1).simplify(.38,preserve_topology=True)
    assert not outline.is_empty and outline.is_valid
    if bounds==BOXES[3][1]:
        # The relief shadows almost fill the four counters in 田 and the narrow
        # counter in 口. Their visible returns are picked on the full-resolution crop.
        counters = [
            [(138,200),(176,203),(274,208),(293,214),(290,220),(231,217),(150,209)],
            [(150,277),(179,277),(206,285),(207,294),(176,291),(149,285)],
            [(248,278),(300,272),(301,286),(249,293)],
            [(161,322),(210,325),(209,339),(171,336)],
            [(251,326),(300,318),(299,333),(253,337)],
        ]
        for counter in counters:
            coordinates=[((3777+u*159/428-2570)*880/1600,215-(2136+v*157/424-2010)*215/390) for u,v in counter]
            outline=outline.difference(Polygon(coordinates))
    return mapping(outline)

if __name__=='__main__':
    opts=argparse.ArgumentParser(description=__doc__)
    opts.add_argument('photo',type=Path);opts.add_argument('output',type=Path);args=opts.parse_args()
    assert sha256(args.photo.read_bytes()).hexdigest()=='defed3ff9735856549d84801b3cad035e101776a8e2c160e3a711d942ba3daa0'
    image=Image.open(args.photo).convert('RGB').crop((2570,2010,4170,2400)).resize((880,215),Image.Resampling.LANCZOS)
    data={'author':'Antigng','source':'https://commons.wikimedia.org/wiki/File:富民新邨.jpg','license':'CC BY-SA 4.0','license_url':'https://creativecommons.org/licenses/by-sa/4.0/','detail_crop_original_pixels':[2570,2010,4170,2400],'detail_size':[880,215],'geometry_axes':'local picture pixels, y grows upwards from bottom','glyphs':[]}
    for name,bounds in BOXES:
        data['glyphs'].append({'character':name,'source_roi':bounds,'geometry':glyph(image,bounds)})
    args.output.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
