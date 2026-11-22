"""Check every editable tablet part for a closed, consistently oriented solid."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = next(p for p in HERE.parents if (p / 'tools/package_architectural_model.py').is_file())
sys.path.insert(0, str(PROJECT / 'source/precise/hongkou-general-post-office/source/common'))
sys.path.insert(0, str(HERE.parent/'source'))
from photo_architecture import Builder
from gable_dedications import add_gable_dedications, PALETTE


def part_topology(part):
    xyz = np.asarray(part['vertices'], dtype=float)
    faces = np.asarray(part['triangles'], dtype=int)
    coordinates, remap = np.unique(np.round(xyz, 9), axis=0, return_inverse=True)
    compact = remap[faces]
    triangles = coordinates[compact]
    # Subtract a nearby origin to make millimetre-scale solids stable.
    a, b, c = np.moveaxis(triangles - coordinates.mean(axis=0), 1, 0)
    area = np.cross(b-a, c-a)
    volume = float(np.einsum('ij,ij->', a, np.cross(b, c))/6)
    edges = Counter()
    directed = Counter()
    for i, j, k in compact.tolist():
        for u, v in ((i,j),(j,k),(k,i)):
            edges[(min(u,v),max(u,v))] += 1
            directed[(u,v)] += 1
    boundary = sum(n != 2 for n in edges.values())
    reversed_mismatch = sum(directed[(u,v)] != directed[(v,u)] for (u,v) in edges)
    degenerate = int((np.linalg.norm(area,axis=1) < 1.e-11).sum())
    return {'component':part['label'],'material':part['material'],'triangles':len(faces),
            'undirected_edges':len(edges),'edges_without_two_incidents':boundary,
            'orientation_mismatches':reversed_mismatch,'degenerate_triangles':degenerate,
            'signed_volume_m3':volume,'passed':volume>1.e-11 and boundary==0 and reversed_mismatch==0 and degenerate==0}


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('output',type=Path)
    cli.add_argument('--lod',action='store_true')
    args=cli.parse_args()
    builder=Builder(PALETTE)
    add_gable_dedications(builder,args.lod)
    rows=[part_topology(p) for p in builder.parts]
    result={'lod':args.lod,'model_source_sha256':hashlib.sha256((HERE.parent/'source/gable_dedications.py').read_bytes()).hexdigest(),
            'parts':rows,'passed':all(r['passed'] for r in rows)}
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(args.lod,len(rows),sum(r['triangles'] for r in rows),result['passed'],
          [(r['component'],r['edges_without_two_incidents'],r['orientation_mismatches'],r['signed_volume_m3']) for r in rows if not r['passed']])
    raise SystemExit(0 if result['passed'] else 1)
