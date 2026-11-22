"""Read the yellow 家政 and arrow paint from the EXIF-oriented, credited 2015 courtyard photograph."""
import argparse,json
from hashlib import sha256
from pathlib import Path
import contourpy
import numpy as np
from PIL import Image, ImageOps
from shapely.geometry import Polygon

SOURCE='c704d8f7e2e8900bc362c6ce4d0d0b268c2921b28ba1553d4c562d9ffa49f873'
def extract(photo):
    assert sha256(photo.read_bytes()).hexdigest()==SOURCE
    image=ImageOps.exif_transpose(Image.open(photo)).convert('RGB')
    assert image.size==(2988,5312)
    box=(888,3265,1122,3409)
    colors=np.asarray(image.crop(box),dtype=float)
    r,g,b=colors.transpose(2,0,1)
    mask=(r>78)&(g>68)&(r-b>41)&(g-b>37)&(r>g*.94)
    x=np.arange(box[0],box[2]);y=np.arange(box[1],box[3])
    generator=contourpy.contour_generator(x=x,y=y,z=mask.astype(float),fill_type='OuterOffset')
    points,offsets=generator.filled(.5,1.5)
    groups=[]
    for pts,ends in zip(points,offsets):
        rings=[pts[i:j]for i,j in zip(ends[:-1],ends[1:])]
        poly=Polygon(rings[0],rings[1:]).simplify(.62)
        if not poly.is_valid:poly=poly.buffer(0)
        if poly.area<25:continue
        a,c=poly.centroid.coords[0]
        label='arrow' if c>3372 else ('家' if a<1003 else '政')
        if label=='arrow' and c<3378:continue
        groups.append(dict(mark=label,area_px2=round(poly.area,2),shell=list(poly.exterior.coords),
                           holes=[list(r.coords)for r in poly.interiors if Polygon(r).area>7]))
    return dict(source='Antigng, File:郑家弄.jpg, 2015-09-09, CC BY-SA 4.0',source_sha256=SOURCE,
                source_url='https://commons.wikimedia.org/wiki/File:%E9%83%91%E5%AE%B6%E5%BC%84.jpg',
                reference_size=[2988,5312],corner_order='top left, top right, bottom right, bottom left',
                green_board=[[878,3261],[1131,3256],[1134,3406],[878,3414]],fasteners=[[887.1,3268.1],[1123.5,3266.1],[1123.9,3397.7],[886.2,3404.0],[1007.9,3401.0]],
                pigment=groups,method='Threshold the yellow paint within the full-resolution sign, follow exterior and interior isolines, simplify by 0.62 source pixels.')
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('photograph',type=Path);parser.add_argument('output',type=Path);a=parser.parse_args()
    a.output.write_text(json.dumps(extract(a.photograph),ensure_ascii=False,indent=2)+'\n')
