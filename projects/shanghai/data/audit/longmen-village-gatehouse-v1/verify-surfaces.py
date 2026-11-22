"""Independently check three real decoded sets of triangles after the placement review."""
import argparse,json,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
SOURCE=PROJECT/'source/precise/huangpu-longmen-village-gatehouse/source'
sys.path.insert(0,str(SOURCE))
from check_surfaces import check_triangles
from hashlib import sha256
cli=argparse.ArgumentParser(description=__doc__)
cli.add_argument('--work',required=True,type=Path)
cli.add_argument('--out',required=True,type=Path)
args=cli.parse_args()
out={}
for row in json.loads((args.work/'delivered-decode.json').read_bytes()):
    v=np.fromfile(row['triangle_file'],np.float64).reshape(-1,3,3)[:,:,[0,2,1]]*[1,-1,1]
    names=np.array(row['material_names'])[np.fromfile(row['triangle_material_ids_file'],np.uint16)]
    assert len(v)==len(names)==row['triangles']
    out[row['variant']]={'sha256':row['sha256'],**check_triangles(v,names,row['variant']=='lod')}
assert set(out)=={'raw','web','lod'}
args.out.parent.mkdir(exist_ok=True,parents=True)
args.out.write_text(json.dumps({'passed':True,'checker_sha256':sha256((SOURCE/'check_surfaces.py').read_bytes()).hexdigest(),
                              'role_checks':out},ensure_ascii=False,indent=2)+'\n')
print([(k,v['triangles'],len(v['rays']))for k,v in out.items()])
