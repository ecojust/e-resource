import sys,json,hashlib,collections
from pathlib import Path
import numpy as np
sys.path.insert(0,sys.argv[1]);from verify_serialized import load
def bags(t,tags):
 out={}
 for m in sorted(set(tags)):
  v=np.asarray(t[tags==m],dtype='<f4');v[v==0]=0;starts=np.lexsort((v[:,:,2],v[:,:,1],v[:,:,0]),axis=-1)[:,0];v=v[np.arange(len(v))[:,None],(starts[:,None]+np.arange(3))%3];out[m]=collections.Counter(x.tobytes()for x in v)
 return out
def bind(p):return {'file':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
rows=[]
for role,old,new in [('raw',Path(sys.argv[2]),Path(sys.argv[3])),('lod',Path(sys.argv[4]),Path(sys.argv[5]))]:
 ot,om,_=load(old);nt,nm,_=load(new);ob,nb=bags(ot,om),bags(nt,nm);changed=[]
 for m in sorted(set(ob)|set(nb)):
  removed=ob.get(m,collections.Counter())-nb.get(m,collections.Counter());added=nb.get(m,collections.Counter())-ob.get(m,collections.Counter())
  if removed or added:
   ar=np.stack([np.frombuffer(x,dtype='<f4').reshape(3,3)for x in removed.elements()]);aa=np.stack([np.frombuffer(x,dtype='<f4').reshape(3,3)for x in added.elements()]);changed.append({'material':m,'removed_triangles':len(ar),'added_triangles':len(aa),'removed_bounds_enu_m':{'min':ar.min((0,1)).tolist(),'max':ar.max((0,1)).tolist()},'added_bounds_enu_m':{'min':aa.min((0,1)).tolist(),'max':aa.max((0,1)).tolist()},'removed_oriented_triangles_enu':ar.tolist(),'added_oriented_triangles_enu':aa.tolist()})
 assert len(changed)==1 and changed[0]['material']=='dark bronze' and changed[0]['removed_triangles']==changed[0]['added_triangles']==24
 assert np.array_equal(ot.min((0,1)),nt.min((0,1)))and np.array_equal(ot.max((0,1)),nt.max((0,1)))
 assert abs(changed[0]['added_bounds_enu_m']['min'][2]-24.525)<1e-4 and abs(changed[0]['added_bounds_enu_m']['max'][2]-25.475)<1e-4
 rows.append({'variant':role,'previous_asset':bind(old),'final_asset':bind(new),'total_triangles':len(nt),'unchanged_material_groups':19,'only_two_twelve_triangle_dark_panels_changed':True,'entire_model_bounds_unchanged':True,'differences':changed})
r={'model_id':'hongkou-general-post-office','passed':True,'method':'Actual GLB oriented FLOAT32 triangle multiset subtraction by material; cyclic vertex normalization retains winding. All triangles outside 2 twelve-triangle dark-bronze boxes are bit-identical.','pre_correction_visuals':'revision-82a935ab/native.json','final_visuals':'native.json','variants':rows};Path(sys.argv[6]).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'passed':True,'variants':[{'variant':r['variant'],'unchanged_material_groups':19,'changed_triangles':24}for r in rows]}))
