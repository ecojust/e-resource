"""Export and check each individually editable gable solid."""
import argparse,hashlib,json,sys
from collections import Counter
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[1]/'hongkou-general-post-office/source/common')]
from gable_relief import PALETTE,add_gable_relief
from photo_architecture import Builder

def export(directory,lod=False):
    b=Builder(PALETTE);add_gable_relief(b,lod)
    for part in b.parts:
        verts=np.array(part['vertices']);tris=np.array(part['triangles'])
        edges=Counter((int(i),int(j))for face in tris for i,j in zip(face,np.roll(face,-1)))
        if any(n!=1 or edges[j,i]!=1 for (i,j),n in edges.items()):
            raise ValueError('Non-manifold or reversed edge in '+part['label'])
        verts-=verts.mean(axis=0);t=verts[tris]
        if (t[:,0]*np.cross(t[:,1],t[:,2])).sum()<=0:
            raise ValueError('Nonpositive volume in '+part['label'])
    mode='lod' if lod else 'full'
    out=directory/f'ornament-{mode}.glb';b.save(out,{'name':'Guiren Li street gable relief and name tablet','photos_embedded':False})
    return {'level':mode,'parts':len(b.parts),'triangles':sum(len(p['triangles'])for p in b.parts),
            'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'nonmanifold_or_nonpositive':[]}
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);args=ap.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    for coarse in [False,True]:
        row=export(args.output,coarse)
        (args.output/f"component-{row['level']}.json").write_text(json.dumps(row,indent=2)+'\n')
