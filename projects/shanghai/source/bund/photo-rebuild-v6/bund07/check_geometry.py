#!/usr/bin/env python3
"""Local part topology/numeric validation; no rendering or geometric truth claim."""
from pathlib import Path
from collections import Counter
import json,hashlib
import numpy as np
from build_model import build
HERE=Path(__file__).resolve().parent
B,raw=build(HERE/'output');issues=[];counts={'parts':len(B.parts),'closed_parts':0,'positive_volume_parts':0,'finite_float32_parts':0,'edge_incidence_failures':0,'winding_failures':0};minimum=None
for part in B.parts:
 xyz=np.asarray(part['vertices'],dtype=np.float32).astype(np.float64);tri=np.asarray(part['triangles'],dtype=int)
 edges=Counter();balance=Counter()
 for face in tri:
  for a,b in zip(face,np.roll(face,-1)):
   edge=tuple(sorted((int(a),int(b))));edges[edge]+=1;balance[edge]+=1 if a<b else -1
 closed=all(n==2 for n in edges.values());wound=all(n==0 for n in balance.values());counts['closed_parts']+=int(closed);counts['edge_incidence_failures']+=int(not closed);counts['winding_failures']+=int(not wound)
 center=xyz.mean(0);a,b,c=(xyz[tri[:,i]]-center for i in range(3));vol=np.einsum('ij,ij->i',a,np.cross(b,c)).sum()/6;counts['positive_volume_parts']+=int(vol>0);counts['finite_float32_parts']+=int(np.isfinite(xyz).all());minimum=vol if minimum is None else min(minimum,vol)
 if not closed or not wound or not vol>0:issues.append({'label':part['label'],'closed':closed,'consistent_winding':wound,'signed_volume_float32_m3':float(vol),'nonmanifold_edges':[{'vertices':list(edge),'count':count,'coordinates':[xyz[edge[0]].tolist(),xyz[edge[1]].tolist()]} for edge,count in edges.items() if count!=2][:12]})
report={'schema':'bund07-actual-parts-structural-audit-v1','passed':not issues,'raw_sha256':raw['sha256'],'raw_bytes':raw['bytes'],'raw_triangles':raw['triangles'],'counts':counts,'minimum_signed_component_volume_m3':float(minimum),'issues':issues,'helper_sha256':hashlib.sha256((HERE.parent/'common/photo_architecture.py').read_bytes()).hexdigest(),'limitations':['Closed positive part volumes do not prove zero overlaps between intentional trim/wall assemblies.','Photographic shape, camera calibration and true source dimensions require separate visual review.','This checker does not render, push or edit the main project.']}
(HERE/'output/structural-check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(0 if report['passed'] else 1)
