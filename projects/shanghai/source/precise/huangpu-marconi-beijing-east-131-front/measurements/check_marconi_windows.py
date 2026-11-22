"""Cast first-surface rays at the three photographed windows in a real glTF."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
from glb_triangles import SerialScene
from marconi_windows import MEASURED,openings,fixed_extent,leaf_frame,on_wall,TIMBER,FIXED,IRON,BEAD,GLASS,LIGHT,DARK
from marconi_photo_plane import pixel
def checks(low):
 fwd=np.array([0.,1.,0.]);up=np.array([0.,0.,1.])
 for witness,row in zip(MEASURED['openings'],openings()):
  key=row['key'];l,r,b,t=fixed_extent(witness);fy=row['frame_y']
  for f in (.22,.49,.81):
   yield key+' sill',np.array([row['left']+(row['right']-row['left'])*f,row['front_y']-.085,row['bottom']-.018]),fwd,LIGHT,.015
  for x in (l+.019,r-.019):
   for f in (.2,.45,.73):
    yield key+' fixed jamb',np.array([x,fy-.014,b+(t-b)*f]),fwd,FIXED,.008
  if key=='upper':
   width=(r-l-.10)/4
   for i in range(4):
    if i<2:hinge,d,n,_,_,_=leaf_frame(witness,i)
    else:hinge=np.array([l+.05+i*width,fy-.053,0.]);d=np.array([1.,0.,0.]);n=fwd
    def query(s,y,z,tag,mat):
     return f'upper sash {i+1} {tag}',hinge+d*s+n*y+up*z,n,mat,.006
    z0,z1=b+.028,t-.046;floor=z0+.04;top=z1-.046
    for s in (.016,width-.016):
     for f in (.22,.47,.77):yield query(s,-.018,z0+(z1-z0)*f,'stile',TIMBER)
    for f in (.21,.53,.76):
     yield query(f*width,-.018,z0+.02,'lower rail',TIMBER)
     yield query(f*width,-.018,z1-.023,'top rail',TIMBER)
     for tier in (1,2):yield query(f*width,-.012,floor+(top-floor)*tier/3,'horizontal glazing bar',TIMBER)
    for tier in range(3):
     fraction=.81 if (i==3 and tier==0) else .46
     z=floor+(top-floor)*(tier+fraction)/3
     glass_y=.017 if i==3 and tier in (0,2) else -.002
     for f in (.23,.49,.72):yield query(f*width,glass_y,z,'glass pane',GLASS)
     for x in (.036,width-.036):yield query(x,glass_y if low else -.007,z,'glazing bead or distant pane',GLASS if low else BEAD)
   for f in (.12,.24):
    for k in (.19,.34):
     yield 'upper open half, guard rail',np.array([l+(r-l)*k,fy+.084,b+(t-b)*f]),fwd,IRON,.25
   for k in (.18,.31):
    yield 'open half, clear sightline to recessed shade',np.array([l+(r-l)*k,fy+1.08,b+(t-b)*.53]),fwd,DARK,.97
  else:
   g=witness['grid_px'];xmin,xmax,head,foot=g['outer']
   xs=[on_wall(x,(head+foot)/2,fy)[0] for x in [xmin,*g['vertical'],xmax]]
   zs=[on_wall((xmin+xmax)/2,y,fy)[2] for y in [foot,g['horizontal'][1],g['horizontal'][0],head]]
   for x0,x1 in zip(xs,xs[1:]):
    for z0,z1 in zip(zs,zs[1:]):
     yield key+' glazing cell',np.array([(x0+x1)/2,fy-.005,(z0+z1)/2]),fwd,GLASS,.008
     yield key+' putty bead or distant pane',np.array([(x0+x1)/2,fy-.005 if low else fy-.010,z0+.008]),fwd,GLASS if low else BEAD,.007
   for x in xs:
    for z0,z1 in zip(zs,zs[1:]):yield key+' vertical strip',np.array([x,fy-.021,(z0+z1)/2]),fwd,IRON,.012
   for z in zs:
    for x0,x1 in zip(xs,xs[1:]):yield key+' horizontal strip',np.array([(x0+x1)/2,fy-.021,z]),fwd,IRON,.012
def inspect(mesh,low):
 scene=SerialScene(mesh);rows=[]
 for name,p,d,mat,gap in checks(low):
  hit=scene.ray(p-d*gap,d,gap+.004)
  actual=hit['material'] if hit else None
  diff=None if hit is None else float(np.linalg.norm(np.array(hit['point_enu_m'])-p))
  rows.append(dict(feature=name,expected_material=mat,material=actual,xyz_m=np.round(p,5).tolist(),source_pixel_2017=np.round(pixel(p),1).tolist(),distance_error_m=diff,passed=actual==mat and diff is not None and diff<.0017))
 return dict(**scene.asset,level='lod' if low else 'full',triangles=len(scene.tri),rays=len(rows),passed=all(v['passed'] for v in rows),checks=rows)
if __name__=='__main__':
 cmd=argparse.ArgumentParser()
 cmd.add_argument('mesh',type=Path);cmd.add_argument('level',choices=['full','lod']);cmd.add_argument('output',type=Path)
 a=cmd.parse_args();r=inspect(a.mesh,a.level=='lod');a.output.write_text(json.dumps(r,ensure_ascii=False,indent=1)+'\n')
 print(sum(v['passed']for v in r['checks']),r['rays'],r['triangles'])
 raise SystemExit(int(not r['passed']))
