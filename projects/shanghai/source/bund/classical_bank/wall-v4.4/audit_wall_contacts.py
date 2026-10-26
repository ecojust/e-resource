"""Read-only raw GLB opposite-side contacts in captured structural depth groups."""
from pathlib import Path
import argparse,importlib.util,json,hashlib,collections,numpy as np
from shapely.geometry import Polygon
from shapely.strtree import STRtree
ap=argparse.ArgumentParser();ap.add_argument('--project',type=Path,required=True);ap.add_argument('--raw',type=Path,required=True);ap.add_argument('--capture',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args();D=json.loads(args.capture.read_text());spec=importlib.util.spec_from_file_location('glb',args.project/'tools/build_bund_lods.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);j,b=m.read_glb(args.raw);ts=[]
def visit(i,parent):
 node=j['nodes'][i];M=parent@m.node_matrix(node)
 if 'mesh' in node:
  for p in j['meshes'][node['mesh']]['primitives']:
   if j['materials'][p['material']]['name']!='Warm granite wall':continue
   v=m.accessor_values(j,b,p['attributes']['POSITION']);v=v@M[:3,:3].T+M[:3,3];ix=m.accessor_values(j,b,p['indices']).reshape(-1,3);ts.extend(v[ix])
 for c in node.get('children',[]):visit(c,M)
for i in j['scenes'][j.get('scene',0)]['nodes']:visit(i,np.eye(4))
T=np.array(ts);E=T[:,:,[0,2]]*np.array([1,-1]);B=np.stack([D['world_basis_u'],D['world_basis_v']],axis=1);A=E@B;Z=T[:,:,1];norm=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]);length=np.linalg.norm(norm,axis=1);source_groups=collections.defaultdict(list)
for s in D['shells']:source_groups[(*[round(x,9) for x in s['u']],*[round(x,9) for x in s['v']],round(s['front_plane_offset'],8),round(s['depth'],8))].append(s)
rows=[]
for key,shells in sorted(source_groups.items()):
 s=shells[0];u=np.array(s['u']);v=np.array(s['v']);off=s['front_plane_offset'];depth=s['depth'];XZ=np.array([p for q in shells for ring in q['front_polygons'] for p in ring]);lo=XZ.min(0);hi=XZ.max(0);X=A@u;Y=A@v-off;world_t=np.array(D['world_basis_u'])*u[0]+np.array(D['world_basis_v'])*u[1];direction=(norm@np.array([world_t[0],0,-world_t[1]]))/np.maximum(length,1e-30);mask=(abs(direction)>.99999)&(length>1e-7)&(X.min(1)>=lo[0]-1e-4)&(X.max(1)<=hi[0]+1e-4)&(Z.min(1)>=lo[1]-1e-4)&(Z.max(1)<=hi[1]+1e-4)&(Y.min(1)>=-1e-4)&(Y.max(1)<=depth+1e-4);planes=collections.defaultdict(list)
 for i in np.where(mask)[0]:planes[round(float(X[i].mean()),4)].append((Polygon(np.column_stack([Y[i],Z[i]])),int(np.sign(direction[i])),i,float(X[i].mean())))
 count=0;area=0;maxoff=0
 for fs in planes.values():
  shapes=[f[0] for f in fs];tree=STRtree(shapes)
  for i,p in enumerate(shapes):
   for jj in tree.query(p):
    k=int(jj)
    if k<=i or fs[i][1]==fs[k][1]:continue
    a=p.intersection(shapes[k]).area
    if a>1e-5:count+=1;area+=a;maxoff=max(maxoff,abs(fs[i][3]-fs[k][3]))
 rows.append({'u':u.tolist(),'v':v.tolist(),'front_plane_offset':off,'depth_m':depth,'opposing_contact_pairs':count,'summed_pair_overlap_m2':area,'maximum_contact_plane_offset_m':maxoff,'side_triangles_checked':int(mask.sum())})
report={'schema_version':'captured-wall-depth-contact-audit-v1','asset':args.raw.name,'asset_sha256':hashlib.sha256(args.raw.read_bytes()).hexdigest(),'scope':'Opposing side faces within each captured structural front/depth/height/along-facade envelope; actual raw GLB node transforms applied. True window-height jambs are retained; only opposing overlap is counted.','group_count':len(rows),'opposing_contact_pairs':sum(r['opposing_contact_pairs'] for r in rows),'summed_group_pair_overlap_m2':sum(r['summed_pair_overlap_m2'] for r in rows),'plane_bucket_m':.0001,'minimum_overlap_area_m2':1e-5,'groups':rows,'browser_visual_confirmation_not_part_of_this_script':True};args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='groups'},indent=2))
