"""Trace the seven dark letters in the December 2015 photograph of the left porch pier."""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image
import numpy as np
from scipy.ndimage import gaussian_filter
from shapely.geometry import box
from shapely.ops import unary_union
CHARACTERS=[('上',194,244),('海',247,298),('市',300,351),('质',353,405),('量',407,455),('协',459,509),('会',512,561)]
def extract(photo):
    intensity=np.array(Image.open(photo).convert('L'),dtype=float)
    assert intensity.shape==(640,330)
    shapes=[]
    for character,top,bottom in CHARACTERS:
        roi=intensity[top:bottom,157:217]
        bg=np.percentile(roi,89,axis=1,keepdims=True)
        contrast=gaussian_filter(bg-roi,.67)
        threshold=dict(上=10.5,海=8.5,市=11.4,质=12.0,量=14,协=13,会=12)[character]
        pieces=[]
        for j,row in enumerate(contrast>threshold):
            edges=np.flatnonzero(np.diff(np.r_[False,row,False]))
            pieces.extend(box(157+a,top+j,157+b,top+j+1)for a,b in edges.reshape(-1,2))
        glyph=unary_union(pieces)
        rings=[]
        for part in getattr(glyph,'geoms',[glyph]):
            if part.area<19:continue
            outline=part.simplify(.66,preserve_topology=True)
            rings.append([[[round(x,3),round(y,3)]for x,y in list(r.coords)[:-1]]for r in [outline.exterior,*outline.interiors]])
        shapes.append(dict(character=character,band=[157,top,217,bottom],contrast_threshold=round(threshold,3),rings=rings))
    return dict(photo_sha256=hashlib.sha256(photo.read_bytes()).hexdigest(),image=[330,640],board_edges_at_top=[[146,181],[223,181]],board_edges_at_base=[[150,577],[231,578]],glyphs=shapes)
if __name__=='__main__':
    c=argparse.ArgumentParser(description=__doc__);c.add_argument('photo',type=Path);c.add_argument('output',type=Path);a=c.parse_args();r=extract(a.photo);a.output.write_text(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n');print([(d['character'],len(d['rings']))for d in r['glyphs']])
