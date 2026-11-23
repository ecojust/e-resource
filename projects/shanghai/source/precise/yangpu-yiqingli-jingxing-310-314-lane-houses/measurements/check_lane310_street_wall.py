"""Measure the historical grey street wall and its low plinth in front of the ochre annex."""
from pathlib import Path
import argparse,json,sys
import numpy as np
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'source/precise/xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
sys.path.insert(0,str(HERE.parent/'source'))
from glb_triangles import SerialScene
from build_model import placed_matrix
from lane310 import cut

def check(file):
    sc=SerialScene(file)
    W=placed_matrix(json.loads((HERE.parent/'source/house-placements.json').read_bytes())['house_310'])
    results=[]
    # Sample across the visible span and at three different heights. Test the
    # physical street-facing plane using rays normal to the registered wall.
    for v in [398,467,537]:
        expected='red mineral finish' if v>514 else 'patched basement render'
        front=.067 if v>514 else .09
        for u in [45,76,106,136,166,196,226,240]:
            on_plane=cut(u,v,front)
            origin=(W@[*list(on_plane-[0,2,0]),1])[:3]
            hit=sc.ray(origin,W[:3,:3]@[0,1,0],4)
            okay=bool(hit and expected in hit['material'] and abs(hit['distance_m']-2)<.012)
            results.append({'reference_px':[u,v],'expected_material':expected,'expected_distance_m':2,
                            'observed':hit,'pass':okay})
    return {'mesh':sc.asset,'original_photo':'registered-houses-and-photographs.json','samples':results,
            'matched':sum(row['pass'] for row in results),'count':len(results)}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mesh',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();r=check(a.mesh);a.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print(r['matched'],r['count'],[(i['reference_px'],i['observed']['material'] if i['observed'] else None) for i in r['samples'] if not i['pass']])
