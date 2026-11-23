"""Check the compiled lamp connection, door throat and transverse vestibule arcade.

Usage: python check_room_clearances.py source.glb output.json
"""
from pathlib import Path
import hashlib,json,sys
import numpy as np
from shapely.geometry import LineString,box
from shapely.ops import unary_union
here=Path(__file__).resolve().parent
from fit_oblique import read_triangles
from fit_vestibule import plane_point,REAR,HALF
p=Path(sys.argv[1]);destination=Path(sys.argv[2])
m=np.array(json.loads((here/'vestibule-station.json').read_bytes())['projection'])
tri,ids,names,sha=read_triangles(p)
scale=np.array([1600/950,1067/634]);height=8.30
def world(u,v,axis,value):
 return plane_point(m,*(np.array([u,v])*scale),axis,value)
mount=world(507,54,2,height)
def hits(eye,ray):
 e1=tri[:,1]-tri[:,0];e2=tri[:,2]-tri[:,0];h=np.cross(ray,e2);det=np.einsum('ij,ij->i',e1,h)
 usable=np.abs(det)>1e-7;inv=np.zeros_like(det);inv[usable]=1/det[usable]
 v=eye-tri[:,0];u=inv*np.einsum('ij,ij->i',v,h);q=np.cross(v,e1);w=inv*(q@ray);distance=inv*np.einsum('ij,ij->i',e2,q)
 good=np.flatnonzero(usable&(u>=-1e-7)&(w>=-1e-7)&(u+w<=1+1e-7)&(distance>1e-4))
 ordered=good[np.argsort(distance[good])]
 return [(round(float(distance[i]),4),names[ids[i]][1]) for i in ordered[:8]]
def cross_intervals(z):
 # Horizontal section of actual triangles across the complete rear door throat.
 subset=tri[(tri[:,:,2].min(axis=1)<z)&(tri[:,:,2].max(axis=1)>z)&(tri[:,:,1].min(axis=1)<REAR+1.5)&(tri[:,:,1].max(axis=1)>REAR-.12)]
 intervals=[]
 for face in subset:
  cut=[]
  for a,b in zip(face,np.roll(face,-1,axis=0)):
   if (a[2]<z)!=(b[2]<z):cut.append((a+(b-a)*(z-a[2])/(b[2]-a[2]))[:2])
  if len(cut)!=2:continue
  seg=LineString(cut).intersection(box(-HALF,REAR-.12,HALF,REAR+1.5))
  if not seg.is_empty:intervals.append((seg.bounds[0],seg.bounds[2]))
 return intervals
door=[]
for a,c in [(422,498),(508,606),(616,680)]:
 aa=world(a,530,1,REAR)[0];cc=world(c,530,1,REAR)[0]
 door.append([aa,cc])
def spans(z):
 cuts=cross_intervals(z);rows=[]
 for lo,hi in door:
  gaps=[];last=lo
  for a,b in sorted(cuts):
   if b<lo or a>hi:continue
   a=max(lo,a);b=min(hi,b)
   if a-last>.002:gaps.append([float(last),float(a),float(a-last)])
   last=max(last,b)
  if hi-last>.002:gaps.append([float(last),float(hi),float(hi-last)])
  rows.append(gaps)
 return rows
side=[]
for u in [(170+264)/2,216]:
 xyz=world(u,405,0,-HALF);y=xyz[1]
 side.append(dict(y=y,z=1.15,west=hits(np.array([0,y,1.15]),np.array([-1,0,0.])),east=hits(np.array([0,y,1.15]),np.array([1,0,0.]))))
near_mount=(np.linalg.norm(tri[:,:,:2]-mount[:2],axis=2).max(axis=1)<.14)&(tri[:,:,2].max(axis=1)>8.25)
metal=np.array([names[k][1]=='bronze-black joinery' for k in ids])
top=float(tri[near_mount&metal,:,2].max())
plaster=next(distance for distance,role in hits(mount+[0.,0.,.002],np.array([0.,0.,1.])) if role=='warm ivory plaster')
ceiling=height+.002+plaster
photo=[]
for left,right,row in [(558,592,502),(559,594,550),(561,595,575)]:
    a=world(left,row,1,REAR+.305);b=world(right,row,1,REAR+.305)
    photo.append(dict(left_source_px=(np.array([left,row])*scale).tolist(),right_source_px=(np.array([right,row])*scale).tolist(),
                      aperture_on_estimated_hinge_plane_m=float(b[0]-a[0]),mean_height_m=float((a[2]+b[2])/2)))
actual={str(z):spans(z) for z in [.25,1.,1.9]}
walk=[max((span[2] for span in paths),default=0.) for paths in actual['1.0']]
assert top>=ceiling and top-ceiling<.018,'Lamp suspension lacks a continuous connection or embeds deeply into the coffer.'
assert all(.45<max(q[2] for q in offsets[1])<.68 for offsets in actual.values())
assert max(walk[0],walk[2])<.025
assert all(all(distance>HALF+1.5 for distance,mat in r['east']+r['west']) for r in side)
dct=dict(mesh_sha256=sha,source_photo='https://commons.wikimedia.org/wiki/File:Shanghai_No._3_Girls%27_High_School,_Five-Four_lecture_building_entrance.jpg',
 authority='https://www.shcn.gov.cn/col6991/20221017/1223835.html',source_photo_size=[1600,1067],
 source_lamp='Ctny’s 2017 vestibule photograph shows a dark ceiling rose contacting the plaster inside a coffer. One central suspension descends to the tented brackets of a polygonal, amber-coloured lantern, with a smaller pendant below. The exact number of facets around the hidden back is unresolved.',
 coordinates='Z up. Widths are conditional on the photo registration and its 4.65 m rear-portal scale. For each horizontal section, project all real triangle segments between rear y−0.12 and y+1.50 m onto x. The complement inside each cased opening is a continuous straight path; sub-centimetre seams are retained in the raw slices.',
 rear_wall_y=REAR,door_frame_x_ranges_m=door,door_frame_widths_m=[b-a for a,b in door],
 actual_clear_x_slices_m=actual,largest_clear_width_left_centre_right_m=walk,
 measured_central_aperture_photo=photo,
 model_minus_photo_aperture_m=[walk[1]-r['aperture_on_estimated_hinge_plane_m'] for r in photo],
 closed_outer_doors='The photo shows three entrance doorways. The outer two are shut, and only the centre right leaf stands open. Apparent photographed widths were back-projected to the estimated hinge plane; the edges of an angled panel can lie ahead of or behind this plane.',
 previous_mesh=dict(sha256='9a7030147ad74036d00ccefcc1bfedd340d559d882bde348bbf71e28c0bbd742',centre_straight_clear_width_m=.8268977105617523,ceiling_mount_gap_m=.071),
 ceiling_connection=dict(rose_center_xyz=mount.tolist(),solid_metal_top_z_m=top,plaster_underside_z_m=ceiling,overlap_m=top-ceiling),
 side_openings=side,arcade_evidence='At a test height of 1.15 m, independent west/east casts through the hall pass both walls of the vestibule. The first blocking geometry is at the far teaching-wing return. The 2022 district account confirms east and west corridors, with classrooms along both sides. Only the western arch profile can be traced sufficiently in the 2017 picture. Mirroring the opposite profile is a modeling assumption; detail beyond these doorways and the auditorium interior is outside the surveyed model.')
destination.write_text(json.dumps(dct,ensure_ascii=False,indent=2)+'\n')
print('Clear door widths and rose overlap (m)',walk,top-ceiling)
