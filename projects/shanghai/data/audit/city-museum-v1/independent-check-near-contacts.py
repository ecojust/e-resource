"""Bound all actual near triangles by geometrically possible original owners.
Near owner attributes do not exist; ambiguous faces remain explicitly ambiguous.
Usage: review-directory city-triangle-directory clip-candidate.json output.json
"""
from pathlib import Path
import hashlib,json,sys
import numpy as np
import shapely
from shapely.geometry import shape,mapping,Polygon
from shapely.ops import unary_union
R,D,C,O=map(Path,sys.argv[1:5]);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
orig=json.loads((R/'independent-original-city-projection.json').read_text());dec=json.loads((D/'city-source-decode.json').read_text());row=next(r for r in dec['variants']if r['variant']=='near1860');b=(D/row['output']['file']).read_bytes();assert hashlib.sha256(b).hexdigest()==row['output']['sha256'];ts=np.frombuffer(b,dtype='<f8').reshape(-1,3,3);shapes=shapely.convex_hull(shapely.polygons(ts[:,:,:2]));heights=ts[:,:,2].max(1);c=json.loads(C.read_text());mask=unary_union([shape(c[k+'_mask_geometry_local_enu'])for k in ['main','site']]);matches=[];owners=[]
for r in orig['near_roof_projections']:
 owners.append(r['owner']);g=shape(r['geometry_local_xy']).buffer(.005,join_style=2);matches.append(shapely.covers(g,shapes)&(heights<=r['source_height_estimate_m']+.005))
matches=np.asarray(matches);counts=matches.sum(0);assert np.all(counts>0);assert len(ts)==122780
def cut(v,h,above):
 out=[]
 for a,b in zip(v,v[1:]+v[:1]):
  aa=a[2]>=h if above else a[2]<=h;bb=b[2]>=h if above else b[2]<=h
  if aa:out.append(a)
  if aa!=bb:out.append(a+(b-a)*((h-a[2])/(b[2]-a[2])))
 return out
records=[]
for owner in [510,1262]:
 selected=matches[owners.index(owner)];g=shapely.union_all(shapes[selected]);overlap=g.intersection(mask);assert overlap.area<1e-7 and overlap.length<1e-7
 low=[]
 for t in ts[selected&(ts[:,:,2].min(1)<=2)]:
  v=cut(list(t),0,True)
  if v:v=cut(v,2,False)
  if len(v)>=3:
   p=Polygon([a[:2]for a in v])
   if p.area>1e-10:low.append(p)
 low=unary_union(low);records.append({'owner':owner,'compatible_triangle_count':int(selected.sum()),'compatible_but_ambiguous_triangles':int((selected&(counts>1)).sum()),'possible_projection_area_m2':g.area,'possible_projection_mask_overlap_m2':overlap.area,'possible_low_area_m2':low.area,'possible_low_geometry_local_xy':mapping(low),'possible_full_geometry_local_xy':mapping(g)})
out={'schema':'city-museum-independent-possible-near-contacts-v1','passed':True,'method':'Every independently decoded actual triangle, including all instances, is tested for full projected convex containment in each actual source roof+0.005m and source maximum elevation. All possible owners are retained rather than selecting a guessed face owner. All triangles have at least one compatible source. Every triangle compatible with510/1262 is excluded from effective display clipping. Its exact z0..2 polygon clip forms a conservative possible-contact envelope.','bindings':{'independent_source_decode_sha256':sha(D/'city-source-decode.json'),'actual_near_triangle_payload_sha256':row['output']['sha256'],'original_city_review_sha256':sha(R/'independent-original-city-projection.json'),'clip_candidate_sha256':sha(C),'script_sha256':sha(Path(__file__))},'actual_triangles':len(ts),'unmatched_triangles':0,'ambiguous_triangle_count':int((counts>1).sum()),'records':records,'limits':'Compatible does not mean positively identified foreign ownership. Contact areas with final new geometry are upper bounds and must be reported, not silently relabeled as only high eaves.'}
O.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'passed':True,'triangles':len(ts),'ambiguous':out['ambiguous_triangle_count'],'links':[{'id':r['owner'],'possible_triangles':r['compatible_triangle_count'],'low_area':r['possible_low_area_m2']}for r in records]}))
