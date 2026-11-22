"""Export a removable gable ornament and verify each editable component."""
import argparse,hashlib,json,sys
from pathlib import Path
from collections import Counter
import numpy as np
from shapely.geometry import Polygon
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[1]/'hongkou-general-post-office/source/common')]
from acanthus_relief import PALETTE,add_acanthus_relief
from photo_architecture import Builder

def export(directory,lod,row):
    b=Builder(PALETTE);add_acanthus_relief(b,lod,row)
    check=[]
    for p in b.parts:
        v=np.asarray(p['vertices'],dtype=float);t=np.asarray(p['triangles'],dtype=int)
        directed=Counter((int(a),int(c)) for f in t for a,c in zip(f,np.roll(f,-1)))
        edges=all(count==1 and directed[c,a]==1 for (a,c),count in directed.items())
        tv=(v-v.mean(axis=0))[t];volume=np.einsum('ij,ij->i',tv[:,0],np.cross(tv[:,1],tv[:,2])).sum()/6
        area=np.linalg.norm(np.cross(tv[:,1]-tv[:,0],tv[:,2]-tv[:,0]),axis=1).min()/2
        outline_ok=None
        if p['label']!='Gable leaf | relief bed' and 'volute button' not in p['label']:
            profiles=v[:-2].reshape(-1,7 if lod else 10,3)
            outline=Polygon(np.vstack([profiles[:,0][:,[0,2]],profiles[::-1,-2][:,[0,2]]]))
            outline_ok=bool(outline.is_valid and outline.area>0)
            if not outline_ok:raise ValueError('Folded ribbon edge in '+p['label'])
        check.append(dict(label=p['label'],faces=len(t),simple_projected_carving_edge=outline_ok,
                        positive_volume_m3=round(float(volume),11),
                        smallest_triangle_m2=float(area),closed_with_consistent_winding=bool(edges)))
        if min(volume,area)<=0 or not edges:raise ValueError('Open or degenerate part '+p['label'])
    out=directory/('acanthus-'+('lod' if lod else 'full')+'.glb')
    b.save(out,{'name':'Acanthus panel below the blank gable screen','editable_components':len(check)})
    return dict(file=out.name,sha256=hashlib.sha256(out.read_bytes()).hexdigest(),parts=len(check),
                triangles=sum(p['faces'] for p in check),measurements=row,members=check)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path);parser.add_argument('row',type=Path)
    args=parser.parse_args();args.directory.mkdir(parents=True,exist_ok=True)
    row=json.loads(args.row.read_bytes())
    reports=[export(args.directory,lod,row)for lod in (False,True)]
    (args.directory/'editable-acanthus-solids.json').write_text(json.dumps(reports,indent=2)+'\n')
