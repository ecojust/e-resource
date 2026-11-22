"""Return the first visible material at the indicated points in the 640-pixel historical print."""
from pathlib import Path
import argparse,hashlib,json,sys
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
from read_study import decode,hit,norm
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('mesh',type=Path);parser.add_argument('output',type=Path)
args=parser.parse_args()
P=np.array(json.loads((HERE/'historic-balcony-period-camera.json').read_bytes())['P'])
eye=-np.linalg.solve(P[:,:3],P[:,3])
triangles,materials,_=decode(args.mesh)
regions=[('west-dark',[(35,122),(48,132),(32,154),(51,166)]),('west-stone',[(24,118),(58,151),(51,187)]),('centre-left',[(110,139),(125,142),(138,153),(144,163),(106,168)]),('centre-east-dark',[(220,146),(227,162),(218,173)]),('centre-east-bright',[(239,149),(248,158),(245,184)]),('splay-dark',[(325,147),(331,166),(327,188)]),('splay-bright',[(347,155),(349,163),(350,190)]),('splay-sill',[(337,209),(332,218),(342,217)]),('east-front-panel',[(442,195),(450,198),(459,205)]),('east-front-upper',[(442,162),(455,169),(460,157)]),('wall',[(179,140),(193,166),(383,152),(403,177)]),('crown',[(125,47),(138,55),(244,52)])]
regions_material={
 'west-dark':['glass in shade'],'west-stone':['pale window surround'],'centre-left':['silvery reflected light'],
 'centre-east-dark':['glass in shade'],'centre-east-bright':['silvery reflected light'],'splay-dark':['glass in shade'],
 'splay-bright':['silvery reflected light'],'splay-sill':['projecting stone edge','pale window surround'],
 'east-front-panel':['light timber panel'],'east-front-upper':['silvery reflected light'],'wall':['dark mineral facing'],
 'crown':['dark mineral facing']}
rows=[]
for group,points in regions:
    for pixel in points:
        direction=norm(np.linalg.solve(P[:,:3],np.r_[pixel,1.]))
        first=hit(triangles,materials,eye,direction)
        material=first[0] if first else None
        matches=material is not None and material.split(' | ')[-1] in regions_material[group]
        rows.append(dict(region=group,pixel=pixel,first_material=material,first_position_m=first[1] if first else None,
                         expected=regions_material[group],matches_photographic_region=matches))
record=dict(model_sha256=hashlib.sha256(args.mesh.read_bytes()).hexdigest(),count=len(rows),
            matched=sum(row['matches_photographic_region'] for row in rows),rows=rows)
args.output.write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n')
