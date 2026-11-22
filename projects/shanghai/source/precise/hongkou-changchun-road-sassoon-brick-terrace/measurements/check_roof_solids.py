"""Check the indexed edges and signed volume of every editable dormer component."""
from collections import Counter
from hashlib import sha256
from pathlib import Path
import json
import sys

import numpy as np

here = Path(__file__).resolve().parent
sys.path.insert(0, str(here.parent / 'source'))
sys.path.insert(0, str(here.parents[1] / 'hongkou-general-post-office/source/common'))
from photo_architecture import Builder
from sassoon_roof_windows import PALETTE, add_roof_windows

def measure(lod):
    builder = Builder(PALETTE)
    add_roof_windows(builder, lod)
    totals = {}
    for part in builder.parts:
        v = np.asarray(part['vertices'])
        t = np.asarray(part['triangles'], dtype=int)
        edges = Counter()
        for i,j,k in t:
            edges.update([tuple(sorted((i,j))),tuple(sorted((j,k))),tuple(sorted((k,i)))])
        a,b,c = (v[t[:,i]] - v[0] for i in range(3))
        volume = np.einsum('ij,ij->i', a, np.cross(b,c)).sum()/6
        if any(count!=2 for count in edges.values()) or volume<=1e-12:
            raise ValueError((part['label'],volume))
        entry = totals.setdefault(part['material'],{'parts':0,'triangles':0,'volume_m3':0.})
        entry['parts'] += 1
        entry['triangles'] += len(t)
        entry['volume_m3'] += float(volume)
    return {'closed_positive_components':len(builder.parts),'triangles':sum(q['triangles']for q in totals.values()),'materials':totals}
if __name__ == '__main__':
    result = {'component_source_sha256':sha256((here.parent/'source/sassoon_roof_windows.py').read_bytes()).hexdigest(),
              'full':measure(False),'lod':measure(True)}
    Path(sys.argv[1]).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
