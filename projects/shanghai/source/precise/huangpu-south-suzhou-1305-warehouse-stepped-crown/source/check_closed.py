"""Verify the direction and pairing of every edge in reconstructed source components."""
from collections import Counter
import numpy as np
def check_closed(builder):
    report=[]
    for part in builder.parts:
        coordinates=np.asarray(part['vertices'])
        faces=coordinates[np.asarray(part['triangles'])]
        edge=Counter()
        for tri in faces:
            v=[tuple(np.round(point,8)) for point in tri]
            edge.update(zip(v,v[1:]+v[:1]))
        bad=sum(1 for (a,b),count in edge.items() if count!=1 or edge[(b,a)]!=1)
        volume=float(np.einsum('ij,ij->i',faces[:,0],np.cross(faces[:,1],faces[:,2])).sum()/6)
        report.append({'component':part['label'],'triangle_count':len(faces),'unpaired_or_duplicated_directed_edges':bad,'signed_volume_m3':volume})
    return report
