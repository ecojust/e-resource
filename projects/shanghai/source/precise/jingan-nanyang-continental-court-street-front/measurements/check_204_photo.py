"""Cast through independent features digitised on the photograph of the 204 entrance."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
from glb_triangles import SerialScene
from street_shops_and_roof import SHADOW, STONE, GARLAND, BAND, SOFFIT, GREEN, PLAQUE

# The working detail is the original box [430,1800,1650,2720] sampled at half scale.
# Keep all selected pixels, including those on thin edges whose relief is difficult to read.
MARKS=[
    ('leftmost pointed blind niche',SHADOW,[(104,130),(115,111),(124,146),(99,150)]),
    ('second pointed blind niche',SHADOW,[(159,129),(169,107),(180,144),(163,149)]),
    ('shallow central tablet',SHADOW,[(214,106),(247,124),(288,109),(325,111),(342,130)]),
    ('third pointed blind niche',SHADOW,[(375,128),(382,107),(393,136),(369,138)]),
    ('fourth pointed blind niche',SHADOW,[(427,126),(433,107),(446,140),(422,139)]),
    ('ligaments between niches',STONE,[(143,134),(198,128),(355,123),(408,124)]),
    ('lower arched lip',GARLAND,[(115,177),(157,166),(216,151),(282,146),(352,149),(415,159),(448,170)]),
    ('soffit seen from the street',SOFFIT,[(148,206),(208,194),(266,182),(330,185),(393,191),(442,204)]),
    ('enamel street number',GREEN,[(521,249),(537,251)]),
    ('bilingual heritage plaque',PLAQUE,[(514,293),(541,303),(529,317)])]

def check(path):
    proj=np.array(json.loads((HERE/'street-and-204-projections.json').read_text())['204-hi11']['P'])
    scene=SerialScene(path);eye=-np.linalg.solve(proj[:,:3],proj[:,3]);rows=[]
    for detail,mat,points in MARKS:
        for x,y in points:
            u,v=430+2*x,1800+2*y
            ray=np.linalg.solve(proj[:,:3],[u,v,1.])
            hit=scene.ray(eye,ray,90)
            actual=hit['material'] if hit else None
            rows.append(dict(detail=detail,source_pixel=[u,v],expected=mat,actual=actual,matched=mat==actual,hit=hit))
    return dict(source='高亦寒，陕西北路204号门洞，2000×3008原像',camera='204-hi11',model_sha256=hashlib.file_digest(path.open('rb'),'sha256').hexdigest(),matched=sum(x['matched'] for x in rows),count=len(rows),observations=rows)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('model',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args()
    answer=check(args.model)
    args.output.write_text(json.dumps(answer,ensure_ascii=False,indent=1)+'\n')
    print(answer['matched'],answer['count'])
