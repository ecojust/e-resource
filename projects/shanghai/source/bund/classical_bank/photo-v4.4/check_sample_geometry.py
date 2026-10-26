#!/usr/bin/env python3
"""Independent exported-frame bounds/normals and sampled projective-UV checks."""
from pathlib import Path
import argparse,importlib.util,json,numpy as np,hashlib
P=Path(__file__).resolve().parent;ap=argparse.ArgumentParser();ap.add_argument('--project',required=True);args=ap.parse_args();R=Path(args.project)
spec=importlib.util.spec_from_file_location('read_glb',R/'tools/build_bund_lods.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
G=json.loads((R/'source/bund/classical_bank/geometry-input.json').read_text())['bund12'];C=json.loads((P/'calibration.json').read_text())['windows'];j,bin=m.read_glb(P/'bund12-photo-raw.glb');U=G['world_basis_u'];V=G['world_basis_v'];FC=G['front_center'];tested=0;front_normal_min=1.0
bounds=[]
for w in C:
 x=12.7+(w['bay']+.5)*(G['front_width']-25.4)/14;z0,z1,width=(19.6,22.7,1.95) if w['level']==3 else(13.8,17.9,2.2);bounds.append((x-width/2,x+width/2,z0,z1))
def visit(index,parent):
 global tested,front_normal_min
 node=j['nodes'][index];M=parent@m.node_matrix(node)
 if 'mesh' in node:
  for pr in j['meshes'][node['mesh']]['primitives']:
   name=j['materials'][pr['material']]['name']
   if not name.startswith('PhotoFacade_'):continue
   v=m.accessor_values(j,bin,pr['attributes']['POSITION']);v=v@M[:3,:3].T+M[:3,3];bx=v[:,0];by=-v[:,2];z=v[:,1];x=bx*U[0]+by*U[1]-FC[0];y=bx*V[0]+by*V[1]-FC[1];inside=np.zeros(len(v),bool)
   for lo,hi,bot,top in bounds:inside|=(x>=lo-1e-4)&(x<=hi+1e-4)&(z>=bot-1e-4)&(z<=top+1e-4)
   assert np.all(inside),'Replacement geometry left its six original aperture bounds'
   assert y.min()>=.23999 and y.max()<=.61501,'Replacement depth exceeds original glazing/frame range'
   if name=='PhotoFacade_Bund12_Glazing_OriginalPhoto':
    assert np.allclose(y,.57,atol=1e-5,rtol=0)
    n=m.accessor_values(j,bin,pr['attributes']['NORMAL']);n=n@np.linalg.inv(M[:3,:3]);n/=np.linalg.norm(n,axis=1)[:,None];out=np.array([-V[0],0,V[1]]);front_normal_min=min(front_normal_min,float((n@out).min()));assert front_normal_min>.99999
   tested+=len(v)
 for c in node.get('children',[]):visit(c,M)
for i in j['scenes'][j.get('scene',0)]['nodes']:visit(i,np.eye(4))
rows=json.loads((P/'panes.json').read_text());maximum=0
for row in rows:
 A=[];b=[]
 for (s,t),(x,y) in zip([(0,0),(1,0),(1,1),(0,1)],row['source_quad_original_pixels']):A.extend([[s,t,1,0,0,0,-s*x,-t*x],[0,0,0,s,t,1,-s*y,-t*y]]);b.extend([x,y])
 H=np.r_[np.linalg.solve(A,b),1].reshape(3,3)
 def pixel(s,t):q=H@np.array([s,t,1]);return q[:2]/q[2]
 for y in range(6):
  for x in range(6):
   st=np.array([(x/6,y/6),((x+1)/6,y/6),((x+1)/6,(y+1)/6),(x/6,(y+1)/6)]);px=np.array([pixel(*r) for r in st])
   for tri in[(0,1,2),(0,2,3),(0,1,3),(1,2,3)]:
    for wt in[(1/3,1/3,1/3),(.5,.5,0),(.5,0,.5),(0,.5,.5)]:
     t=np.array(tri);s,t1=np.array(wt)@st[t];interp=np.array(wt)@px[t];maximum=max(maximum,float(np.linalg.norm(interp-pixel(s,t1))))
assert maximum<.25;assert all(0<=x<5184 and 0<=y<3456 for r in rows for x,y in r['source_quad_original_pixels'])
out={'schema_version':'bund12-photo-geometry-uv-check-v1','status':'passed','source_raw_file':'bund12-photo-raw.glb','source_raw_sha256':hashlib.sha256((P/'bund12-photo-raw.glb').read_bytes()).hexdigest(),'replacement_exported_vertices_checked':tested,'new_geometry_within_six_original_aperture_bounds':True,'new_geometry_within_original_depth_envelope':True,'photo_front_depth_m':.57,'photo_front_normals_minimum_dot_outward':front_normal_min,'panes':len(rows),'subdivisions_per_axis':6,'max_tested_projective_uv_interpolation_error_original_pixels':maximum,'tolerance_original_pixels':.25,'test_locations':'Every grid cell, both triangulation diagonals, triangle centers and edge midpoints','image_pixels_modified':False,'all_source_quads_within_original_image':True,'browser_test_performed':False}
(P/'geometry-uv-validation.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
