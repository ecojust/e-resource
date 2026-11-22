"""Verify source-pixel underside bands, fitted dimensions, and surfaces of the exported crest."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
# The triangle reader is distributed with this collection of reconstructed Shanghai buildings.
sys.path.append(str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact'))
from glb_triangles import SerialScene
from historic_roof_ornament import blade,shelves,mast_geometry,STONE,EDGE,METAL,SHOE
from rosholt_ornament_plane import DATA,pixel,PROJECTION

def source_checks(src):
    if hashlib.sha256(src.read_bytes()).hexdigest()!=DATA['photograph']['sha256']:
        raise ValueError('Expected the original 1020 by 706 Rosholt print')
    mono=np.asarray(Image.open(src).convert('L'),float)
    checks=[]
    for i,s in enumerate(DATA['shelves']):
        expected=s['lower_lip'][1]
        y=int(round(expected))
        # Sample the central half of the four dark undersides, away from both mast and sky.
        x0,x1=601,606
        line=mono[y-3:y+4,x0:x1].mean(axis=1)
        actual=int(y-3+np.argmin(line))
        dark=float(mono[actual,x0:x1].mean())
        light=float(mono[max(y-5,0),x0:x1].mean())
        checks.append(dict(lip=i+1,expected_pixel_row=expected,measured_darkest_row=actual,dark_grey_level=dark,light_grey_level=light,passed=abs(actual-expected)<2.1 and light-dark>30))
    return checks
def checks():
    for b in DATA['ribs']:
        l,r,y0,y1,z0,z1=blade(b)
        for f in (.2,.55,.82):
            yield b['name']+' exposed side',np.array([l,y0+f*(y1-y0),z0+.65*(z1-z0)]),[1,0,0],STONE
        yield b['name']+' top',np.array([(l+r)/2,(y0+y1)/2,z1]),[0,0,-1],STONE
    for i,(l,r,y0,y1,z0,z1) in enumerate(shelves()):
        for f in (.45,.7,.85):
            x=l+f*(r-l)
            yield f'shelf {i+1} underside',np.array([x,(y0+y1)/2,z0]),[0,0,1],EDGE
            yield f'shelf {i+1} upper face',np.array([x,(y0+y1)/2,z1]),[0,0,-1],EDGE
            yield f'shelf {i+1} front lip',np.array([x,y0,(z0+z1)/2]),[0,1,0],EDGE
    x,y,lo,hi,r=mast_geometry()
    for f in (.72,.81,.94):
        # Probe at a vertex of both the 10- and 24-side tube profiles.
        yield 'visible mast',np.array([x+r,y,lo+(hi-lo)*f]),[-1,0,0],METAL
def inspect(model,src):
    scene=SerialScene(model);points=[]
    for name,p,d,m in checks():
        d=np.asarray(d,dtype=float)
        hit=scene.ray(p-.016*d,d,.032)
        dist=None if hit is None else float(np.linalg.norm(np.array(hit['point_enu_m'])-p))
        points.append(dict(feature=name,xyz_m=p.round(6).tolist(),image_xy_px=np.round(pixel(p),2).tolist(),expected=m,actual=None if hit is None else hit['material'],error_m=dist,passed=bool(hit and hit['material']==m and dist<.0025)))
    photos=source_checks(src)
    return dict(**scene.asset,triangles=len(scene.tri),source_image_sha256=DATA['photograph']['sha256'],source_dark_bands=photos,local_projection=PROJECTION.tolist(),measured_lip_pitch_m=[float(shelves()[i][4]-shelves()[i+1][4]) for i in range(3)],storey_assumption_m=DATA['period']['assumed_storey_m'],passed=all(v['passed'] for v in points+photos),contacts=points)
if __name__=='__main__':
    cli=argparse.ArgumentParser()
    for n in ('model','historic_image','output'):cli.add_argument(n,type=Path)
    args=cli.parse_args();result=inspect(args.model,args.historic_image)
    args.output.write_text(json.dumps(result,indent=1)+'\n')
    print(sum(v['passed'] for v in result['contacts']),len(result['contacts']),[(v['measured_darkest_row'],v['passed']) for v in result['source_dark_bands']])
    raise SystemExit(0 if result['passed'] else 1)
