"""Check the painted blue strokes, loops and centres between the eight 2017 characters."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import polylabel
from check_shop_signs import Builder,HERE,SerialScene
from shop_signs import PALETTE,PIER_BLUE,add_south_pier_words,panel_mapper


def export(path,low):
    b=Builder(PALETTE)
    add_south_pier_words(b,low)
    for part in b.parts:
        v=np.asarray(part['vertices'])
        f=np.asarray(part['triangles'])
        edges=Counter((i,j)for t in f for i,j in zip(t,np.roll(t,-1)))
        if any(n!=1 or edges[j,i]!=1 for (i,j),n in edges.items()):raise ValueError(part['label'])
        tri=(v-v.mean(axis=0))[f]
        if np.sum(tri[:,0]*np.cross(tri[:,1],tri[:,2]))<=0:raise ValueError(part['label'])
    b.save(path,{'name':'Two blue E-Ju Chenxin shop inscriptions, August–September 2017'})
    return {'parts':len(b.parts),'triangles':sum(len(p['triangles'])for p in b.parts),'closed_positive':True}


def check(file,low,whole):
    scene=SerialScene(file)
    panels=json.loads((HERE/'south-shop-pier-panels.json').read_bytes())['world_panels']
    words=json.loads((HERE/'2017-south-pier-words.json').read_bytes())['panels']
    rows=[]
    for col,items in words.items():
        point=panel_mapper(panels[col])
        tests=[]
        for n,item in enumerate(items):
            if n:
                v=(items[n-1]['normalized_bounds'][1]+item['normalized_bounds'][3])/2
                tests.append(('between',(0,v),False))
            for rings in item['low' if low else 'near']:
                p=Polygon(rings[0],rings[1:])
                for desc,shape,ink in [(item['letter'],p,True)]+[(item['letter']+' counter',Polygon(r.coords),False)for r in p.interiors]:
                    tests.append((desc,polylabel(shape,tolerance=.00013).coords[0],ink))
        for desc,(u,v),ink in tests:
            start=point(u,v,.07)
            direction=point(u,v,0)-start
            hit=scene.ray(start,direction/np.linalg.norm(direction),.20 if whole else .069)
            actual=hit['material'] if hit else None
            correct=actual==PIER_BLUE if ink else (bool(actual) and actual not in (PIER_BLUE,'Fangyou | painted blue edge') if whole else actual is None)
            rows.append(dict(column=col,letter=desc,uv=[round(u,6),round(v,6)],first=actual,blue_stroke=ink,passed=bool(correct)))
    return dict(model_sha256=hashlib.sha256(file.read_bytes()).hexdigest(),unfiltered=True,count=len(rows),
                passed=all(i['passed']for i in rows),hits=rows)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mesh',type=Path);p.add_argument('report',type=Path)
    p.add_argument('--low',action='store_true');p.add_argument('--whole',action='store_true');p.add_argument('--export',action='store_true')
    a=p.parse_args();info=export(a.mesh,a.low) if a.export else {}
    result={**info,**check(a.mesh,a.low,a.whole)}
    a.report.write_text(json.dumps(result,ensure_ascii=False,indent=1)+'\n')
    print(result['count'],[h for h in result['hits']if not h['passed']][:3])
    raise SystemExit(int(not result['passed']))
