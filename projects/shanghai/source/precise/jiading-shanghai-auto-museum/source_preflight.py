#!/usr/bin/env python3
"""Bounded source/math checks only: never generate or accept the full museum."""
from pathlib import Path
import ast,argparse,hashlib,json,math,sys,re
import numpy as np
import shapely
from shapely.geometry import Polygon,LineString,shape,box
from shapely.ops import transform,unary_union
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from build_model import Museum,PALETTE
from common.photo_architecture import Builder
from solids import path_data,subpath,profile_sweep,surface_solid,panel,audit_parts

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
 if args.output.exists():raise ValueError('Do not overwrite source check evidence')
 m=Museum();q,t,n=path_data(m.spine_path)
 strip=Polygon([*q,*list((q-5*n)[::-1])]);assert strip.is_valid
 radii=[]
 for i in range(1,len(q)-1):
  a,b,c=q[i-1:i+2];u=b-a;v=c-b;w=c-a;cross=abs(u[0]*v[1]-u[1]*v[0])
  radii.append(float(np.linalg.norm(u)*np.linalg.norm(v)*np.linalg.norm(w)/max(2*cross,1e-12)))
 assert min(radii)>5.0,'Northern5mwrapper must not fold through its inner offset'
 assert len(m.e['lower_glass_storey_bottoms_m'])+len(m.e['upper_storey_glass_insets_m'])==m.c['official_constraints']['total_floors']==5
 assert len(set(m.e['lower_glass_storey_insets_m']))==3
 assert m.roof_z(0,-5)==m.e['upper_lower_deck_top_m']
 b=Builder(PALETTE);outer=LineString(m.c_outer_profile());inner=outer.offset_curve(-.94,join_style=1);core_outer=outer.offset_curve(-.05,join_style=1)
 core=Polygon([*core_outer.coords,*list(inner.coords)[::-1]])
 profile_sweep(b,subpath(m.spine_line,1,2,.25),list(core.exterior.coords),'Museum silver honeycomb aluminium','fixture/one-metre-C-wrapper')
 glass=outer.offset_curve(-.16,join_style=1).buffer(.0325,cap_style=2,join_style=1)
 profile_sweep(b,subpath(m.spine_line,3,4,.25),list(glass.exterior.coords),'Museum blue green glass','fixture/one-metre-C-glass')
 panel(b,[[-1,0],[0,.1],[1,0]],lambda x,y:0,lambda x,y:1,'Museum pale glass','fixture/tilted-curtain',outward1=.16)
 surface_solid(b,Polygon([[0,0],[3,0],[3,3],[0,3]],[[[1,1],[1,2],[2,2],[2,1]]]),lambda x,y:1+.1*x*x,lambda x,y:.6+.1*x*x,'Museum interior concrete','fixture/surface-with-real-hole',grid=.6)
 glyphs=json.loads((HERE/'references'/'museum-sign-outlines.json').read_text())['glyphs']
 for i,(ch,size) in enumerate([('博',.56),('A',.22)]):
  b.prism(shape(glyphs[ch]['outline']),0,.035,lambda x,z,d,size=size,i=i:(30+x*size,20-d+i,2+z*size),'Museum white sign relief',f'fixture/letter-{i}')
 fixture=audit_parts(b.parts);assert fixture['passed'],fixture['failures']
 # Approximate plan envelope, explicitly not an exported-triangle collision test.
 centre=np.asarray(m.e['external_stair_estimate_enu']);along=np.array([-.6,-.8]);out=np.array([.8,-.6])
 stair=Polygon([centre+along*u+out*v for u,v in [(-4.05,-2.05),(4.05,-2.05),(4.05,2.05),(-4.05,2.05)]])
 proposed=unary_union([m.base.buffer(2.75),m.upper,stair,box(-34.5,-10,-30,5)])
 anchor=m.g['anchor'];r=6378137.;scale=math.cos(math.radians(anchor[1]));mx=r*math.radians(anchor[0]);my=r*math.log(math.tan(math.pi/4+math.radians(anchor[1])/2))
 def project(x,y):return ((r*math.radians(x)-mx)*scale,(r*math.log(math.tan(math.pi/4+math.radians(y)/2))-my)*scale)
 neighbors=[]
 for old in m.g['current_city_detail']['same_near_neighbors_to_retain']:
  p=transform(project,shape(old['geometry']));a=proposed.intersection(p).area
  neighbors.append({'local_id':old['local_id'],'overlap_estimate_m2':a,'separation_estimate_m':proposed.distance(p),'source_preserved':True})
  assert a==0,'Estimated envelope crosses a retained neighbor'
 checked=[]
 for name in ['build_model.py','curves.py','solids.py','source_preflight.py','prepare_sign_outlines.py','prepare_audit_questions.py','render_previews.py','run_root.py','freeze_author_source.py','prepare_repairs_from_v1.py','check_local_repairs.py','design/plot_design.py','common/photo_architecture.py']:
  p=HERE/name;ast.parse(p.read_text());checked.append({'file':name,'sha256':sha(p)})
 photos=json.loads((HERE/'references'/'photo-register.json').read_text())['photos']
 for p in photos:
  file=HERE/'references'/Path(p['file']).name
  assert file.is_file() and sha(file)==p['sha256']
 glassnames=[s for s in PALETTE if 'glass' in s.lower()]
 assert all(re.search('glass|glaz',s,re.I) and not re.search('clock|opal|lamp|frame|mullion|muntin|division|grille|gate|bronze|stone',s,re.I) for s in glassnames)
 report={'schema':'auto-museum-source-preflight-v11','passed_in_source_math_scope':True,
  'full_model_generated':False,'actual_raw_structure_passed':False,'model_accepted':False,
  'calibration_sha256':sha(HERE/'calibration.json'),'source_geometry_sha256':sha(HERE/'geometry-input.json'),
  'source_files_syntax_checked':checked,'runtime_versions':{'python':sys.version.split()[0],'numpy':np.__version__,'shapely':shapely.__version__},
  'curved_plan_inputs_valid':True,'northern_C_offset_strip_valid':True,'minimum_sampled_northern_plan_radius_m':min(radii),
  'lower_roof_upper_deck_shared_nominal_level_m':m.roof_z(0,-5),
  'five_source_supported_storeys':True,'three_lower_storey_setbacks_m':m.e['lower_glass_storey_insets_m'],
  'small_fixture_actual_FLOAT32_parts':fixture['parts'],'small_fixture_triangles':fixture['triangles'],'small_fixture_closed_oriented_positive_volume':fixture['passed'],
  'retained_neighbors_estimated_envelope_only':neighbors,'estimated_plan_bounds_m':list(proposed.bounds),
  'real_glazing_names_match_current_MAIN_rule':glassnames,
  'limitations':['This is bounded source/math evidence, not an actual exported museum audit.','Estimated envelope does not prove whole-assembly or neighborhood collision freedom.','Native threeview inspection, actual decoded semantic geometry, source-owner matching and browser checks remain required.']}
 args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:v for k,v in report.items() if k not in ['source_files_syntax_checked','limitations']},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
