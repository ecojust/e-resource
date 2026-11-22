"""Check each raised 2017 inscription and preserved counter in both decoded meshes."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
import sys
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import polylabel

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[1]/'hongkou-general-post-office/source/common'),
              str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
from photo_architecture import Builder
from glb_triangles import SerialScene
from shop_signs import PALETTE, FINISH, INSCRIPTIONS, panel_mapper, add_shop_signs

def export(path,low):
    b=Builder(PALETTE)
    add_shop_signs(b,low)
    for part in b.parts:
        v=np.asarray(part['vertices']); f=np.asarray(part['triangles'])
        dirs=Counter((i,j)for t in f for i,j in zip(t,np.roll(t,-1)))
        shared=[(i,j)for (i,j),n in dirs.items()if n!=1 or dirs[j,i]!=1]
        if shared:raise ValueError((part['label'],'unpaired',len(shared)))
        tri=(v-v.mean(axis=0))[f]
        if np.sum(tri[:,0]*np.cross(tri[:,1],tri[:,2]))<=0:raise ValueError((part['label'],'volume'))
    b.save(path,{'name':'Four shopfront inscriptions photographed beside Rongkang Villas in 2017'})
    return {'parts':len(b.parts),'triangles':sum(len(g['triangles'])for g in b.parts),'all_closed_positive':True}

def check(path,low,whole=False):
    scene=SerialScene(path);rows=[]
    corners=json.loads((HERE/'shop-panel-geometry.json').read_bytes())['world_panels']
    for key,letters in INSCRIPTIONS.items():
        point=panel_mapper(corners[key])
        for letter in letters:
            parts=[Polygon(g[0],g[1:])for g in letter['low' if low else 'near']]
            # Select a point well inside each visible blob in the dimensionless board, including dots.
            for i,poly in enumerate(parts):
                uv=polylabel(poly,tolerance=.00014)
                controls=[(uv,FINISH[letter['surface']][0],'stroke')]
                for hole in poly.interiors:
                    void=Polygon(hole);mid=polylabel(void,tolerance=.00014)
                    board_finish={'south':'Rongkang | red fascia','north_left':'Rongkang | charcoal sign board','north_middle':'Rongkang | grey sign board','north_right':'Rongkang | limestone sign board'}
                    controls.append((mid,board_finish[key] if whole else None,'counter'))
                for sample,required,kind in controls:
                    u,v=sample.coords[0]
                    o=point(u,v,.080);ray=point(u,v,0)-o
                    ray=ray/np.linalg.norm(ray)
                    hit=scene.ray(o,ray,.14 if whole else .0794)
                    actual=hit['material'] if hit else None
                    rows.append(dict(board=key,sign=letter['lettering'],piece=i+1,where=[round(u,5),round(v,5)],
                                     kind=kind,expected=required,first=actual,passed=actual==required))
    return dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),mesh=path.name,checks=len(rows),
                passed=all(r['passed'] for r in rows),failures=[r for r in rows if not r['passed']],rays=rows)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mesh',type=Path);parser.add_argument('output',type=Path)
    parser.add_argument('--whole',action='store_true');parser.add_argument('--low',action='store_true');parser.add_argument('--export',action='store_true')
    args=parser.parse_args();info=export(args.mesh,args.low) if args.export else None
    report=check(args.mesh,args.low,args.whole)
    if info:report.update(info)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=1)+'\n')
    print(report['checks'],len(report['failures']),report['failures'][:1])
    raise SystemExit(0 if report['passed'] else 1)
