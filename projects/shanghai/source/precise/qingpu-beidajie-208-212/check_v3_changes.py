#!/usr/bin/env python3
"""Scope proof for v3 sign and tile repairs; source parts are bound to actual GLBs."""
import argparse,collections,hashlib,importlib.util,json,math,struct,sys
from pathlib import Path
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
HERE=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def is_target(p):
 label=p['label'];return label.startswith('roof-tile-') or 'vertical-sign-' in label or 'observed-green-sign' in label

def load(root,name):
 spec=importlib.util.spec_from_file_location(name,root/'build_model.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 obj=m.TeaHouse();obj.structure();obj.gallery();obj.roof();obj.signs_lanterns();return obj

def counter(records,material):
 records=records.copy();records[records==0]=0 # Canonicalize equivalent IEEE signed zero.
 prefix=material.encode()+b'\0';return collections.Counter(hashlib.sha256(prefix+x.tobytes()).digest() for x in records)

def generated(parts):
 whole=collections.Counter();target=collections.Counter()
 for p in parts:
  xyz=np.asarray(p['vertices'],float)[:,[0,2,1]]*[1,1,-1];xyz=xyz.astype('<f4').astype(float)
  t=np.asarray(p['triangles']);tri=xyz[t];n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);n/=np.linalg.norm(n,axis=1)[:,None]
  rec=np.concatenate([tri,np.repeat(n[:,None,:],3,axis=1)],axis=2).astype('<f4');c=counter(rec,p['material']);whole.update(c)
  if is_target(p):target.update(c)
 return whole,target

def actual(path):
 b=path.read_bytes();n=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+n]);binary=b[28+n:]
 def ac(i):
  a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];width={'VEC3':3,'SCALAR':1}[a['type']]
  return np.frombuffer(binary,dtype={5126:'<f4',5125:'<u4'}[a['componentType']],count=a['count']*width,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,width)
 out=collections.Counter()
 for p in g['meshes'][0]['primitives']:
  t=ac(p['indices']).ravel().reshape(-1,3);v=ac(p['attributes']['POSITION']);n=ac(p['attributes']['NORMAL'])
  out.update(counter(np.concatenate([v[t],n[t]],axis=2),g['materials'][p['material']]['name']))
 return out

def local(obj,p):
 v=np.asarray(p['vertices'],dtype=np.float32).astype(float);return np.asarray([obj.coords(x) for x in v])

def lap_stats(obj):
 parts={p['label']:p for p in obj.b.parts if p['label'].startswith('roof-tile-')};lookup={}
 for name,p in parts.items():
  _,_,side,row,column=name.split('-');lookup[(int(side),int(row),int(column))]=local(obj,p)
 outer=[];inner=[];pair_count=0;near_coplanar=0;minimum_lap=1;maximum_lap=0
 def surface(v,d,inside=False):
  a=9 if inside else 0;b=27 if inside else 18
  # Same angle-index lies on the actual straight longitudinal mesh edge.
  t=(d-v[a:a+9,1])/(v[b:b+9,1]-v[a:a+9,1])
  return v[a:a+9,2]+t*(v[b:b+9,2]-v[a:a+9,2])
 for (side,row,col),a in lookup.items():
  key=(side,row+1,col)
  if key not in lookup:continue
  b=lookup[key];low=max(float(a[:9,1].mean()),float(b[:9,1].mean()));high=min(float(a[18:27,1].mean()),float(b[18:27,1].mean()))
  assert high>low+.0349
  pair_count+=1;minimum_lap=min(minimum_lap,high-low);maximum_lap=max(maximum_lap,high-low)
  upper,lower=(b,a) if side==0 else (a,b)
  values=[]
  for d in np.linspace(low,high,3):
   gap=surface(upper,d)-surface(lower,d);clear=surface(upper,d,True)-surface(lower,d)
   values.extend(gap.tolist());outer.extend(gap.tolist());inner.extend(clear.tolist())
  near_coplanar+=int(max(abs(x) for x in values)<.001)
 return {'adjacent_tile_pairs':pair_count,'sampled_outer_skin_points':len(outer),'lap_extent_m':[minimum_lap,maximum_lap],
   'signed_uphill_outer_skin_above_downhill_m':[min(outer),max(outer)],'upper_inner_skin_above_lower_outer_skin_m':[min(inner),max(inner)],
   'pairs_with_all_outer_samples_within_1mm':near_coplanar}

def main(a):
 old=load(a.baseline,'v2_reference_builder');new=load(HERE,'v3_candidate_builder')
 oldraw=a.baseline/'output/qingpu-beidajie-208-212-raw.glb';newraw=HERE/'output/qingpu-beidajie-208-212-raw.glb'
 oc,ot=generated(old.b.parts);nc,nt=generated(new.b.parts);assert oc==actual(oldraw);assert nc==actual(newraw)
 assert oc-ot==nc-nt,'Non-target POSITION/NORMAL/material triangles changed'
 old_lap=lap_stats(old);new_lap=lap_stats(new)
 assert old_lap['pairs_with_all_outer_samples_within_1mm']>0 # Actual near-coplanar cases; retain the complete measured distribution, including ridge-adjacent exceptions.
 assert .017<new_lap['signed_uphill_outer_skin_above_downhill_m'][0]<.020
 assert new_lap['signed_uphill_outer_skin_above_downhill_m'][1]<.020
 assert new_lap['upper_inner_skin_above_lower_outer_skin_m'][0]>.002
 assert new_lap['pairs_with_all_outer_samples_within_1mm']==0
 # All six sign glyphs lie ahead of every unchanged building/roof surface.
 sign=[p for p in new.b.parts if 'observed-green-sign' in p['label']]
 background=[local(new,p) for p in new.b.parts if not ('vertical-sign-' in p['label'] or 'observed-green-sign' in p['label'])]
 max_other_d=float(max(v[:,1].max() for v in background));min_sign_d=float(min(local(new,p)[:,1].min() for p in sign));assert min_sign_d-max_other_d>.20
 one=next(p for p in sign if p['label'].endswith('-一'));v=local(new,one);w=float(np.ptp(v[:,0]));h=float(np.ptp(v[:,2]))
 font=TTFont(HERE/'fonts/TeahouseSubset.otf');gs=font.getGlyphSet();glyph=gs[font.getBestCmap()[ord('一')]];pen=BoundsPen(gs);glyph.draw(pen);x0,y0,x1,y1=pen.bounds;ratio=(y1-y0)/(x1-x0)
 assert abs(h/w-ratio)<.0005,(w,h,ratio)
 assert sha(HERE/'photos/commons-33172025.jpg')==sha(a.baseline/'photos/commons-33172025.jpg')
 assert sha(HERE/'geometry-input.json')==sha(a.baseline/'geometry-input.json')
 assert sha(HERE/'fonts/TeahouseSubset.otf')==sha(a.baseline/'fonts/TeahouseSubset.otf')
 result={'schema':'teahouse-v3-targeted-repair-audit-v1','passed':True,'v2_raw_sha256':sha(oldraw),'v3_raw_sha256':sha(newraw),
  'actual_glb_matches_generated_position_normal_material_multiset':True,'ieee_signed_zero_canonicalized_for_comparison':True,'non_target_actual_triangles_preserved':sum((oc-ot).values()),
  'non_target_removed_or_changed_triangles':0,'target_scope':['main roof short tile shells only; backing/pitch/ridge-cap/gables/canopy unchanged','vertical sign board and six green glyphs; only一aspect changes; two new concealed mounts'],
  'v2_real_lap_evidence':old_lap,'v3_real_lap_evidence':new_lap,
  'sign_clearance':{'minimum_letter_back_d_m':min_sign_d,'maximum_other_building_d_m':max_other_d,'clearance_m':min_sign_d-max_other_d,'reason':'For viewing directions with positive outward-normal component, all letters are in front of every roof/rafter/background surface; no roof occlusion is geometrically possible.'},
  'one_glyph':{'source_bbox_units':list(pen.bounds),'natural_height_width_ratio':ratio,'actual_v3_width_m':w,'actual_v3_height_m':h,'actual_v3_ratio':h/w,'v2_wrong_vertical_stretch_factor':.43/(.43*ratio),'cause':'Per-single-glyph independent width/height normalization, not winding or triangulation failure','same_font_original_outline_not_rotated':True},
  'original_photo_geometry_input_font_bytes_unchanged':True,'root_v2_visual_findings':'Root and author actually viewed the native preview; 江 was occluded and一was vertically stretched; root accepted arches/gallery/side-gable closure only.',
  'v3_native_browser_visual_acceptance':False,'checker_sha256':sha(__file__)}
 out=HERE/'audit';out.mkdir(exist_ok=True);(out/'v2-v3-targeted-repair.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 # Scientific glyph-outline comparison from actual source geometry, not an edited photograph.
 import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
 from matplotlib.patches import Polygon as Patch
 fig,axes=plt.subplots(1,2,figsize=(8,4))
 for ax,obj,title in [(axes[0],old,'v2: one glyph forced to a square'),(axes[1],new,'v3: original glyph aspect restored')]:
  p=next(p for p in obj.b.parts if 'observed-green-sign' in p['label'] and p['label'].endswith('-一'));v=local(obj,p);center=(v[:,:3].max(0)+v[:,:3].min(0))/2
  for t in p['triangles']:
   q=v[list(t)]
   if np.ptp(q[:,1])<1e-5 and q[:,1].mean()>v[:,1].mean():ax.add_patch(Patch(q[:,[0,2]]-center[[0,2]],facecolor='#277c58',edgecolor='none'))
  ax.set_xlim(-.26,.26);ax.set_ylim(-.26,.26);ax.set_aspect('equal');ax.set_title(title,fontsize=10);ax.set_xlabel('metres');ax.grid(alpha=.2)
 fig.tight_layout();fig.savefig(out/'one-glyph-aspect-comparison.png',dpi=140);plt.close(fig)
 print(json.dumps({k:result[k] for k in ['passed','non_target_actual_triangles_preserved','v2_real_lap_evidence','v3_real_lap_evidence','sign_clearance','one_glyph']},ensure_ascii=False,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);main(p.parse_args())
